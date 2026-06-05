import json
from iota_sdk import Client

class IOTAConnector:
    """
    核心上鏈層
    負責與 IOTA 網路連線，處理資料格式轉換(JSON轉Hex)並發送至 Tangle。
    """
    def __init__(self, node_url='https://api.shimmer.network'):
        self.node_url = node_url
        print(f"正在連線至 IOTA 節點: {self.node_url} ...")
        self.client = Client(nodes=[self.node_url])

    def send_data(self, tag: str, payload_dict: dict) -> str:
        """
        將字典格式的資料上鏈
        :param tag: 資料標籤，用於檢索
        :param payload_dict: 要上鏈的資料字典
        :return: Block ID
        """
        try:
            # 將字典轉換為 JSON 字串
            json_data = json.dumps(payload_dict)
            print(f"準備發送的資料: {json_data}")

            # IOTA SDK 底層要求將字串轉為 hex (十六進制) 格式進行傳輸，且需以 0x 開頭
            hex_data = "0x" + json_data.encode("utf-8").hex()
            hex_tag = "0x" + tag.encode("utf-8").hex()

            # 建立並發送一個包含資料的區塊 (Block)
            # 因為我們只是傳送資料，沒有動到資金，所以這是一個 0 價值交易
            block = self.client.build_and_post_block(tag=hex_tag, data=hex_data)

            # block 變數會回傳一個包含 (block_id, block_data) 的元組
            block_id = block[0]

            print("\n[OK] 資料發送成功！")
            return block_id

        except Exception as e:
            print(f"\n[ERROR] 發送失敗，發生錯誤: {e}")
            raise e
