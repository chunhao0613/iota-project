import json
import hashlib

class DataHasher:
    @staticmethod
    def calculate_hash(temperature: float, humidity: float, power: float, timestamp: str, device_id: str, firmware_version: str) -> str:
        """
        Calculates a SHA-256 hash from IoT sensor readings including device metadata.
        To ensure reproducible hash results, we:
          1. Round floats to a fixed precision (4 decimal places).
          2. Structure the payload in a specific dict including device metadata.
          3. Convert to a canonical JSON string (keys sorted, separators compact).
          4. Compute SHA-256 hex digest.
        """
        payload = {
            "device_id": str(device_id),
            "firmware_version": str(firmware_version),
            "temperature": round(float(temperature), 4),
            "humidity": round(float(humidity), 4),
            "power": round(float(power), 4),
            "timestamp": str(timestamp)
        }
        # Canonical JSON string: keys sorted, no extra whitespace
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        # Calculate SHA256
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
