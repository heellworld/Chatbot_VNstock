from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, BigInteger
from sqlalchemy.orm import relationship
from config.database import Base

class FactStockPrice(Base):
    __tablename__ = 'Fact_StockPrice'
    
    TimeKey = Column(Integer, ForeignKey('Dim_Time.TimeKey'), primary_key=True)
    StockKey = Column(Integer, ForeignKey('Dim_Company.StockKey'), primary_key=True)
    Open = Column(DECIMAL(10, 4))
    High = Column(DECIMAL(10, 4))
    Low = Column(DECIMAL(10, 4))
    Close = Column(DECIMAL(10, 4))
    Volume = Column(BigInteger)
    
    # Relationships (tùy chọn, hỗ trợ truy vấn ORM)
    time = relationship("DimTime", backref="fact_stock_prices")
    company = relationship("DimCompany", backref="fact_stock_prices")