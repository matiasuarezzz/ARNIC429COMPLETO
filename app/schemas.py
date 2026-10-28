from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InstrumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    label: int = Field(default=0, ge=0, le=255)
    sdi: int = Field(default=0, ge=0, le=3)
    encoding: Literal["BNR", "DISCRETE"] = "BNR"
    ssm: int = Field(default=0, ge=0, le=3)
    resolution: float = Field(default=1.0, gt=0)
    units: str = Field(default="", max_length=32)
    active: bool = True


class InstrumentRead(InstrumentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShipmentCreate(BaseModel):
    instrument_id: int = Field(gt=0)
    value: float = Field(allow_inf_nan=False)


class ShipmentRead(BaseModel):
    id: int
    instrument_id: int
    instrument_name: str
    value: float
    arinc_word: int
    arinc_hex: str
    status: str
    output_note: str
    created_at: datetime
