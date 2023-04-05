import os
from block.block import Block
from account.account import Account, generate_accounts, ZERO_ADDRESS
from time import time
import json


def get_account(accounts: list[Account], address: str) -> Account:
    for a in accounts:
        if a.address == address:
            return a
    raise AccountNotFound()


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
        self.new_blocks = []
        self.pending_txs = []
        self.load_state()

    def add_block(self, _block: Block):
        assert int(_block.get_block_hash(), 16) < self.target
        if len(self.blocks) > 0:
            assert _block.number == self.blocks[-1].number + 1
            assert _block.prev_hash == self.blocks[-1].get_block_hash()
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

        if _block.number % self.recalculate_every_x_blocks == 0 and _block.number > 0:
            print("Recalculating difficulty.")
            self.recalculate_difficulty()
            self.recalculate_target()
            self.xth_last_block_time = _block.timestamp

    def recalculate_difficulty(self):
        last_block_time = self.blocks[-1].timestamp
        self.difficulty *= (
            self.recalculate_every_x_blocks * self.expected_block_time
        ) / (last_block_time - self.xth_last_block_time)

    def recalculate_target(self):
        self.target = ((2**256) - 1) / self.difficulty

    def save_state(self, write_file=False) -> dict:
        state = {
            "difficulty": self.difficulty,
            "target": self.target,
            "recalculate_every_x_blocks": self.recalculate_every_x_blocks,
            "xth_last_block_time": self.xth_last_block_time,
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

    # If a state is given in `state.json` or passed as state_dict,
    # the blockchain syncs to that state by setting all accounts values.
    # Else, it will just generate accounts empty accounts.
    # In both cases, an empty block is added so add_block() can
    # check information from the previous block.

    def load_state(self, state_dict: dict = {}):
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

    def execute_block(self, block: Block):
        accounts = self.accounts
        for t in block.txs:
            fr_account = get_account(accounts, t.fr)
            to_account = get_account(accounts, t.to)

            if t.amount > fr_account.balance:
                print("Can't process transaction, amount more than balance.")
                # Raise InsufficientBalance()
                continue

            if not t.verify_signature():
                print("Can't verify signature.")
                continue

            if t.nonce != fr_account.nonce:
                print(
                    f"Transaction nonce ({t.nonce}) differs from account nonce ({fr_account.nonce}). "
                )
                continue

            fr_account.balance -= t.amount
            to_account.balance += t.amount
            fr_account.nonce += 1

            if t.to == ZERO_ADDRESS and t.data != {}:  # contract creation
                deploy_address = (
                    "0x"
                    + hashlib.sha256((t.fr + str(t.nonce)).encode()).hexdigest()[:40]
                )
                deploy_contract(
                    t.fr, t.data["code"], t.data["variables"], deploy_address, accounts
                )

            elif to_account.code != "" and t.data != {}:  # contract call
                call_contract(accounts, t.fr, t.to, t.data["call"])

    def append_new_blocks(self):
        if self.new_blocks:
            print("Appending blocks found by others.")
            for block_dict in self.new_blocks:
                b = Block(_block_dict=block_dict)
                self.execute_block(b)
                self.add_block(b)
            self.new_blocks = []
        else:
            print("No blocks to add.")
