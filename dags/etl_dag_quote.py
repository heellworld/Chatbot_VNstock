from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import pandas as pd
from src.etl.extract import collect_quote_data
from src.etl.transform import processing_dimtime, prepare_fact_stock_price
from src.etl.load import load_dim_time, load_fact_stock_price, get_stock_key_map
from src.etl.extract.extract import get_last_date
from airflow.exceptions import AirflowException, AirflowSkipException
from config.database import SessionLocal
from src.models import DimTime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 8),
    'retries': 2,
    'retry_delay': timedelta(minutes=10),  # Thử lại sau 30 phút
    'email_on_failure': True,
}

with DAG('etl_quote_daily', 
         default_args=default_args, 
         schedule_interval='0 18 * * 1-5',  # Chạy lúc 18:00 các ngày trong tuần (thị trường đóng cửa)
         catchup=False) as dag:
    
    start = DummyOperator(task_id='start')
    
    def extract_quote_task():
        """Trích xuất dữ liệu quote từ API"""
        try:
            last_date = get_last_date()
            print(f"Lấy dữ liệu cho ngày: {last_date}")
            
            quote_data = collect_quote_data(last_date)
            if quote_data is None or quote_data.empty:
                print(f"Không có dữ liệu quote cho ngày {last_date}, bỏ qua quy trình")
                raise AirflowSkipException(f"Không có dữ liệu cho ngày {last_date}")
            
            print(f"Đã lấy được {len(quote_data)} bản ghi dữ liệu giá")
            return quote_data.to_dict()
        except AirflowSkipException:
            raise  # Ném lại ngoại lệ này để Airflow bỏ qua task
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu quote: {str(e)}")
            raise AirflowException(f"Extract thất bại: {str(e)}")

    def transform_quote_task(**context):
        """Biến đổi dữ liệu quote thành dim_time và fact_stock_price"""
        try:
            quote_data_dict = context['ti'].xcom_pull(task_ids='extract_quote')
            if not quote_data_dict:
                raise ValueError("Không có dữ liệu từ bước extract")
                
            df_quote = pd.DataFrame(quote_data_dict)
            
            # Xử lý dim_time
            dim_time_df = processing_dimtime(df_quote)
            if dim_time_df.empty:
                raise AirflowException("dim_time_df không có dữ liệu. Dừng quy trình.")
            
            # Kiểm tra xem TimeKey đã tồn tại trong database chưa
            existing_time_keys = get_existing_time_keys()
            new_time_keys = dim_time_df[~dim_time_df['TimeKey'].isin(existing_time_keys)]
            if not new_time_keys.empty:
                print(f"Phát hiện {len(new_time_keys)} TimeKey mới cần được thêm vào DimTime")
            
            # Xử lý fact_stock_price
            fact_stock_price_df = prepare_fact_stock_price(df_quote, dim_time_df)
            if fact_stock_price_df.empty:
                raise AirflowException("fact_stock_price_df không có dữ liệu. Dừng quy trình.")
            
            # Kiểm tra dữ liệu fact_stock_price
            print(f"Dữ liệu fact_stock_price: {len(fact_stock_price_df)} bản ghi")
            print(f"Số lượng mã chứng khoán: {fact_stock_price_df['StockSymbol'].nunique()}")
            print(f"Số lượng ngày: {fact_stock_price_df['TimeKey'].nunique()}")
            
            # Nếu cả hai DataFrame đều có dữ liệu
            transformed_data = {
                'dim_time': dim_time_df.to_dict(),
                'fact_stock_price': fact_stock_price_df.to_dict()
            }
            
            context['ti'].xcom_push(key='transformed_quote_data', value=transformed_data)
            return transformed_data
        except Exception as e:
            print(f"Lỗi trong quá trình biến đổi dữ liệu: {str(e)}")
            raise AirflowException(f"Transform thất bại: {str(e)}")

    def load_quote_task(**context):
        """Nạp dữ liệu quote đã biến đổi vào data warehouse"""
        try:
            transformed_data = context['ti'].xcom_pull(key='transformed_quote_data')
            if not transformed_data:
                raise ValueError("Không có dữ liệu từ bước transform")
                
            dim_time_df = pd.DataFrame(transformed_data['dim_time'])
            fact_stock_price_df = pd.DataFrame(transformed_data['fact_stock_price'])
            
            # Load dim_time (chỉ load các bản ghi mới)
            time_rows = load_dim_time(dim_time_df)
            print(f"Đã thêm {time_rows} bản ghi vào DimTime")
            
            # Lấy stock_key_map từ DimCompany
            stock_key_map = get_stock_key_map()
            if not stock_key_map:
                raise ValueError("Không thể lấy mapping StockSymbol -> StockKey")
                
            print(f"Đã lấy mapping cho {len(stock_key_map)} mã chứng khoán")
            
            # Load fact_stock_price
            price_rows = load_fact_stock_price(fact_stock_price_df, stock_key_map)
            print(f"Đã thêm {price_rows} bản ghi vào FactStockPrice")
            
            return f"Hoàn thành: {time_rows} bản ghi thời gian, {price_rows} bản ghi giá"
        except Exception as e:
            print(f"Lỗi trong quá trình nạp dữ liệu: {str(e)}")
            raise AirflowException(f"Load thất bại: {str(e)}")

    # Định nghĩa các task
    extract_quote = PythonOperator(
        task_id='extract_quote', 
        python_callable=extract_quote_task
    )
    
    transform_quote = PythonOperator(
        task_id='transform_quote', 
        python_callable=transform_quote_task, 
        provide_context=True
    )
    
    load_quote = PythonOperator(
        task_id='load_quote', 
        python_callable=load_quote_task, 
        provide_context=True
    )
    
    end = DummyOperator(task_id='end')

    # Thiết lập thứ tự thực thi
    start >> extract_quote >> transform_quote >> load_quote >> end

# Hàm hỗ trợ để lấy các TimeKey hiện có trong DB
def get_existing_time_keys():
    with SessionLocal() as session:
        time_keys = session.query(DimTime.TimeKey).all()
        return [tk[0] for tk in time_keys]