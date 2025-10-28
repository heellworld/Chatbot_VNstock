from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from config.database import SessionLocal
from src.etl.extract.extract import collect_finance_data, collect_company_data, collect_definition_data
from src.etl.transform.transform import processing_dimcompany, processing_dimratio, processing_ratio, prepare_fact_ratios
from src.etl.load.load_dw import load_dim_company, load_dim_ratio, load_fact_financial_ratios
from src.models import DimTime, DimCompany, DimRatio
from airflow.exceptions import AirflowException, AirflowSkipException

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 6),
    'retries': 3,  # Tăng số lần retry để xử lý trường hợp dữ liệu chưa có
    'retry_delay': timedelta(days=1),  # Thử lại sau 1 ngày
    'email_on_failure': True,  # Gửi email khi task thất bại
}

with DAG(
    'etl_quarterly',
    default_args=default_args,
    schedule_interval='0 0 2-5 1,4,7,10 *',  # Chạy vào ngày 2-5 của tháng đầu quý (1,4,7,10)
    catchup=False  # Không catch up các task đã bỏ lỡ
) as dag:
    
    def check_quarter_data_available():
        """Kiểm tra xem dữ liệu cho quý hiện tại đã có sẵn chưa"""
        try:
            # Thử lấy mẫu dữ liệu
            sample_data = collect_finance_data(sample=True)
            if sample_data is None or sample_data.empty:
                print("Dữ liệu quý chưa sẵn sàng, sẽ thử lại sau")
                raise AirflowSkipException("Dữ liệu quý chưa có. Task sẽ được thử lại sau.")
            return True
        except Exception as e:
            print(f"Lỗi khi kiểm tra dữ liệu quý: {str(e)}")
            raise AirflowSkipException(f"Lỗi khi kiểm tra dữ liệu: {str(e)}")
    
    def extract_quarterly_task():
        """Trích xuất dữ liệu finance, company, và definition từ API"""
        try:
            finance_data = collect_finance_data()
            company_data = collect_company_data()
            definition_data = collect_definition_data()
            
            # Kiểm tra dữ liệu đầu vào
            if finance_data.empty:
                raise ValueError("Không có dữ liệu tài chính")
            if company_data.empty:
                raise ValueError("Không có dữ liệu công ty")
            if definition_data.empty:
                raise ValueError("Không có dữ liệu định nghĩa")
                
            # Log thông tin về dữ liệu đã thu thập
            print(f"Đã thu thập: {len(finance_data)} bản ghi tài chính, {len(company_data)} công ty, {len(definition_data)} chỉ số")
            
            return {
                'finance': finance_data.to_dict(),
                'company': company_data.to_dict(),
                'definition': definition_data.to_dict()
            }
        except Exception as e:
            print(f"Lỗi trong quá trình thu thập dữ liệu: {str(e)}")
            raise AirflowException(f"Extract thất bại: {str(e)}")

    def transform_quarterly_task(**context):
        """Biến đổi dữ liệu quarterly thành dim_company, dim_ratio, và fact_ratios"""
        try:
            extracted_data = context['ti'].xcom_pull(task_ids='extract_quarterly')
            if not extracted_data:
                raise ValueError("Không có dữ liệu từ bước extract")
                
            df_finance = pd.DataFrame(extracted_data['finance'])
            df_company = pd.DataFrame(extracted_data['company'])
            df_definition = pd.DataFrame(extracted_data['definition'])
            
            # Xử lý dữ liệu
            dim_company_df = processing_dimcompany(df_company)
            dim_ratio_df = processing_dimratio(df_definition)
            df_ratio_processed = processing_ratio(df_finance)
            
            # Lấy dim_time từ database
            dim_time_df = get_dim_time_from_db()
            if dim_time_df.empty:
                raise ValueError("Bảng DimTime không có dữ liệu")
                
            fact_ratios_df = prepare_fact_ratios(df_ratio_processed, dim_time_df)
            if fact_ratios_df.empty:
                raise ValueError("Không thể tạo bảng fact_ratios")
            
            # Lưu kết quả biến đổi
            transformed_data = {
                'dim_company': dim_company_df.to_dict(),
                'dim_ratio': dim_ratio_df.to_dict(),
                'fact_ratios': fact_ratios_df.to_dict()
            }
            
            print(f"Đã biến đổi: {len(dim_company_df)} công ty, {len(dim_ratio_df)} chỉ số, {len(fact_ratios_df)} bản ghi tỉ lệ tài chính")
            context['ti'].xcom_push(key='transformed_quarterly_data', value=transformed_data)
        except Exception as e:
            print(f"Lỗi trong quá trình biến đổi dữ liệu: {str(e)}")
            raise AirflowException(f"Transform thất bại: {str(e)}")

    def load_quarterly_task(**context):
        """Nạp dữ liệu quarterly đã biến đổi vào data warehouse"""
        try:
            transformed_data = context['ti'].xcom_pull(key='transformed_quarterly_data')
            if not transformed_data:
                raise ValueError("Không có dữ liệu từ bước transform")
                
            dim_company_df = pd.DataFrame(transformed_data['dim_company'])
            dim_ratio_df = pd.DataFrame(transformed_data['dim_ratio'])
            fact_ratios_df = pd.DataFrame(transformed_data['fact_ratios'])
            
            # Load dim_company và dim_ratio trước để có stock_key_map và ratio_key_map
            load_dim_company(dim_company_df)
            load_dim_ratio(dim_ratio_df)
            
            # Lấy mapping từ database sau khi đã load dim_company và dim_ratio
            with SessionLocal() as session:
                stock_key_map = get_stock_key_map(session)
                ratio_key_map = get_ratio_key_map(session)
            
            # Load fact_financial_ratios
            rows_loaded = load_fact_financial_ratios(fact_ratios_df, stock_key_map, ratio_key_map)
            print(f"Đã nạp {rows_loaded} bản ghi vào fact_financial_ratios")
        except Exception as e:
            print(f"Lỗi trong quá trình nạp dữ liệu: {str(e)}")
            raise AirflowException(f"Load thất bại: {str(e)}")

    # Định nghĩa các task
    check_data_available = PythonOperator(
        task_id='check_quarter_data',
        python_callable=check_quarter_data_available
    )
    
    extract_quarterly = PythonOperator(
        task_id='extract_quarterly', 
        python_callable=extract_quarterly_task
    )
    
    transform_quarterly = PythonOperator(
        task_id='transform_quarterly', 
        python_callable=transform_quarterly_task, 
        provide_context=True
    )
    
    load_quarterly = PythonOperator(
        task_id='load_quarterly', 
        python_callable=load_quarterly_task, 
        provide_context=True
    )

    # Thiết lập thứ tự thực thi
    check_data_available >> extract_quarterly >> transform_quarterly >> load_quarterly

# Hàm hỗ trợ lấy dim_time từ database
def get_dim_time_from_db():
    with SessionLocal() as session:
        dim_time_data = session.query(DimTime).all()
        if not dim_time_data:
            print("Cảnh báo: Bảng DimTime không có dữ liệu!")
            return pd.DataFrame()
            
        return pd.DataFrame([{
            'TimeKey': row.TimeKey,
            'Date': row.Date,
            'Year': row.Year,
            'Quarter': row.Quarter,
            'Month': row.Month,
            'Week': row.Week,
            'Day': row.Day
        } for row in dim_time_data])

# Hàm lấy stock_key_map từ DimCompany
def get_stock_key_map(session):
    companies = session.query(DimCompany).all()
    if not companies:
        raise ValueError("Không có dữ liệu trong bảng DimCompany")
    return {company.StockSymbol: company.StockKey for company in companies}

# Hàm lấy ratio_key_map từ DimRatio
def get_ratio_key_map(session):
    ratios = session.query(DimRatio).all()
    if not ratios:
        raise ValueError("Không có dữ liệu trong bảng DimRatio")
    return {ratio.RatioName: ratio.RatioKey for ratio in ratios}