import pandas as pd
from vnstock import Vnstock
from vnstock.explorer.vci import Finance
from datetime import datetime
from sqlalchemy import func

from config.database import SessionLocal
from src.etl.transform.process_data import (process_definition_data, 
                          process_ratio_data, process_company_data)
from src.models import DimTime
import time
from datetime import timedelta

# Hàm lấy ngày cuối cùng từ data warehouse
def get_last_date():
    """
    Lấy ngày cuối cùng từ bảng Dim_Time trong data warehouse
    """
    with SessionLocal() as session:  # Sử dụng session thay vì engine.connect()
        last_date = session.query(func.max(DimTime.Date)).scalar()  # Dùng ORM và hàm aggregate
        return last_date + timedelta(days=1)

# Hàm thu thập dữ liệu quote
def collect_quote_data(last_date):
    print(f"Ngày bắt đầu: {last_date}")
    print("Đang trích xuất lịch sử giá")
    time_current = datetime.now().strftime('%Y-%m-%d')
    print(f"Ngày hiện tại: {time_current}")
    stock = Vnstock().stock(symbol='VCI', source='VCI')
    vn30_symbols = stock.listing.symbols_by_group('VN30')
    quote_data_list = []
    
    for symbol in vn30_symbols:
        try:
            # Thu thập dữ liệu từ API
            quote_data = stock.quote.history(
                symbol=symbol,
                start=f'{last_date}',
                end=f'{time_current}',
                interval='1D'
            )
            
            # Xử lý cột và định dạng dữ liệu
            processed_data = (
                quote_data
                .assign(MaCK=symbol)
                .rename(columns={
                    'date': 'time',
                    'openPrice': 'open',
                    'highPrice': 'high',
                    'lowPrice': 'low',
                    'closePrice': 'close',
                    'volume': 'volume'
                })
                [['time', 'MaCK', 'open', 'high', 'low', 'close', 'volume']]
            )
            
            # Chuyển đổi cột 'time' thành chuỗi để serialize
            processed_data['time'] = processed_data['time'].astype(str)
            processed_data['volume'] = processed_data['volume'].astype('float64')
            
            quote_data_list.append(processed_data)
            print(f"✅ Xử lý thành công: {symbol}")

        except Exception as e:
            print(f"❌ Lỗi xử lý {symbol}: {str(e)}")
            continue  # Bỏ qua mã lỗi và tiếp tục
    
    # Tổng hợp dữ liệu sau khi xử lý tất cả mã
    if not quote_data_list:
        print("⚠️ Không có dữ liệu nào được thu thập")
        return pd.DataFrame()
    
    quote_summary = pd.concat(quote_data_list, ignore_index=True)
    print(quote_summary)
    return quote_summary

# Hàm thu thập dữ liệu finance
def collect_finance_data():
    print("Đang trích xuất chỉ số tài chính")
    stock = Vnstock().stock(symbol='VCI', source='VCI')
    vn30_symbols = stock.listing.symbols_by_group('VN30')
    finance_data_list = []
    for symbol in vn30_symbols:

        try:
            finance = Vnstock().stock(symbol=symbol, source='VCI').finance
            data = finance.ratio(period='quarter', lang='vi')

            # Thêm cột mã chứng khoán trước khi xử lý
            if isinstance(data, pd.DataFrame):
                finance_data_list.append(data)
                
        except Exception as e:
            print(f"Lỗi khi xử lý finance cho {symbol}: {e}")
        time.sleep(40)  # Dùng sleep thay vì time.sleep
    # Truyền dữ liệu đã thu thập vào hàm xử lý
    final_ratio_dfs = process_ratio_data(finance_data_list)
    print(final_ratio_dfs.head())

    return final_ratio_dfs

# Hàm thu thập dữ liệu company
def collect_company_data():
    stock = Vnstock().stock(symbol='VCI', source='VCI')
    vn30_symbols = stock.listing.symbols_by_group('VN30')
    company_data_list = []
    
    for symbol in vn30_symbols:
        try:
            company = Vnstock().stock(symbol=symbol, source='TCBS').company
            overview = company.overview()
            profile = company.profile()
            if isinstance(overview, pd.DataFrame) and isinstance(profile, pd.DataFrame):
                # Xử lý dữ liệu ngay lập tức bằng process_company_data
                processed_data = process_company_data(overview, profile)
                company_data_list.append(processed_data)
        except Exception as e:
            print(f"Lỗi khi xử lý company cho {symbol}: {e}")
        time.sleep(40)  # Giữ thời gian chờ 40 giây
    
    # Hợp nhất tất cả các DataFrame đã xử lý
    if company_data_list:
        final_df = pd.concat(company_data_list, ignore_index=True)
    else:
        final_df = pd.DataFrame()
    
    return final_df

# Hàm thu thập dữ liệu definition
def collect_definition_data(symbol='PLX', period='quarter'):
    try:
        finance = Finance(symbol=symbol, period=period)
        data = finance._get_ratio_dict()

        if not isinstance(data, pd.DataFrame) or data.empty:
                    print(f"Không có dữ liệu cho {symbol}")
                    return pd.DataFrame()
        filtered_df = process_definition_data(data)

        return filtered_df
    except Exception as e:
        print(f"Lỗi khi thu thập dữ liệu cho {symbol}: {e}")
        return pd.DataFrame()