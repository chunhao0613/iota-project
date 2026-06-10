from pydantic import BaseModel, Field
from typing import Optional, List

class SensorReadingCreate(BaseModel):
    temperature: float = Field(..., description="Temperature reading in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    power: float = Field(..., description="Power consumption in Watts")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the reading")
    device_id: Optional[str] = Field("sensor_ev_01", description="Unique device ID")
    firmware_version: Optional[str] = Field("1.0.0", description="Firmware version of the device")

class DataRecordResponse(BaseModel):
    id: str
    device_id: str
    firmware_version: str
    timestamp: str
    temperature: float
    humidity: float
    power: float
    sha256_hash: str
    iota_block_id: Optional[str] = None
    iota_status: str
    is_tampered: bool
    merkle_root: Optional[str] = None
    merkle_proof: Optional[str] = None

    class Config:
        from_attributes = True

class VerificationResultSchema(BaseModel):
    record_id: str
    checked_at: str
    calculated_hash: str
    db_stored_hash: str
    iota_stored_hash: Optional[str] = None
    local_match: bool
    iota_match: bool
    is_valid: bool
    risk_level: str
    details: Optional[str] = None

    class Config:
        from_attributes = True

class TamperRequest(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    power: Optional[float] = None
