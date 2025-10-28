import pandas as pd

def processing_dimtime(df_quote):
    # Chuyển đổi cột time thành định dạng datetime
    df_quote['time'] = pd.to_datetime(df_quote['time'], format='%Y-%m-%d')
    # Trích xuất các thuộc tính thời gian
    df_quote['Date'] = df_quote['time'].dt.date
    df_quote['Year'] = df_quote['time'].dt.year
    df_quote['Quarter'] = df_quote['time'].dt.quarter
    df_quote['Month'] = df_quote['time'].dt.month
    df_quote['Week'] = df_quote['time'].dt.isocalendar().week
    df_quote['Day'] = df_quote['time'].dt.day
    # Tạo khóa thời gian theo định dạng YYYYMMDD
    df_quote['TimeKey'] = df_quote['time'].dt.strftime('%Y%m%d').astype(int)
    # Loại bỏ các bản ghi trùng lặp
    dim_time_df = df_quote[['TimeKey', 'Date', 'Year', 'Quarter', 'Month', 'Week', 'Day']].drop_duplicates()
    return dim_time_df

def processing_dimcompany(df_company):
    # Đổi tên các cột theo chuẩn
    dim_company = df_company.rename(columns={
        'symbol': 'StockSymbol', 'company_name': 'CompanyName', 'industry': 'Industry',
        'company_type': 'CompanyType', 'stock_rating': 'StockRating', 'short_name': 'ShortName'
    })
    # Tạo khóa cho bảng company
    dim_company['StockKey'] = dim_company.index + 1
    # Làm tròn và chuyển đổi kiểu dữ liệu cho cột StockRating
    dim_company['StockRating'] = dim_company['StockRating'].round(2).astype('float64')
    return dim_company[['StockKey', 'StockSymbol', 'CompanyName', 'ShortName', 'Industry', 'CompanyType', 'StockRating']]

def processing_dimratio(df_definition):
    # Xóa các chuỗi trong ngoặc đơn và khoảng trắng thừa
    df_definition['name'] = df_definition['name'].str.replace(r'\s*\([^)]*\)\s*$', '', regex=True).str.strip()
    # Đổi tên các cột
    df_definition = df_definition.rename(columns={'name': 'RatioName', 'type': 'RatioType', 'unit': 'Unit'})
    # Tạo khóa cho bảng ratio
    df_definition['RatioKey'] = df_definition.index + 1
    return df_definition[['RatioKey', 'RatioName', 'Unit', 'RatioType']]

def processing_ratio(df_ratio):
    # Tạo dictionary ánh xạ từ tên cột cũ sang RatioName
    column_mapping = {
        'CP': 'StockSymbol',
        'Nợ/VCSH': 'Nợ/VCSH',
        'TSCĐ / Vốn CSH': 'TSCĐ/Vốn CSH',
        'Vốn CSH/Vốn điều lệ': 'Vốn CSH/Vốn điều lệ',
        'Biên lợi nhuận ròng (%)': 'Biên lợi nhuận ròng',
        'ROE (%)': 'ROE',
        'ROIC (%)': 'ROIC',
        'ROA (%)': 'ROA',
        'Tỷ suất cổ tức (%)': 'Tỷ suất cổ tức',
        'Đòn bẩy tài chính': 'Đòn bẩy tài chính',
        'Vốn hóa (Tỷ đồng)': 'Vốn hóa',
        'Số CP lưu hành (Triệu CP)': 'Số CP lưu hành',
        'P/E': 'P/E',
        'P/B': 'P/B',
        'P/S': 'P/S',
        'P/Cash Flow': 'P/Cash Flow',
        'EPS (VND)': 'EPS',
        'BVPS (VND)': 'BVPS',
        '(Vay NH+DH)/VCSH': '(Vay NH+DH)/VCSH',
        'Vòng quay tài sản': 'Vòng quay tài sản',
        'Vòng quay TSCĐ': 'Vòng quay TSCĐ',
        'Số ngày thu tiền bình quân': 'Số ngày thu tiền bình quân',
        'Số ngày tồn kho bình quân': 'Số ngày tồn kho bình quân',
        'Số ngày thanh toán bình quân': 'Số ngày thanh toán bình quân',
        'Chu kỳ tiền': 'Chu kỳ tiền',
        'Vòng quay hàng tồn kho': 'Vòng quay hàng tồn kho',
        'Biên EBIT (%)': 'Biên EBIT',
        'Biên lợi nhuận gộp (%)': 'Biên lợi nhuận gộp',
        'EBITDA (Tỷ đồng)': 'EBITDA',
        'EBIT (Tỷ đồng)': 'EBIT',
        'Chỉ số thanh toán hiện thời': 'Chỉ số thanh toán hiện thời',
        'Chỉ số thanh toán tiền mặt': 'Chỉ số thanh toán tiền mặt',
        'Chỉ số thanh toán nhanh': 'Chỉ số thanh toán nhanh',
        'Khả năng chi trả lãi vay': 'Khả năng chi trả lãi vay',
        'EV/EBITDA': 'EV/EBITDA'
    }
    # Đổi tên cột
    df_ratio = df_ratio.rename(columns=column_mapping)
    # Xác định các cột số và điền giá trị thiếu
    numeric_cols = df_ratio.select_dtypes(include=['float64']).columns
    # Điền các giá trị thiếu với giá trị -99999999
    df_ratio[numeric_cols] = df_ratio[numeric_cols].fillna(-99999999)
    return df_ratio

def prepare_fact_ratios(df_ratio, dim_time_df):
    # Định nghĩa các cột nhận diện và cột giá trị
    id_vars = ['StockSymbol', 'Năm', 'Kỳ']
    value_vars = [col for col in df_ratio.columns if col not in id_vars]
    
    # Chuyển đổi DataFrame từ dạng rộng sang dài
    melted_df = pd.melt(
        df_ratio,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='RatioName',
        value_name='Value'
    )
    
    # Ánh xạ TimeKey từ bảng thời gian
    melted_df['TimeKey'] = melted_df.apply(
        lambda row: get_time_key(
            dim_time_df,
            year=row['Năm'],
            quarter=row['Kỳ']
        ),
        axis=1
    )
    
    # Lọc các bản ghi hợp lệ và chọn cột cần thiết
    return melted_df[
        ['TimeKey', 'StockSymbol', 'RatioName', 'Value']
    ].dropna(subset=['TimeKey'])


def prepare_fact_stock_price(df_quote, dim_time_df):
    # Đảm bảo cột time là kiểu datetime
    if not pd.api.types.is_datetime64_any_dtype(df_quote['time']):
        df_quote['time'] = pd.to_datetime(df_quote['time'])
    
    # Trích xuất phần date để so sánh chính xác
    df_quote['date_only'] = df_quote['time'].dt.date
    
    # Tạo dictionary ánh xạ để tìm kiếm nhanh
    time_key_mapping = dict(zip(dim_time_df['Date'], dim_time_df['TimeKey']))
    
    # Ánh xạ TimeKey sử dụng dictionary (hiệu quả hơn)
    df_quote['TimeKey'] = df_quote['date_only'].map(time_key_mapping)
    
    # In ra giá trị TimeKey để kiểm tra
    print("TimeKey", df_quote['TimeKey'])
    
    # Chuẩn hóa tên cột và lọc dữ liệu hợp lệ
    df_quote = (
        df_quote
        .rename(columns={'MaCK': 'StockSymbol'})
        .dropna(subset=['TimeKey'])
    )
    
    # Chọn các cột cần thiết cho bảng fact
    return df_quote[[
        'TimeKey',
        'StockSymbol',
        'open',
        'high',
        'low',
        'close',
        'volume'
    ]]


def get_time_key(dim_time_df, year, quarter):
    # Tìm bản ghi phù hợp theo năm và quý
    match = dim_time_df[
        (dim_time_df['Year'] == year) & 
        (dim_time_df['Quarter'] == quarter)
    ]
    # Trả về TimeKey nếu tìm thấy, ngược lại trả về None
    return match['TimeKey'].iloc[0] if not match.empty else None