from sqlalchemy import Column, Integer, String, NUMERIC
from config.database import Base

class DimCompany(Base):
    __tablename__ = 'Dim_Company'
    
    StockKey = Column(Integer, primary_key=True)
    StockSymbol = Column(String(10))
    CompanyName = Column(String(100))
    ShortName = Column(String(50))
    Industry = Column(String(30))
    CompanyType = Column(String(10))
    StockRating = Column(NUMERIC(5, 2))