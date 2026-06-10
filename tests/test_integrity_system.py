import sys
import os
import unittest
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hasher import DataHasher
from sensor.simulator import SensorSimulator

class TestIoTIntegritySystem(unittest.TestCase):
    def test_hasher_consistency(self):
        """Verify that the hashing function is reproducible for identical inputs."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        hash1 = DataHasher.calculate_hash(25.123456, 60.654321, 220.123, timestamp, "sensor_01", "1.0.0")
        hash2 = DataHasher.calculate_hash(25.123456, 60.654321, 220.123, timestamp, "sensor_01", "1.0.0")
        self.assertEqual(hash1, hash2)

    def test_hasher_rounding(self):
        """Verify that floating-point rounding provides resistance to micro-deviations."""
        timestamp = "2026-06-10T12:00:00Z"
        # Since we round to 4 decimal places:
        # 25.12341 -> 25.1234, 25.12344 -> 25.1234
        # 60.65432 -> 60.6543, 60.65434 -> 60.6543
        # 220.12341 -> 220.1234, 220.12344 -> 220.1234
        hash1 = DataHasher.calculate_hash(25.12341, 60.65432, 220.12341, timestamp, "sensor_01", "1.0.0")
        hash2 = DataHasher.calculate_hash(25.12344, 60.65434, 220.12344, timestamp, "sensor_01", "1.0.0")
        self.assertEqual(hash1, hash2)

    def test_sensor_simulator_ranges(self):
        """Verify that the sensor simulator generates readings within physically valid boundaries."""
        sim = SensorSimulator(hum_mu=110.0) # Intentionally high humidity mean
        reading = sim.generate_reading()
        
        self.assertIn("temperature", reading)
        self.assertIn("humidity", reading)
        self.assertIn("power", reading)
        self.assertIn("timestamp", reading)
        
        # Humidity must still be capped at 100%
        self.assertTrue(0.0 <= reading["humidity"] <= 100.0)
        self.assertTrue(reading["power"] >= 0.0)

if __name__ == "__main__":
    unittest.main()
