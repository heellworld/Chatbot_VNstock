# 📈 Chatbot VNStock - Trợ Lý Phân Tích Tài Chính

Chatbot VNStock là một ứng dụng trí tuệ nhân tạo hỗ trợ phân tích cổ phiếu trên thị trường Việt Nam. Dự án kết hợp giữa công nghệ xử lý ngôn ngữ tự nhiên, phân tích dữ liệu và ETL tự động thông qua Apache Airflow.

## 📋 Tính Năng

- 🤖 Chatbot thông minh hỗ trợ trả lời câu hỏi về cổ phiếu 
- 📊 Phân tích dữ liệu thị trường chứng khoán Việt Nam
- 🔄 ETL tự động với Apache Airflow
- 📝 Lưu trữ và phân tích dữ liệu trong Data Warehouse

## 🛠️ Công Nghệ Sử Dụng

- **Backend**: Python, FastAPI, SQLAlchemy
- **ETL**: Apache Airflow
- **Database**: PostgreSQL
- **Chatbot**: LangChain, LlamaIndex
- **Frontend**: Streamlit
- **Phân Tích Dữ Liệu**: Pandas, NumPy, VNStock
- **Môi Trường**: Docker

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống

- Python 3.9+
- Docker và Docker Compose
- PostgreSQL

### Các Bước Cài Đặt

1. **Clone Dự Án**
   ```bash
   git clone https://github.com/your-username/Chatbot_VNstock.git
   cd Chatbot_VNstock
   ```

2. **Cấu Hình Môi Trường**
   ```bash
   # Tạo file .env từ .env.example
   cp .env.example .env
   
   # Chỉnh sửa file .env với thông tin cá nhân của bạn
   # Đặc biệt là các API key cần thiết và thông tin database
   ```

3. **Cài Đặt Thư Viện**
   ```bash
   pip install -r requirements.txt
   ```

4. **Cấu Hình Database**
   - Tạo database PostgreSQL với tên "datawarehouse_stock"
   - Điều chỉnh thông tin kết nối trong file `dags/config/database.py`

## 🔧 Cấu Hình

### Database

Dự án sử dụng PostgreSQL làm cơ sở dữ liệu. Có hai cấu hình kết nối khác nhau:

1. **Cho Apache Airflow (Docker)**
   
   Trong file `dags/config/database.py`, sử dụng:
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:123456@host.docker.internal:5432/datawarehouse_stock"
   ```

2. **Cho Streamlit (Local)**
   
   Trong file `dags/config/database.py`, sử dụng:
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/datawarehouse_stock"
   ```

### API Keys

Chỉnh sửa file `.env` với các API key cần thiết:
- `OPENAI_API_KEY`: API key của OpenAI
- Các API key khác nếu cần

## 🏃‍♂️ Chạy Ứng Dụng

### Khởi Động Airflow

```bash
# Đảm bảo sử dụng cấu hình Database cho Docker trước khi chạy
# Chỉnh sửa file dags/config/database.py để sử dụng host.docker.internal

docker-compose up -d
```

Truy cập Airflow Web UI tại: http://localhost:8080 (tài khoản: airflow, mật khẩu: airflow)

### Chạy Streamlit Chatbot

```bash
# Đảm bảo sử dụng cấu hình Database cho Local trước khi chạy
# Chỉnh sửa file dags/config/database.py để sử dụng localhost

streamlit run frontend.py
```

Truy cập Streamlit UI tại: http://localhost:8501

## 📚 Cấu Trúc Dự Án

```
Chatbot_VNstock/
├── .env                    # Biến môi trường
├── alembic.ini             # Cấu hình alembic cho database migrations
├── config/                 # Cấu hình dự án
├── dags/                   # DAGs của Airflow
│   ├── config/             # Cấu hình cho DAGs
│   └── src/                # Mã nguồn ETL và xử lý dữ liệu
├── data/                   # Dữ liệu
├── docker-compose.yaml     # Cấu hình Docker
├── docs/                   # Tài liệu
├── frontend.py             # UI Streamlit
├── logs/                   # Log files
├── migrations/             # Database migrations
├── plugins/                # Airflow plugins
└── requirements.txt        # Thư viện yêu cầu
```

## 📝 Lưu Ý Quan Trọng

- Khi chạy Airflow (Docker), đảm bảo cấu hình database sử dụng `host.docker.internal` thay vì `localhost`
- Khi chạy Streamlit, đảm bảo cấu hình database sử dụng `localhost`
- API keys cần được cấu hình trong file `.env` trước khi chạy ứng dụng
- Database PostgreSQL cần được tạo trước với tên "datawarehouse_stock"

## 🤝 Đóng Góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request nếu bạn muốn cải thiện dự án.

## 📄 Giấy Phép

[MIT](LICENSE)


