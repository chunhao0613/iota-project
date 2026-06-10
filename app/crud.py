from sqlalchemy.orm import Session
from app import models, schemas
from datetime import datetime

def create_data_record(db: Session, record_id: str, reading: schemas.SensorReadingCreate, sha256_hash: str, iota_status: str = "PENDING") -> models.DataRecord:
    db_record = models.DataRecord(
        id=record_id,
        device_id=reading.device_id,
        firmware_version=reading.firmware_version,
        timestamp=reading.timestamp,
        temperature=reading.temperature,
        humidity=reading.humidity,
        power=reading.power,
        sha256_hash=sha256_hash,
        iota_block_id=None,
        iota_status=iota_status,
        is_tampered=False
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def update_data_record_block(db: Session, record_id: str, block_id: str, status: str = "ANCHORED") -> models.DataRecord:
    db_record = db.query(models.DataRecord).filter(models.DataRecord.id == record_id).first()
    if db_record:
        db_record.iota_block_id = block_id
        db_record.iota_status = status
        db.commit()
        db.refresh(db_record)
    return db_record

def update_anchored_batch(db: Session, record_ids: list, block_id: str, merkle_root: str, proofs_mapping: dict):
    import json
    for r_id in record_ids:
        db_record = db.query(models.DataRecord).filter(models.DataRecord.id == r_id).first()
        if db_record:
            db_record.iota_block_id = block_id
            db_record.iota_status = "ANCHORED"
            db_record.merkle_root = merkle_root
            db_record.merkle_proof = json.dumps(proofs_mapping.get(r_id, []))
    db.commit()

def get_data_record(db: Session, record_id: str) -> models.DataRecord:
    return db.query(models.DataRecord).filter(models.DataRecord.id == record_id).first()

def get_data_records(db: Session, limit: int = 50, offset: int = 0):
    # Retrieve records sorted by timestamp descending
    return db.query(models.DataRecord).order_by(models.DataRecord.timestamp.desc()).offset(offset).limit(limit).all()

def tamper_data_record(db: Session, record_id: str, tamper_req: schemas.TamperRequest) -> models.DataRecord:
    db_record = db.query(models.DataRecord).filter(models.DataRecord.id == record_id).first()
    if db_record:
        if tamper_req.temperature is not None:
            db_record.temperature = tamper_req.temperature
        if tamper_req.humidity is not None:
            db_record.humidity = tamper_req.humidity
        if tamper_req.power is not None:
            db_record.power = tamper_req.power
        
        # Mark as tampered but DO NOT recalculate the hash or touch IOTA Block ID
        db_record.is_tampered = True
        db.commit()
        db.refresh(db_record)
    return db_record

def create_verification_log(db: Session, record_id: str, calculated_hash: str, stored_hash: str, iota_hash: str, local_match: bool, iota_match: bool, is_valid: bool, details: str) -> models.VerificationLog:
    db_log = models.VerificationLog(
        record_id=record_id,
        checked_at=datetime.utcnow().isoformat(),
        calculated_hash=calculated_hash,
        stored_hash=stored_hash,
        iota_hash=iota_hash,
        local_match=local_match,
        iota_match=iota_match,
        is_valid=is_valid,
        details=details
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_verification_logs(db: Session, record_id: str):
    return db.query(models.VerificationLog).filter(models.VerificationLog.record_id == record_id).order_by(models.VerificationLog.checked_at.desc()).all()
