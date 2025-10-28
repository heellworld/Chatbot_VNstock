from config.database import SessionLocal
from src.models import DimTime, DimCompany, DimRatio, FactFinancialRatios, FactStockPrice
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

def load_dim_time(dim_time_df: pd.DataFrame):
    with SessionLocal() as session:
        for _, row in dim_time_df.iterrows():
            # Tạo câu lệnh insert với on_conflict_do_nothing
            stmt = insert(DimTime).values(
                TimeKey=row['TimeKey'],
                Date=row['Date'],
                Year=row['Year'],
                Quarter=row['Quarter'],
                Month=row['Month'],
                Week=row['Week'],
                Day=row['Day']
            ).on_conflict_do_nothing(index_elements=['TimeKey'])
            
            # Thực thi câu lệnh
            session.execute(stmt)
        session.commit()

def load_dim_company(dim_company_df: pd.DataFrame):
    with SessionLocal() as session:
        for _, row in dim_company_df.iterrows():
            stmt = insert(DimCompany).values(
                StockKey=row['StockKey'],
                StockSymbol=row['StockSymbol'],
                CompanyName=row['CompanyName'],
                ShortName=row['ShortName'],
                Industry=row['Industry'],
                CompanyType=row['CompanyType'],
                StockRating=row['StockRating']
            ).on_conflict_do_nothing(index_elements=['StockKey'])
            session.execute(stmt)
        session.commit()

def load_dim_ratio(dim_ratio_df: pd.DataFrame):
    with SessionLocal() as session:
        for _, row in dim_ratio_df.iterrows():
            dim_ratio = DimRatio(
                RatioKey=row['RatioKey'],
                RatioName=row['RatioName'],
                Unit=row['Unit'],
                RatioType=row['RatioType']
            )
            session.add(dim_ratio)
        session.commit()

def load_fact_financial_ratios(fact_ratios_df: pd.DataFrame, stock_key_map: dict, ratio_key_map: dict):
    with SessionLocal() as session:
        for _, row in fact_ratios_df.iterrows():
            stock_key = stock_key_map.get(row['StockSymbol'])
            ratio_key = ratio_key_map.get(row['RatioName'])
            if stock_key and ratio_key:
                fact_ratio = FactFinancialRatios(
                    TimeKey=int(row['TimeKey']),
                    StockKey=stock_key,
                    RatioKey=ratio_key,
                    Value=row['Value']
                )
                session.add(fact_ratio)
        session.commit()

def load_fact_stock_price(fact_stock_price_df: pd.DataFrame, stock_key_map: dict):
    with SessionLocal() as session:
        for _, row in fact_stock_price_df.iterrows():
            stock_key = stock_key_map.get(row['StockSymbol'])
            if stock_key:
                fact_stock_price = FactStockPrice(
                    TimeKey=int(row['TimeKey']),
                    StockKey=stock_key,
                    Open=row['open'],
                    High=row['high'],
                    Low=row['low'],
                    Close=row['close'],
                    Volume=int(row['volume']) if pd.notna(row['volume']) else None
                )
                session.add(fact_stock_price)
        session.commit()

# Hàm get_stock_key_map (giữ nguyên cấu trúc)
def get_stock_key_map():
    with SessionLocal() as session:
        companies = session.query(DimCompany).all()
        if not companies:
            raise ValueError("Không có dữ liệu trong bảng DimCompany")
        return {company.StockSymbol: company.StockKey for company in companies}