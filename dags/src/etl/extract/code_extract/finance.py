import pandas as pd
from vnstock import Vnstock
import os
import time

def collect_finance_data():
    # Khởi tạo đối tượng Vnstock
    stock = Vnstock().stock(symbol='VCI', source='VCI')
    
    # Danh sách các phương thức cần gọi và tên file tương ứng
    methods = [
        ('ratio', 'ratio_quarter')
    ]
    
    # Lấy danh sách mã chứng khoán VN30
    vn30_symbols = stock.listing.symbols_by_group('VN30')
    print("Danh sách mã chứng khoán VN30:", vn30_symbols)
    
    # Đường dẫn thư mục lưu trữ
    output_dir = r"D:\project_persional\chabot_stock\data\raw\finance"
    
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lặp qua từng mã chứng khoán
    for symbol in vn30_symbols:
        try:
            # Khởi tạo đối tượng finance cho mã chứng khoán
            finance = Vnstock().stock(symbol=symbol, source='VCI').finance
            
            # Lặp qua từng phương thức
            for method_name, file_prefix in methods:
                try:
                    # Gọi phương thức với period='quarter' và lang='vi'
                    data = getattr(finance, method_name)(period='quarter', lang='vi')
                    
                    # Kiểm tra và lưu dữ liệu nếu là DataFrame
                    if isinstance(data, pd.DataFrame):
                        data['MaCK'] = symbol  # Thêm cột mã chứng khoán
                        file_name = f"finance_{file_prefix}_{symbol}.csv"
                        file_path = os.path.join(output_dir, file_name)
                        data.to_csv(file_path, index=False, encoding='utf-8-sig')
                        print(f"Đã lưu {method_name} cho {symbol} vào {file_path}")
                    else:
                        print(f"Dữ liệu từ {method_name} cho {symbol} không phải là DataFrame.")
                
                except Exception as e:
                    print(f"Lỗi khi xử lý {method_name} cho {symbol}: {e}")
            
            # Chờ 40 giây trước khi chuyển sang mã tiếp theo
            print(f"Hoàn tất xử lý cho {symbol}. Chờ 40 giây...")
            time.sleep(40)
        
        except Exception as e:
            print(f"Lỗi khi xử lý mã chứng khoán {symbol}: {e}")

# Chạy chương trình
print(collect_finance_data())