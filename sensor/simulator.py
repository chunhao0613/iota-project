import random
from datetime import datetime

class SensorSimulator:
    """
    Generates simulated IoT sensor data.
    Adds Gaussian noise to baseline values to simulate environmental measurements.
    """
    def __init__(self, temp_mu: float = 25.0, temp_sigma: float = 1.2,
                 hum_mu: float = 60.0, hum_sigma: float = 2.5,
                 power_mu: float = 220.0, power_sigma: float = 4.0):
        # Baselines and standard deviations
        self.temp_mu = temp_mu
        self.temp_sigma = temp_sigma
        self.hum_mu = hum_mu
        self.hum_sigma = hum_sigma
        self.power_mu = power_mu
        self.power_sigma = power_sigma

    def generate_reading(self) -> dict:
        """Generates a reading with Gaussian noise."""
        temp = random.gauss(self.temp_mu, self.temp_sigma)
        hum = random.gauss(self.hum_mu, self.hum_sigma)
        power = random.gauss(self.power_mu, self.power_sigma)
        
        # Ensure outputs are physically realistic
        hum = max(0.0, min(100.0, hum))
        power = max(0.0, power)
        
        # Timestamp formatted to UTC ISO-8601 (ending in Z)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return {
            "temperature": round(temp, 4),
            "humidity": round(hum, 4),
            "power": round(power, 4),
            "timestamp": timestamp
        }
