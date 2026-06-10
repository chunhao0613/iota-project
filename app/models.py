from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class DataRecord(Base):
    __tablename__ = "data_records"

    id = Column(String, primary_key=True, index=True) # UUID string
    device_id = Column(String, nullable=False, default="sensor_ev_01")
    firmware_version = Column(String, nullable=False, default="1.0.0")
    timestamp = Column(String, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    sha256_hash = Column(String, nullable=False) # Stored hash of the readings
    iota_block_id = Column(String, nullable=True, index=True) # Anchoring proof
    iota_status = Column(String, default="PENDING") # PENDING, ANCHORED, FAILED, NOT_ANCHORED
    is_tampered = Column(Boolean, default=False) # Helper flag for testing/demo tampering
    merkle_root = Column(String, nullable=True) # Root of the Merkle Tree batch
    merkle_proof = Column(String, nullable=True) # JSON representation of the Merkle path proof

    # Relationship to verification logs
    verification_logs = relationship("VerificationLog", back_populates="record", cascade="all, delete-orphan")

class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, ForeignKey("data_records.id"), nullable=False)
    checked_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    calculated_hash = Column(String, nullable=False)
    stored_hash = Column(String, nullable=False)
    iota_hash = Column(String, nullable=True) # Can be null if fetching from IOTA fails
    local_match = Column(Boolean, nullable=False)
    iota_match = Column(Boolean, nullable=False)
    is_valid = Column(Boolean, nullable=False) # local_match AND iota_match
    details = Column(String, nullable=True)

    # Relationship
    record = relationship("DataRecord", back_populates="verification_logs")
