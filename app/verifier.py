import logging
import json
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.hasher import DataHasher
from app.iota_client import iota_notarizer
from app.merkle import verify_merkle_proof

logger = logging.getLogger(__name__)

class IntegrityVerifier:
    @staticmethod
    def verify_record(db: Session, record_id: str) -> schemas.VerificationResultSchema:
        """
        Executes a 3-way integrity check on an IoT record:
        1. Recalculates the SHA-256 hash using the SQLite record's raw values and device metadata.
        2. Compares the recalculated hash with the hash stored in SQLite.
        3. Validates the hash against the IOTA Tangle.
           - If it is a normal record (NOT_ANCHORED), verifies local database integrity.
           - If it is an anchored anomaly, verifies the Merkle Proof against the anchored Merkle Root on IOTA.
        Logs the audit trail in `verification_logs` table.
        """
        db_record = crud.get_data_record(db, record_id)
        if not db_record:
            raise ValueError(f"Record with ID {record_id} not found in database.")

        # 1. Recalculate local hash including device metadata
        calculated_hash = DataHasher.calculate_hash(
            temperature=db_record.temperature,
            humidity=db_record.humidity,
            power=db_record.power,
            timestamp=db_record.timestamp,
            device_id=db_record.device_id,
            firmware_version=db_record.firmware_version
        )
        
        db_stored_hash = db_record.sha256_hash
        local_match = (calculated_hash == db_stored_hash)
        
        iota_stored_hash = None
        iota_match = False
        details_list = []
        
        # 2. Fetch and verify against IOTA Tangle based on status
        if db_record.iota_status == "NOT_ANCHORED":
            iota_match = True  # Verified locally, anchoring not expected for normal telemetry
            details_list.append("Normal reading verified locally. Not anchored to IOTA (Event Filtering).")
        elif not db_record.iota_block_id:
            details_list.append("Verification Warning: IOTA Block ID is missing or pending.")
        else:
            try:
                iota_payload = iota_notarizer.fetch_anchored_hash(db_record.iota_block_id)
                iota_stored_hash = iota_payload.get("hash")
                
                # Check if this record uses Merkle Tree aggregation
                if db_record.merkle_proof:
                    proof = json.loads(db_record.merkle_proof)
                    # Reconstruct and verify Merkle Root
                    iota_match = verify_merkle_proof(calculated_hash, proof, iota_stored_hash)
                    if not iota_match:
                        details_list.append("Merkle proof verification failed against the anchored Merkle Root.")
                else:
                    # Legacy or direct single-record anchoring
                    anchored_id = iota_payload.get("record_id")
                    if anchored_id != record_id:
                        details_list.append(f"IOTA Warning: Anchored record_id '{anchored_id}' does not match SQLite record_id '{record_id}'.")
                    iota_match = (calculated_hash == iota_stored_hash)
                
            except Exception as e:
                logger.error(f"Error fetching block {db_record.iota_block_id} from IOTA: {e}")
                details_list.append(f"Error fetching from IOTA Tangle: {str(e)}")

        # 3. Determine Risk Level
        # VALID: Local database is correct and IOTA validation passes (or not anchored normal data is intact)
        # WARNING: Local database has been tampered with (recalculated hash != stored hash)
        # CRITICAL: Local hash does not match the blockchain ledger (ledger forgery/mismatch)
        if local_match and iota_match:
            risk_level = "VALID"
        elif not local_match:
            risk_level = "WARNING"
        else:
            risk_level = "CRITICAL"

        is_valid = (risk_level == "VALID")

        # Build status description
        if risk_level == "VALID":
            status_desc = "Integrity VERIFIED. Local data, database, and IOTA Tangle are fully aligned."
        elif risk_level == "WARNING":
            status_desc = f"Integrity COMPROMISED: Local database record does not match its local hash (database tampering). DB: {db_stored_hash[:8]} vs Calc: {calculated_hash[:8]}"
        else:
            status_desc = f"Integrity COMPROMISED: Local hash does not match IOTA anchored ledger (unauthorized modification or ledger mismatch). Calc: {calculated_hash[:8]}"

        if details_list:
            status_desc += " | Notes: " + " ; ".join(details_list)

        # Log audit trail in SQLite
        db_log = crud.create_verification_log(
            db=db,
            record_id=record_id,
            calculated_hash=calculated_hash,
            stored_hash=db_stored_hash,
            iota_hash=iota_stored_hash,
            local_match=local_match,
            iota_match=iota_match,
            is_valid=is_valid,
            details=status_desc
        )

        return schemas.VerificationResultSchema(
            record_id=db_log.record_id,
            checked_at=db_log.checked_at,
            calculated_hash=db_log.calculated_hash,
            db_stored_hash=db_log.stored_hash,
            iota_stored_hash=db_log.iota_hash,
            local_match=db_log.local_match,
            iota_match=db_log.iota_match,
            is_valid=db_log.is_valid,
            risk_level=risk_level,
            details=db_log.details
        )
