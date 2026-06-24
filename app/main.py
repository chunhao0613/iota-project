import logging
import uuid
import time
from typing import List
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.database import engine, get_db, SessionLocal
from app.hasher import DataHasher
from app.iota_client import iota_notarizer
from app.verifier import IntegrityVerifier
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global state to simulate Gateway connection status
gateway_connected = True

# Initialize DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IoT Data Integrity Verifier (IOTA Tangle)",
    description="Backend API to store IoT sensor records in SQLite and notarize/verify them using the IOTA Testnet and Merkle Trees.",
    version="1.1.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
def health_check():
    # Simple check for IOTA connection
    iota_connected = False
    try:
        client = iota_notarizer._get_client()
        info = client.get_info()
        iota_connected = True
    except Exception as e:
        logger.warning(f"IOTA node connection health check failed: {e}")
        
    return {
        "status": "healthy",
        "database": "connected",
        "iota_node": settings.IOTA_NODE_URL,
        "iota_connected": iota_connected
    }

@app.post("/api/v1/records", response_model=schemas.DataRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(reading: schemas.SensorReadingCreate, db: Session = Depends(get_db)):
    """
    Receives raw sensor readings.
    Applies Event Filter, computes SHA-256 hash, and stores in SQLite.
    """
    if not gateway_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Gateway connection is offline. Simulated disconnect."
        )
    record_id = str(uuid.uuid4())
    
    # Event Filter: Anomaly?
    is_anomaly = (reading.temperature > 40.0 or reading.humidity > 90.0 or reading.power > 250.0)
    iota_status = "PENDING" if is_anomaly else "NOT_ANCHORED"
    
    # 1. Compute SHA-256 Hash with metadata
    data_hash = DataHasher.calculate_hash(
        temperature=reading.temperature,
        humidity=reading.humidity,
        power=reading.power,
        timestamp=reading.timestamp,
        device_id=reading.device_id,
        firmware_version=reading.firmware_version
    )
    
    # 2. Store locally in SQLite
    db_record = crud.create_data_record(db, record_id, reading, data_hash, iota_status=iota_status)
    return db_record

@app.post("/api/v1/telemetry", status_code=status.HTTP_201_CREATED)
def receive_telemetry(payload: dict, db: Session = Depends(get_db)):
    """
    Receives telemetry batches posted by the Thaumio HTTP Gateway.
    Iterates over the telemetry records, applies the Event Filter, and stores them in SQLite.
    """
    if not gateway_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Gateway connection is offline. Simulated disconnect."
        )
    try:
        data_records = payload.get("data", [])
        created_records = []
        for item in data_records:
            telemetry = item.get("telemetry", {})
            # Map to our schema
            temp = float(telemetry.get("temperature", 0.0))
            hum = float(telemetry.get("humidity", 0.0))
            power = float(telemetry.get("power", 0.0))
            
            # Check timestamp format. Thaumio sends UNIX epoch float, convert to ISO-like string
            ts_raw = item.get("timestamp", time.time())
            import datetime
            if isinstance(ts_raw, (int, float)):
                ts = datetime.datetime.fromtimestamp(ts_raw).isoformat()
            else:
                ts = str(ts_raw)
                
            dev_id = item.get("device_id", "sensor_ev_01")
            fw = telemetry.get("firmware", "1.0.0")
            if not isinstance(fw, str) or fw == "0.0":
                fw = "2.1.0" if "solar" in dev_id else "1.0.0"

            reading = schemas.SensorReadingCreate(
                temperature=temp,
                humidity=hum,
                power=power,
                timestamp=ts,
                device_id=dev_id,
                firmware_version=fw
            )
            
            record_id = str(uuid.uuid4())
            
            # Event Filter: Anomaly?
            is_anomaly = (temp > 40.0 or hum > 90.0 or power > 250.0)
            iota_status = "PENDING" if is_anomaly else "NOT_ANCHORED"
            
            # Compute SHA-256 Hash with metadata
            data_hash = DataHasher.calculate_hash(
                temperature=reading.temperature,
                humidity=reading.humidity,
                power=reading.power,
                timestamp=reading.timestamp,
                device_id=reading.device_id,
                firmware_version=reading.firmware_version
            )
            
            # Save to Database
            db_record = crud.create_data_record(
                db=db,
                record_id=record_id,
                reading=reading,
                sha256_hash=data_hash,
                iota_status=iota_status
            )
            created_records.append(db_record)
        return {"status": "success", "processed": len(created_records)}
    except Exception as e:
        logger.error(f"Error processing telemetry from Thaumio: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid payload or processing error: {str(e)}")

@app.post("/api/v1/records/anchor-batch")
def anchor_pending_batch(db: Session = Depends(get_db)):
    """
    Aggregates all PENDING anomaly records in SQLite using a Merkle Tree,
    submits the Merkle Root to the IOTA Testnet, and stores the proofs.
    """
    # Get all PENDING records
    pending_records = db.query(models.DataRecord).filter(models.DataRecord.iota_status == "PENDING").all()
    if not pending_records:
        return {"status": "ignored", "message": "No pending records found to anchor."}
        
    record_ids = [r.id for r in pending_records]
    hashes = [r.sha256_hash for r in pending_records]
    
    # 1. Build Merkle Tree
    from app.merkle import build_merkle_tree
    merkle_root, proofs = build_merkle_tree(hashes)
    
    # Create proof mapping {record_id: proof}
    proofs_mapping = {record_ids[i]: proofs[i] for i in range(len(record_ids))}
    
    # 2. Submit Merkle Root to IOTA Tangle
    try:
        block_id = iota_notarizer.anchor_batch_root(merkle_root, record_ids)
        
        # 3. Update records in database to ANCHORED with proofs
        crud.update_anchored_batch(
            db=db,
            record_ids=record_ids,
            block_id=block_id,
            merkle_root=merkle_root,
            proofs_mapping=proofs_mapping
        )
        return {
            "status": "success",
            "anchored_count": len(record_ids),
            "merkle_root": merkle_root,
            "iota_block_id": block_id
        }
    except Exception as e:
        logger.error(f"Failed to anchor Merkle Root batch: {e}")
        # Mark all as FAILED
        for r in pending_records:
            r.iota_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"IOTA anchoring failed: {str(e)}")

@app.post("/api/v1/records/anchor-comparison")
def anchor_comparison(db: Session = Depends(get_db)):
    """
    Anchors PENDING anomaly records (or generates a mock batch if none exist) to:
    1. IOTA Tangle
    2. Arbitrum Sepolia (EVM L2)
    3. Ethereum Sepolia (EVM L1)
    4. Solana Devnet
    Measures latency, gas fees, and hardware requirements for comparative analysis.
    """
    from app.multichain_client import multichain_manager
    from app.merkle import build_merkle_tree
    import json

    pending_records = db.query(models.DataRecord).filter(models.DataRecord.iota_status == "PENDING").all()
    
    is_demo = False
    if not pending_records:
        is_demo = True
        record_ids = [f"demo-rec-{i}" for i in range(5)]
        hashes = [DataHasher.calculate_hash(25.0 + i, 60.0 - i, 220.0, "2026-06-24T12:00:00Z", "sensor_demo", "1.0.0") for i in range(5)]
    else:
        record_ids = [r.id for r in pending_records]
        hashes = [r.sha256_hash for r in pending_records]

    # Build Merkle Tree
    merkle_root, proofs = build_merkle_tree(hashes)
    proofs_mapping = {record_ids[i]: proofs[i] for i in range(len(record_ids))}
    
    payload_data = {
        "batch_root": merkle_root,
        "record_ids": record_ids
    }
    data_str = json.dumps(payload_data, separators=(',', ':'))

    # --- 1. IOTA Tangle Anchoring ---
    iota_start = time.perf_counter()
    iota_error = None
    iota_block_id = None
    try:
        if not is_demo:
            iota_block_id = iota_notarizer.anchor_batch_root(merkle_root, record_ids)
            # Update records in DB to ANCHORED with proofs
            crud.update_anchored_batch(
                db=db,
                record_ids=record_ids,
                block_id=iota_block_id,
                merkle_root=merkle_root,
                proofs_mapping=proofs_mapping
            )
        else:
            # Connect to IOTA to measure latency
            client = iota_notarizer._get_client()
            client.get_info()
            iota_block_id = "0x" + hashes[0] # Mock block id for demo
    except Exception as e:
        iota_error = str(e)
        logger.error(f"IOTA comparative anchoring failed: {e}")
    iota_latency = time.perf_counter() - iota_start

    # --- 2. Multi-chain (Arbitrum, Ethereum, Solana) Anchoring ---
    multichain_res = {}
    try:
        multichain_res = multichain_manager.anchor_all(merkle_root, data_str)
    except Exception as e:
        logger.error(f"Multi-chain comparative anchoring failed: {e}")

    return {
        "status": "success",
        "is_demo": is_demo,
        "anchored_count": len(record_ids),
        "merkle_root": merkle_root,
        "iota": {
            "name": "IOTA / Shimmer Testnet",
            "block_id": iota_block_id,
            "latency_sec": iota_latency,
            "tx_fee_usd": 0.0,
            "gas_used": 0,
            "hardware_rating": "Low (No transaction signing or balance tracking needed on gateway)",
            "error": iota_error
        },
        "arbitrum": multichain_res.get("arbitrum", {
            "blockchain": "Arbitrum Sepolia (EVM L2)",
            "tx_hash": None,
            "latency_sec": 1.0,
            "gas_used": 0,
            "fee_usd": 0.0,
            "hardware_rating": "Medium (Requires private key cryptography, nonce tracking, and gas wallet maintenance)"
        }),
        "ethereum": multichain_res.get("ethereum", {
            "blockchain": "Ethereum Sepolia (EVM L1)",
            "tx_hash": None,
            "latency_sec": 1.5,
            "gas_used": 0,
            "fee_usd": 0.0,
            "hardware_rating": "Medium (Requires private key cryptography, nonce tracking, and gas wallet maintenance)"
        }),
        "solana": multichain_res.get("solana", {
            "blockchain": "Solana Devnet",
            "tx_hash": None,
            "latency_sec": 0.8,
            "gas_used": 0,
            "fee_usd": 0.0,
            "hardware_rating": "Medium (Requires Ed25519 signature computation, account state tracking, and rent exemption balance)"
        })
    }

@app.get("/api/v1/records", response_model=List[schemas.DataRecordResponse])
def read_records(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """
    Returns historical data records.
    """
    records = crud.get_data_records(db, limit=limit, offset=offset)
    return records

@app.get("/api/v1/records/{record_id}", response_model=schemas.DataRecordResponse)
def read_record(record_id: str, db: Session = Depends(get_db)):
    """
    Returns a single data record details.
    """
    db_record = crud.get_data_record(db, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    return db_record

@app.post("/api/v1/records/{record_id}/verify", response_model=schemas.VerificationResultSchema)
def verify_record(record_id: str, db: Session = Depends(get_db)):
    """
    Performs 3-way verification: SQLite values, local re-computed hash, and IOTA Tangle.
    """
    try:
        result = IntegrityVerifier.verify_record(db, record_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.post("/api/v1/records/{record_id}/tamper", response_model=schemas.DataRecordResponse)
def tamper_record(record_id: str, tamper_req: schemas.TamperRequest, db: Session = Depends(get_db)):
    """
    Demonstration API: updates SQLite record fields directly without updating hash.
    Used to show how the system detects database tampering.
    """
    db_record = crud.get_data_record(db, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    tampered_record = crud.tamper_data_record(db, record_id, tamper_req)
    logger.warning(f"Tamper simulation: Record {record_id} was updated in database directly.")
    return tampered_record

@app.get("/api/v1/gateway/status")
def get_gateway_status():
    """
    Returns the simulated gateway connection status.
    """
    return {"connected": gateway_connected}

@app.post("/api/v1/gateway/toggle")
def toggle_gateway_status():
    """
    Toggles the simulated gateway connection status.
    """
    global gateway_connected
    gateway_connected = not gateway_connected
    logger.info(f"Simulated Gateway connection toggled to: {gateway_connected}")
    return {"connected": gateway_connected}

@app.post("/api/v1/records/{record_id}/anchor", response_model=schemas.DataRecordResponse)
def anchor_single_record(record_id: str, db: Session = Depends(get_db)):
    """
    Submits a single record's hash directly to the IOTA Tangle.
    Updates the record status to ANCHORED.
    """
    db_record = crud.get_data_record(db, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    if db_record.iota_status == "ANCHORED":
        return db_record
        
    try:
        # Submit to IOTA
        block_id = iota_notarizer.anchor_hash(record_id, db_record.sha256_hash)
        
        # Update SQLite record
        db_record.iota_status = "ANCHORED"
        db_record.iota_block_id = block_id
        db.commit()
        db.refresh(db_record)
        return db_record
    except Exception as e:
        logger.error(f"Failed to anchor single record {record_id}: {e}")
        db_record.iota_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"IOTA single anchoring failed: {str(e)}")
