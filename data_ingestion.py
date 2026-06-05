import random
import time

class VirtualSensor:
    """
    虛擬環境感測器
    負責模擬隨機的環境數據，提供標準的 JSON 介面給核心上鏈層。
    """
    def __init__(self, device_id="Virtual-Sensor-01"):
        self.device_id = device_id

    def get_data(self) -> dict:
        """
        取得模擬的環境數據
        :return: 包含感測數據的字典格式
        """
        # 模擬溫濕度些微波動
        temperature = round(random.uniform(20.0, 30.0), 2)
        humidity = round(random.uniform(40.0, 70.0), 2)
        
        data = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "temperature": temperature,
            "humidity": humidity,
            "message": "Virtual sensor data generated"
        }
        return data

if __name__ == "__main__":
    # 簡單的單元測試
    sensor = VirtualSensor()
    print("Test VirtualSensor Output:", sensor.get_data())
