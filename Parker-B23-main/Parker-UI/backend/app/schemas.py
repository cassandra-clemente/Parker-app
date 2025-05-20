from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Union
from enum import Enum

class StatusEnum(str, Enum):
    unknown = "unknown"
    open = "open"
    full = "full"
    restricted = "restricted"

class ParkingLotBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    street_name: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[Union[int, str]] = Field(None)  # Allow both int and string
    borough: Optional[int] = Field(None, ge=1, le=5)
    status: StatusEnum = Field(default=StatusEnum.unknown)

    @field_validator('zip_code')
    def parse_zip_code(cls, value):
        if value == '' or value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @field_validator('last_updated', mode='before')
    def parse_datetime(cls, value):
        if isinstance(value, str):
            # Handle both with and without timezone
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing without timezone
                return datetime.strptime(value.split('.')[0], '%Y-%m-%d %H:%M:%S')
        return value

class ParkingLotCreate(ParkingLotBase):
    pass

class ParkingLot(ParkingLotBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
