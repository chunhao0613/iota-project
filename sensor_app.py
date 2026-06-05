from data_ingestion import VirtualSensor
from dlt_connector import IOTAConnector

def main():
    print("=== 系統啟動：v0.1 概念驗證 ===")

    # 1. 初始化資料擷取層 (Data Ingestion Layer)
    sensor = VirtualSensor(device_id="Sensor-Alpha-01")

    # 2. 初始化核心上鏈層 (DLT Connector Layer)
    # 預設連線至 https://api.shimmer.network
    connector = IOTAConnector()

    # 3. 取得虛擬感測器數據
    print("\n[擷取資料] 正在從虛擬感測器讀取資料...")
    sensor_data = sensor.get_data()

    # 4. 透過核心上鏈層發送資料
    print("\n[發送資料] 正在將資料打包發送至 Tangle...")
    tag = "MY_FIRST_SENSOR"
    
    try:
        block_id = connector.send_data(tag=tag, payload_dict=sensor_data)
        print(f"\n[戰情室展示] 區塊 ID (Block ID): {block_id}")
        print("資料已成功上鏈，驗證無誤！")
    except Exception as e:
        print("\n[戰情室展示] 發生錯誤，無法完成上鏈程序。")

if __name__ == '__main__':
    main()