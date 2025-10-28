from sqlalchemy import Column, Integer, Date
from config.database import Base

class DimTime(Base):
    __tablename__ = 'Dim_Time'
    
    TimeKey = Column(Integer, primary_key=True)
    Date = Column(Date)
    Year = Column(Integer)
    Quarter = Column(Integer)
    Month = Column(Integer)
    Week = Column(Integer)
    Day = Column(Integer)