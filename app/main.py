from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.arinc429 import build_word
from app.database import Base, SessionLocal, engine
from app.hardware import play_value_audio, send_serial

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Gestión de envíos ARINC 429", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/instruments", response_model=schemas.InstrumentRead, status_code=status.HTTP_201_CREATED)
def create_instrument(payload: schemas.InstrumentCreate, db: Session = Depends(get_db)):
    if db.scalar(select(models.Instrument).where(models.Instrument.name == payload.name)):
        raise HTTPException(409, "Ya existe un instrumento con ese nombre")
    instrument = models.Instrument(**payload.model_dump())
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


@app.get("/api/instruments", response_model=list[schemas.InstrumentRead])
def list_instruments(db: Session = Depends(get_db)):
    return list(db.scalars(select(models.Instrument).order_by(models.Instrument.name)))


@app.get("/api/instruments/{instrument_id}", response_model=schemas.InstrumentRead)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    instrument = db.get(models.Instrument, instrument_id)
    if instrument is None:
        raise HTTPException(404, "Instrumento no encontrado")
    return instrument


@app.put("/api/instruments/{instrument_id}", response_model=schemas.InstrumentRead)
def update_instrument(instrument_id: int, payload: schemas.InstrumentCreate, db: Session = Depends(get_db)):
    instrument = db.get(models.Instrument, instrument_id)
    if instrument is None:
        raise HTTPException(404, "Instrumento no encontrado")
    duplicate = db.scalar(select(models.Instrument).where(models.Instrument.name == payload.name, models.Instrument.id != instrument_id))
    if duplicate:
        raise HTTPException(409, "Ya existe un instrumento con ese nombre")
    for key, value in payload.model_dump().items():
        setattr(instrument, key, value)
    db.commit()
    db.refresh(instrument)
    return instrument


@app.delete("/api/instruments/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument(instrument_id: int, db: Session = Depends(get_db)):
    instrument = db.get(models.Instrument, instrument_id)
    if instrument is None:
        raise HTTPException(404, "Instrumento no encontrado")
    if instrument.shipments:
        raise HTTPException(409, "No se puede eliminar: el instrumento tiene envíos registrados")
    db.delete(instrument)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/shipments", response_model=schemas.ShipmentRead, status_code=status.HTTP_201_CREATED)
def create_shipment(payload: schemas.ShipmentCreate, db: Session = Depends(get_db)):
    instrument = db.get(models.Instrument, payload.instrument_id)
    if instrument is None or not instrument.active:
        raise HTTPException(404, "Instrumento inexistente o inactivo")
    try:
        word = build_word(label=instrument.label, sdi=instrument.sdi, value=payload.value,
                          resolution=instrument.resolution, ssm=instrument.ssm)
        details = [send_serial(word), play_value_audio(payload.value)]
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc
    shipment = models.Shipment(instrument_id=instrument.id, value=payload.value,
                               arinc_word=word, status="sent", output_note=" ".join(details))
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return _shipment_dict(shipment, instrument.name)


def _shipment_dict(shipment: models.Shipment, instrument_name: str):
    return {"id": shipment.id, "instrument_id": shipment.instrument_id,
            "instrument_name": instrument_name, "value": shipment.value,
            "arinc_word": shipment.arinc_word, "arinc_hex": f"0x{shipment.arinc_word:08X}",
            "status": shipment.status, "output_note": shipment.output_note,
            "created_at": shipment.created_at}


@app.get("/api/shipments", response_model=list[schemas.ShipmentRead])
def list_shipments(db: Session = Depends(get_db)):
    rows = db.scalars(select(models.Shipment).options(joinedload(models.Shipment.instrument)).order_by(models.Shipment.id.desc())).all()
    return [_shipment_dict(row, row.instrument.name) for row in rows]


@app.get("/api/shipments/{shipment_id}", response_model=schemas.ShipmentRead)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    row = db.scalar(select(models.Shipment).options(joinedload(models.Shipment.instrument)).where(models.Shipment.id == shipment_id))
    if row is None:
        raise HTTPException(404, "Envío no encontrado")
    return _shipment_dict(row, row.instrument.name)


@app.put("/api/shipments/{shipment_id}", response_model=schemas.ShipmentRead)
def update_shipment(shipment_id: int, payload: schemas.ShipmentCreate, db: Session = Depends(get_db)):
    row = db.get(models.Shipment, shipment_id)
    instrument = db.get(models.Instrument, payload.instrument_id)
    if row is None:
        raise HTTPException(404, "Envío no encontrado")
    if instrument is None or not instrument.active:
        raise HTTPException(404, "Instrumento inexistente o inactivo")
    try:
        word = build_word(label=instrument.label, sdi=instrument.sdi, value=payload.value,
                          resolution=instrument.resolution, ssm=instrument.ssm)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    row.instrument_id = instrument.id
    row.value = payload.value
    row.arinc_word = word
    row.status = "updated"
    row.output_note = "Registro actualizado; para transmitirlo cree un nuevo envío."
    db.commit()
    db.refresh(row)
    return _shipment_dict(row, instrument.name)


@app.delete("/api/shipments/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Shipment, shipment_id)
    if row is None:
        raise HTTPException(404, "Envío no encontrado")
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
