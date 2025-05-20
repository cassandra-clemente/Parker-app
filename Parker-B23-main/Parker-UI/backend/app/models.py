from .database import Base
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Time
from sqlalchemy.sql import func

class ParkingLot(Base):
    __tablename__ = "parking_lots"
    
    id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    street_name = Column(String(100))
    zip_code = Column(Integer)
    borough = Column(Integer)
    status = Column(String(10), default='unknown')
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
#    time_limit_minutes = Column(Integer)
#    is_free = Column(Boolean)
#    no_parking_start = Column(Time)
#    no_parking_end = Column(Time)
