import hashlib
from typing import List, Tuple, Dict, Any

def sha256_double(data: bytes) -> bytes:
    """Computes double SHA-256 for cryptographic strength (standard in Bitcoin/ledger systems)."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def sha256_single(data: bytes) -> bytes:
    """Computes single SHA-256."""
    return hashlib.sha256(data).digest()

def build_merkle_tree(hashes: List[str]) -> Tuple[str, List[List[Dict[str, Any]]]]:
    """
    Builds a Merkle Tree from a list of hex-encoded SHA-256 hashes.
    
    Returns:
        Tuple[str, List[List[dict]]]:
            - The Merkle Root (hex string).
            - A list of proofs for each input hash in the same order.
              Each proof is a list of steps: [{"sibling": "hex_hash", "is_left": bool}]
    """
    if not hashes:
        return "", []
        
    n = len(hashes)
    if n == 1:
        # If there's only one leaf, it is the root itself; proof is empty
        return hashes[0], [[]]
        
    # Convert hex strings to bytes
    leaves = [bytes.fromhex(h) for h in hashes]
    
    # Store proof steps for each leaf
    proofs = [[] for _ in range(n)]
    
    # Keep track of the active index of each leaf in the current layer
    active_indices = list(range(n))
    current_layer = list(leaves)
    
    while len(current_layer) > 1:
        next_layer = []
        next_active_indices = []
        
        # If the layer has an odd number of nodes, duplicate the last node
        is_odd = len(current_layer) % 2 != 0
        if is_odd:
            current_layer.append(current_layer[-1])
            
        for i in range(0, len(current_layer), 2):
            left = current_layer[i]
            right = current_layer[i+1]
            parent = sha256_single(left + right)
            next_layer.append(parent)
            
            # Record sibling proofs for all original leaf elements mapped to this step
            for idx in range(n):
                pos = active_indices[idx]
                if pos == i:
                    # Sibling is right
                    proofs[idx].append({"sibling": right.hex(), "is_left": False})
                    next_active_indices.append(len(next_layer) - 1)
                elif pos == i + 1:
                    # Sibling is left
                    proofs[idx].append({"sibling": left.hex(), "is_left": True})
                    next_active_indices.append(len(next_layer) - 1)
                    
        current_layer = next_layer
        active_indices = next_active_indices
        
    merkle_root = current_layer[0].hex()
    return merkle_root, proofs

def verify_merkle_proof(leaf_hash: str, proof: List[Dict[str, Any]], root_hash: str) -> bool:
    """
    Verifies that a leaf hash belongs to a Merkle Tree with the given root hash.
    """
    if not root_hash:
        return False
    if not proof:
        return leaf_hash == root_hash
        
    curr = bytes.fromhex(leaf_hash)
    for step in proof:
        sibling = bytes.fromhex(step["sibling"])
        if step["is_left"]:
            curr = sha256_single(sibling + curr)
        else:
            curr = sha256_single(curr + sibling)
            
    return curr.hex() == root_hash
