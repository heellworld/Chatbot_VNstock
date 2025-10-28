from vnstock import Vnstock
import os

def collect_quote_data():
    # Khởi tạo đối tượng Vnstock
    stock = Vnstock().stock(symbol='VCI', source='VCI')
    
    # Lấy danh sách mã chứng khoán của VN30
    vn30_symbols = stock.listing.symbols_by_group('VN30')
    print(vn30_symbols)
    # Đường dẫn thư mục lưu trữ
    output_dir = r"D:\project_persional\chabot_stock\data\raw\quote"
    
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lặp qua từng mã chứng khoán trong VN30
    for symbol in vn30_symbols:
        try:
            # Lấy dữ liệu lịch sử giao dịch
            quote_data = stock.quote.history(symbol=symbol, start='2020-01-01', end='2024-12-31', interval='1D')
            
            # Thêm cột MaCK (mã chứng khoán) vào dữ liệu
            quote_data['MaCK'] = symbol
            
            # Đổi tên cột để phù hợp với yêu cầu
            quote_data.rename(columns={
                'date': 'time',
                'openPrice': 'open',
                'highPrice': 'high',
                'lowPrice': 'low',
                'closePrice': 'close',
                'volume': 'volume'
            }, inplace=True)
            
            # Chọn các cột cần thiết theo thứ tự
            quote_data = quote_data[['time', 'MaCK', 'open', 'high', 'low', 'close', 'volume']]
            
            # Định dạng tên file
            file_name = f"quote_{symbol}.csv"
            file_path = os.path.join(output_dir, file_name)
            
            # Lưu dữ liệu vào file CSV với encoding UTF-8-SIG
            quote_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            print(f"Đã lưu dữ liệu cho {symbol} vào {file_path}")
        except Exception as e:
            print(f"Lỗi khi xử lý {symbol}: {e}")

print(collect_quote_data())