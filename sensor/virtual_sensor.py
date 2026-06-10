import time
import requests
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor.simulator import SensorSimulator

API_URL = "http://127.0.0.1:8000/api/v1/records"
INTERVAL = 5.0 # seconds

def main():
    print("=== IoT Virtual Sensor Daemon Starting ===")
    print(f"Target API Ingestion Endpoint: {API_URL}")
    print(f"Transmission interval: {INTERVAL} seconds")
    
    # Initialize simulator
    simulator = SensorSimulator()
    
    try:
        while True:
            # 1. Generate data
            reading = simulator.generate_reading()
            print(f"\n[{reading['timestamp']}] Generated reading:")
            print(f"  - Temp:  {reading['temperature']:.2f} C")
            print(f"  - Humid: {reading['humidity']:.2f} %")
            print(f"  - Power: {reading['power']:.2f} W")
            
            # 2. Post to FastAPI
            try:
                response = requests.post(API_URL, json=reading, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    print(f"  [OK] Posted successfully! DB Record ID: {data['id']}")
                    print(f"  [OK] Hash: {data['sha256_hash'][:10]}...")
                    print(f"  [OK] IOTA Status: {data['iota_status']}")
                else:
                    print(f"  [FAIL] Failed to post. HTTP Status: {response.status_code}. Response: {response.text}")
            except requests.exceptions.ConnectionError:
                print("  [FAIL] Connection Error: Backend API server appears to be offline.")
            except Exception as e:
                print(f"  [FAIL] Error sending reading: {e}")
                
            # 3. Wait for next interval
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        print("\n=== Virtual Sensor Daemon Terminated by User ===")

if __name__ == "__main__":
    main()
