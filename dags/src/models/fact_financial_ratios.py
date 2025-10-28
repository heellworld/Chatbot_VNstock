from sqlalchemy import Column, Integer, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from config.database import Base

class FactFinancialRatios(Base):
    __tablename__ = 'Fact_FinancialRatios'
    
    TimeKey = Column(Integer, ForeignKey('Dim_Time.TimeKey'), primary_key=True)
    StockKey = Column(Integer, ForeignKey('Dim_Company.StockKey'), primary_key=True)
    RatioKey = Column(Integer, ForeignKey('Dim_Ratio.RatioKey'), primary_key=True)
    Value = Column(DECIMAL(20, 4))
    
    # Relationships (tùy chọn, hỗ trợ truy vấn ORM)
    time = relationship("DimTime", backref="fact_financial_ratios")
    company = relationship("DimCompany", backref="fact_financial_ratios")
    ratio = relationship("DimRatio", backref="fact_financial_ratios")