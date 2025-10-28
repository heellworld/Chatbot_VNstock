import os
import pandas as pd

def process_definition_data(data):

    # Kiểm tra dữ liệu đầu vào
    if not isinstance(data, pd.DataFrame) or data.empty:
        print("Dữ liệu đầu vào không hợp lệ hoặc rỗng.")
        return pd.DataFrame()
    
    # Danh sách các tên chỉ số tài chính cần lọc
    filter_names = [
        'Nợ/VCSH', 'TSCĐ / Vốn CSH', 'Vốn CSH/Vốn điều lệ',
        'Biên lợi nhuận ròng (%)', 'ROE (%)', 'ROIC (%)', 'ROA (%)', 'Tỷ suất cổ tức (%)',
        'Đòn bẩy tài chính', 'Vốn hóa (Tỷ đồng)', 'Số CP lưu hành (Triệu CP)',
        'P/E', 'P/B', 'P/S', 'P/Cash Flow', 'EPS (VND)', 'BVPS (VND)',
        '(Vay NH+DH)/VCSH', 'Vòng quay tài sản', 'Vòng quay TSCĐ',
        'Số ngày thu tiền bình quân', 'Số ngày tồn kho bình quân',
        'Số ngày thanh toán bình quân', 'Chu kỳ tiền', 'Vòng quay hàng tồn kho',
        'Biên EBIT (%)', 'Biên lợi nhuận gộp (%)', 'EBITDA (Tỷ đồng)', 'EBIT (Tỷ đồng)',
        'Chỉ số thanh toán hiện thời', 'Chỉ số thanh toán tiền mặt',
        'Chỉ số thanh toán nhanh', 'Khả năng chi trả lãi vay', 'EV/EBITDA'
    ]
    
    # Bước 1: Lọc các hàng có giá trị cột 'name' nằm trong filter_names
    filtered_df = data[data['name'].isin(filter_names)].copy()
    
    # Kiểm tra dữ liệu sau khi lọc
    if filtered_df.empty:
        print("Không có chỉ số tài chính nào trong danh sách filter_names.")
        return pd.DataFrame()
    
    # Bước 2: Loại bỏ các cột 'order' và 'com_type_code'
    filtered_df = filtered_df.drop(columns=['order', 'com_type_code'], errors='ignore')
    
    # Bước 3: Xử lý trùng lặp trong cột 'name', giữ lại hàng đầu tiên
    filtered_df = filtered_df.drop_duplicates(subset=['name'], keep='first')
    
    return filtered_df