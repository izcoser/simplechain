import os
from block.block import Block
from account.account import Account, generate_accounts
from time import time
import json


class Blockchain:
    def __init__(
        self,
        _difficulty: int,
        _target: int,
        _expected_block_time: float,
        _recalculate_every_x_blocks: int,
        _xth_last_block_time: float,  # for quick syncing
        _blocks: list[Block],
        _accounts: list[Account],
    ):
        self.difficulty = _difficulty
        self.target = _target
        self.expected_block_time = _expected_block_time
        self.recalculate_every_x_blocks = _recalculate_every_x_blocks
        self.xth_last_block_time = _xth_last_block_time
        self.blocks = _blocks
        self.genesis_time = time()
        self.accounts = _accounts

    def add_block(self, _block: Block):
        assert int(_block.get_block_hash(), 16) < self.target
        if len(self.blocks) > 0:
            assert _block.prev_hash == self.blocks[-1].get_block_hash()
            assert _block.number == self.blocks[-1].number + 1
            assert _block.timestamp >= self.blocks[-1].timestamp

        block_time = (
            _block.timestamp - self.blocks[-1].timestamp
            if len(self.blocks) > 0
            else _block.timestamp - self.genesis_time
        )
        print(
            f"Block {_block.number} added. Hash: ...{_block.get_block_hash()[-5:]}. Block time: {block_time}"
        )
        self.blocks.append(_block)

        if (
            self.blocks[-1].number % self.recalculate_every_x_blocks == 0
            and self.blocks[-1].number > 0
        ):
            print("Recalculating difficulty.")
            self.recalculate_difficulty()
            self.recalculate_target()

    def recalculate_difficulty(self):
        last_block_time = self.blocks[-1].timestamp
        xth_last_block_time = (
            self.blocks[-self.recalculate_every_x_blocks].timestamp
            if len(self.blocks) >= self.recalculate_every_x_blocks
            else self.xth_last_block_time
        )
        self.difficulty *= (
            self.recalculate_every_x_blocks * self.expected_block_time
        ) / (last_block_time - xth_last_block_time)

    def recalculate_target(self):
        self.target = ((2**256) - 1) / self.difficulty

    def save_state(self, write_file=False) -> dict:
        state = {
            "difficulty": self.difficulty,
            "target": self.target,
            "recalculate_every_x_blocks": self.recalculate_every_x_blocks,
            "xth_last_block_time": self.xth_last_block_time
            or (self.blocks[-self.recalculate_every_x_blocks].timestamp if len(self.blocks) >= self.recalculate_every_x_blocks else self.genesis_time),
            "last_block_time": self.blocks[-1].timestamp,
            "last_block_number": self.blocks[-1].number,
            "last_block_hash": self.blocks[-1].get_block_hash(),
            "genesis_time": self.genesis_time,
            "expected_block_time": self.expected_block_time,
            "accounts": [a.serialize() for a in self.accounts],
        }
        if write_file:
            with open("state.json", "w") as s:
                s.write(json.dumps(state))
        return state

    def load_state(self, state_dict={}):
        if os.path.isfile("state.json") or state_dict != {}:
            if os.path.isfile("state.json"):
                with open("state.json", "r") as s:
                    state = json.load(s)
            else:
                state = state_dict

            self.difficulty = state["difficulty"]
            self.target = state["target"]
            self.recalculate_every_x_blocks = state["recalculate_every_x_blocks"]
            self.xth_last_block_time = state["xth_last_block_time"]
            self.genesis_time = state["genesis_time"]
            self.expected_block_time = state["expected_block_time"]
            b = Block(
                _number=state["last_block_number"],
                _timestamp=state["last_block_time"],
                _nonce=-1,
                _prev_hash=state["last_block_hash"],
                _txs=[],
            )
            self.blocks.append(b)
            self.accounts = [
                Account(
                    _private_key=a["private_key"],
                    _nonce=a["nonce"],
                    _balance=a["balance"],
                    _code=a["code"],
                    _storage=a["storage"],
                )
                for a in [json.loads(s) for s in state["accounts"]]
            ]
        else:
            b = Block(
                _number=0,
                _timestamp=self.genesis_time,
                _nonce=-1,
                _prev_hash="0" * 64,
                _txs=[],
            )
            self.blocks.append(b)
            self.accounts = generate_accounts()
