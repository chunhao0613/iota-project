import unittest
import hashlib
from app.merkle import build_merkle_tree, verify_merkle_proof

class TestMerkleTree(unittest.TestCase):
    def test_empty(self):
        root, proofs = build_merkle_tree([])
        self.assertEqual(root, "")
        self.assertEqual(proofs, [])

    def test_single_leaf(self):
        h1 = hashlib.sha256(b"hello").hexdigest()
        root, proofs = build_merkle_tree([h1])
        self.assertEqual(root, h1)
        self.assertEqual(proofs, [[]])
        self.assertTrue(verify_merkle_proof(h1, [], root))

    def test_even_leaves(self):
        h1 = hashlib.sha256(b"data1").hexdigest()
        h2 = hashlib.sha256(b"data2").hexdigest()
        
        root, proofs = build_merkle_tree([h1, h2])
        
        # Root should be sha256(h1_bytes + h2_bytes)
        expected_root = hashlib.sha256(bytes.fromhex(h1) + bytes.fromhex(h2)).hexdigest()
        self.assertEqual(root, expected_root)
        
        # Verify proofs
        self.assertTrue(verify_merkle_proof(h1, proofs[0], root))
        self.assertTrue(verify_merkle_proof(h2, proofs[1], root))
        
        # Tampered verification should fail
        self.assertFalse(verify_merkle_proof(h1 + "ff", proofs[0], root))

    def test_odd_leaves(self):
        h1 = hashlib.sha256(b"data1").hexdigest()
        h2 = hashlib.sha256(b"data2").hexdigest()
        h3 = hashlib.sha256(b"data3").hexdigest()
        
        root, proofs = build_merkle_tree([h1, h2, h3])
        
        # Verify all proofs
        self.assertTrue(verify_merkle_proof(h1, proofs[0], root))
        self.assertTrue(verify_merkle_proof(h2, proofs[1], root))
        self.assertTrue(verify_merkle_proof(h3, proofs[2], root))

if __name__ == "__main__":
    unittest.main()
