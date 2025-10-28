import os
import pandas as pd


def process_ratio_data(dataframe):
    desired_columns = [
        'CP', 'Năm', 'Kỳ', 'Nợ/VCSH', 'TSCĐ / Vốn CSH', 'Vốn CSH/Vốn điều lệ',
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

    merged_dfs = []
    for df in dataframe:
        # Kiểm tra cấu trúc cột
        print("Các cột trong DataFrame gốc:", df.columns.tolist())
        
        # Chọn các cột mà cấp 2 (level 1) nằm trong desired_columns
        selected_columns = [col for col in df.columns if col[1] in desired_columns]
        print("Các cột được chọn:", selected_columns)
        
        # Tạo DataFrame mới với các cột được chọn
        df_processed = df[selected_columns].copy()
        
        # Đổi tên cột thành cấp 2 (level 1)
        df_processed.columns = [col[1] for col in selected_columns]
        print("Các cột sau khi đổi tên:", df_processed.columns.tolist())
        
        # Thêm các cột còn thiếu trong desired_columns với giá trị NaN
        for col in desired_columns:
            if col not in df_processed.columns:
                df_processed[col] = pd.NA
        
        # Sắp xếp lại cột theo thứ tự trong desired_columns
        df_processed = df_processed[desired_columns]
        
        # Reset index
        df_processed = df_processed.reset_index(drop=True)
        
        # Kiểm tra dữ liệu sau khi xử lý
        print("Dữ liệu đầu tiên sau khi xử lý:\n", df_processed.head())
        
        merged_dfs.append(df_processed)
    
    if merged_dfs:
        summary_df = pd.concat(merged_dfs, ignore_index=True)
    else:
        print("Không có dữ liệu để hợp nhất.")
        return pd.DataFrame(columns=desired_columns)
    
    return summary_df