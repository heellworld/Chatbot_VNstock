from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
# Cập nhật URL database (dùng 'postgresql' thay vì 'postgres')
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/datawarehouse_stock"

# SQLALCHEMY_DATABASE_URL = os.environ.get(
#     "DW_DATABASE_URL",
#     "postgresql+psycopg2://postgres:123456@host.docker.internal:5432/datawarehouse_stock"
# )
# Tạo sync engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    future=True  # Vẫn giữ future=True để dùng SQLAlchemy 2.0 style
)

# Tạo sessionmaker thông thường
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency cho database session sync
def get_db():
    """
    Hàm tạo và quản lý phiên cơ sở dữ liệu đồng bộ.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()