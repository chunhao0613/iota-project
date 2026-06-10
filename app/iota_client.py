import json
import logging
from iota_sdk import Client
from app.config import settings

logger = logging.getLogger(__name__)

class IotaNotarizer:
    def __init__(self, node_url: str = None, tag: str = None):
        self.node_url = node_url or settings.IOTA_NODE_URL
        self.tag = tag or settings.IOTA_TAG
        self._client = None

    def _get_client(self) -> Client:
        """Lazy initialization of the IOTA SDK Client."""
        if self._client is None:
            logger.info(f"Connecting to IOTA/Shimmer node: {self.node_url}")
            # ignore_node_health=True ensures the client doesn't block if a single node fails health check
            self._client = Client(nodes=[self.node_url], ignore_node_health=True)
        return self._client

    def anchor_hash(self, record_id: str, data_hash: str) -> str:
        """
        Publishes a SHA-256 hash and corresponding Record ID to the IOTA Tangle.
        Uses TaggedData payload type (L1 zero-value data transaction).
        Returns:
            str: The unique IOTA Block ID.
        """
        client = self._get_client()
        
        # Prepare content payload
        payload_data = {
            "record_id": record_id,
            "hash": data_hash
        }
        json_str = json.dumps(payload_data, separators=(',', ':'))
        
        # The IOTA SDK requires the tag and data payloads to be hex-encoded strings with '0x' prefix
        hex_tag = "0x" + self.tag.encode("utf-8").hex()
        hex_data = "0x" + json_str.encode("utf-8").hex()
        
        logger.info(f"Submitting block to Tangle. Record ID: {record_id}, Hash: {data_hash}")
        block = client.build_and_post_block(
            tag=hex_tag,
            data=hex_data
        )
        
        # build_and_post_block returns a list: [block_id, block_data]
        block_id = block[0]
        logger.info(f"Block posted successfully. Block ID: {block_id}")
        return block_id

    def anchor_batch_root(self, batch_root: str, record_ids: list) -> str:
        """
        Publishes a Merkle Root and list of Record IDs to the IOTA Tangle.
        Uses TaggedData payload type (L1 zero-value data transaction).
        Returns:
            str: The unique IOTA Block ID.
        """
        client = self._get_client()
        
        # Prepare content payload
        payload_data = {
            "batch_root": batch_root,
            "record_ids": record_ids
        }
        json_str = json.dumps(payload_data, separators=(',', ':'))
        
        # The IOTA SDK requires the tag and data payloads to be hex-encoded strings with '0x' prefix
        hex_tag = "0x" + self.tag.encode("utf-8").hex()
        hex_data = "0x" + json_str.encode("utf-8").hex()
        
        logger.info(f"Submitting Merkle Root batch to Tangle. Root: {batch_root}, Records count: {len(record_ids)}")
        block = client.build_and_post_block(
            tag=hex_tag,
            data=hex_data
        )
        
        block_id = block[0]
        logger.info(f"Batch block posted successfully. Block ID: {block_id}")
        return block_id

    def fetch_anchored_hash(self, block_id: str) -> dict:
        """
        Fetches the anchored data from the IOTA Tangle using a Block ID.
        Decodes the hex payload back to original dictionary.
        Returns:
            dict: {"record_id": str, "hash": str} or {"hash": str, "record_ids": list}
        """
        client = self._get_client()
        logger.info(f"Fetching block data from Tangle for Block ID: {block_id}")
        
        # Get raw block data from node (returns a Block object)
        block = client.get_block_data(block_id)
        
        if not block or not getattr(block, "payload", None):
            raise ValueError(f"Block {block_id} does not contain a payload.")
            
        payload = block.payload
        payload_type = getattr(payload, "type", None)
        if payload_type != 5: # TaggedData type is 5
            raise ValueError(f"Block {block_id} payload type is not TaggedData (type 5).")
            
        data_hex = getattr(payload, "data", None)
        if not data_hex:
            raise ValueError(f"Block {block_id} payload does not contain data.")
            
        # Decode the hex payload (removing '0x' prefix)
        clean_hex = data_hex[2:] if data_hex.startswith("0x") else data_hex
        decoded_bytes = bytes.fromhex(clean_hex)
        decoded_str = decoded_bytes.decode("utf-8")
        
        # Load JSON representation
        data_dict = json.loads(decoded_str)
        # Normalize: if it is a batch root, map to "hash" field for downstream verifiers
        if "batch_root" in data_dict:
            return {
                "hash": data_dict["batch_root"],
                "record_ids": data_dict.get("record_ids", [])
            }
        return data_dict

# Global singleton instance
iota_notarizer = IotaNotarizer()
