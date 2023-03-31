from transaction.transaction import Transaction
from time import time
from node.node import Node
import hashlib


class Block:
    def __init__(
        self,
        _number: int,
        _timestamp: int,
        _nonce: int,
        _prev_hash: str,
        _txs: list[Transaction],
    ):
        self.number = _number
        self.timestamp = _timestamp
        self.nonce = _nonce
        self.prev_hash = _prev_hash
        self.txs = _txs

    def __str__(self) -> str:
        return f"Block {self.number}, Timestamp: {self.timestamp}, Nonce: {self.nonce}, PrevHash: {self.prev_hash[:5]}...{self.prev_hash[-3:]}, {len(self.txs)} txs."

    def get_block_hash(self) -> str:
        if self.nonce == -1:  # block was quick synced and is not full:
            return (
                self.prev_hash
            )  # prev_hash here is actually the block's hash, as synced.
        else:
            txs_str = "\n".join([tx.get_tx_hash() for tx in self.txs])
            return hashlib.sha256(
                f"Block {self.number}, Timestamp: {self.timestamp}, Nonce: {self.nonce}, PrevHash: {self.prev_hash}, Tx Hashes: {txs_str}".encode()
            ).hexdigest()

    # Will try to find a nonce such that the block hash < {target}.
    def mine_nonce(self, target: int, node: Node):
        i = 0
        print(f"Looking for nonce such that hash < {target}")
        while not node.block_found_by_peer:
            self.nonce = i
            self.timestamp = time()
            h = self.get_block_hash()
            if int(h, 16) < target:
                print(f"Found nonce {i} that makes the hash < {target}:")
                print(h)
                break
            else:
                i += 1
