from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    label: Mapped[int] = mapped_column(Integer, default=0)
    sdi: Mapped[int] = mapped_column(Integer, default=0)
    encoding: Mapped[str] = mapped_column(String(16), default="BNR")
    ssm: Mapped[int] = mapped_column(Integer, default=0)
    resolution: Mapped[float] = mapped_column(Float, default=1.0)
    units: Mapped[str] = mapped_column(String(32), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="instrument")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"))
    value: Mapped[float] = mapped_column(Float)
    arinc_word: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="created")
    output_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    instrument: Mapped[Instrument] = relationship(back_populates="shipments")
