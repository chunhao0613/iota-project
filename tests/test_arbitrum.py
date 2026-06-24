import unittest
from unittest.mock import patch, MagicMock
from app.arbitrum_client import ArbitrumSepoliaClient

class TestArbitrumSepoliaClient(unittest.TestCase):
    def setUp(self):
        self.client = ArbitrumSepoliaClient()

    def test_gas_estimation_logic(self):
        """Test calculation of EVM gas for calldata (0x00 is 4 gas, non-zero is 16 gas)."""
        # Data containing 3 zero bytes and 3 non-zero bytes (e.g., b'\x00\x00\x00\x01\x02\x03')
        # Wait, the string "abc\x00" contains 'a', 'b', 'c', and a null byte.
        # Let's test with a simple string "hello" (5 bytes, all non-zero)
        # Expected: 21000 base + 5 * 16 = 21080 gas
        cost_details = self.client.estimate_anchoring_cost("hello")
        self.assertEqual(cost_details["gas_used"], 21080)
        
    @patch("app.arbitrum_client.requests.post")
    def test_gas_price_query(self, mock_post):
        """Test fetching gas price from RPC and correct calculations."""
        # Mock eth_gasPrice response: 0.1 Gwei (100,000,000 wei)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x5f5e100" # 100,000,000 in hex
        }
        mock_post.return_value = mock_response
        
        cost_details = self.client.estimate_anchoring_cost("hello")
        self.assertEqual(cost_details["gas_price_gwei"], 0.1)
        self.assertAlmostEqual(cost_details["fee_eth"], (21080 * 100000000) / 1e18)

    @patch("app.arbitrum_client.requests.post")
    def test_simulated_batch_anchoring(self, mock_post):
        """Test simulated anchoring returns correct layout and measurements."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456" # Mock block number/gas price
        }
        mock_post.return_value = mock_response
        
        res = self.client.anchor_batch_root("mock_root", ["rec1", "rec2"])
        
        self.assertEqual(res["blockchain"], "Arbitrum Sepolia (EVM L2)")
        self.assertTrue(res["tx_hash"].startswith("0x"))
        self.assertEqual(res["status"], "success (simulated)")
        self.assertIn("gas_used", res)
        self.assertIn("fee_usd", res)

if __name__ == "__main__":
    unittest.main()
