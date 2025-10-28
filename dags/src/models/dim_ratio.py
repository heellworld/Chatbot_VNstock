from sqlalchemy import Column, Integer, String
from config.database import Base

class DimRatio(Base):
    __tablename__ = 'Dim_Ratio'
    
    RatioKey = Column(Integer, primary_key=True)
    RatioName = Column(String(50))
    Unit = Column(String(20))
    RatioType = Column(String(50))