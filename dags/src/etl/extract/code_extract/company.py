import pandas as pd
from vnstock import Vnstock
import os
import time
import re

def collect_company_data():
    # Khởi tạo đối tượng Vnstock
    stock = Vnstock().stock(symbol='VCI', source='VCI')
    
    # Danh sách các phương thức cần gọi và tên file tương ứng
    methods = [
        ('overview', 'overview'),
        ('profile', 'profile')
    ]
    
    # Lấy danh sách mã chứng khoán VN30
    vn30_symbols = stock.listing.symbols_by_group('VN30')
    print("Danh sách mã chứng khoán VN30:", vn30_symbols)
    
    # Đường dẫn thư mục lưu trữ
    output_dir = r"D:\project_persional\chabot_stock\data\raw\company"
    
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lặp qua từng mã chứng khoán
    for symbol in vn30_symbols:
        try:
            # Khởi tạo đối tượng company cho mã chứng khoán
            company = Vnstock().stock(symbol=symbol, source='TCBS').company
            
            # Lặp qua từng phương thức
            for method_name, file_prefix in methods:
                try:
                    # Gọi phương thức tương ứng
                    data = getattr(company, method_name)()
                    
                    # Nếu dữ liệu là DataFrame, lưu vào file
                    if isinstance(data, pd.DataFrame):
                        data['MaCK'] = symbol
                        file_name = f"{file_prefix}_{symbol}.csv"
                        file_path = os.path.join(output_dir, file_name)
                        data.to_csv(file_path, index=False, encoding='utf-8-sig')
                        print(f"Đã lưu {method_name} cho {symbol} vào {file_path}")
                    else:
                        print(f"Dữ liệu từ {method_name} cho {symbol} không phải là DataFrame.")
                except Exception as e:
                    print(f"Lỗi khi xử lý {method_name} cho {symbol}: {e}")
            # Sau khi hoàn tất các phương thức cho symbol, chờ 10 giây
            print(f"Hoàn tất xử lý cho {symbol}. Chờ 40 giây trước khi chuyển sang symbol tiếp theo...")
            time.sleep(40)  # Thêm khoảng chờ 10 giây
        
        except Exception as e:
            print(f"Lỗi khi xử lý mã chứng khoán {symbol}: {e}")

# Chạy chương trình
print(collect_company_data())