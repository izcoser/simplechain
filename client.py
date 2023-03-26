import copy
from eth_account import Account as web3_account
from eth_account.messages import encode_defunct
from hexbytes import HexBytes
from time import time
import hashlib
import json
import os

# Y(S, T)= S'

MAX_SUPPLY = 1000
ADDR_COUNT = 256
ZERO_ADDRESS = "0x" + "0" * 40


class BadSignatureException(Exception):
    "Raised when a transaction is not signed by the from address"
    pass


class AccountNotFound(Exception):
    "Raised when an account is not found on the list of accounts."
    pass


class Transaction:
    "Represents a transaction."

    def __init__(
        self,
        _fr: str,
        _to: str,
        _amount: float,
        _nonce: int,
        _signature: str,
        _data: str,
        _gas_price: float,
    ):
        self.fr = _fr
        self.to = _to
        self.amount = _amount
        self.nonce = _nonce
        self.signature = _signature
        self.data = _data
        self.gas_price = _gas_price

    def verify_signature(self) -> bool:
        try:
            message = encode_defunct(
                text=f"{self.fr}{self.to}({self.amount})({self.nonce})({self.gas_price})({self.data})"
            )
            if self.fr != web3_account.recover_message(
                message, signature=self.signature
            ):
                raise BadSignatureException
            return True
        except BadSignatureException:
            return False

    def get_tx_hash(self) -> str:
        return hashlib.sha256(
            f"{self.fr}{self.to}({self.amount})({self.nonce})({self.gas_price})({self.data})".encode()
        ).hexdigest()


class Account:
    "Holds information about an account."
    """ Address: 64 hexadecimal characters;
        Private Key;
        Nonce: a transaction counter starting at 0;
        Balance;
        Contract Code;
        Storage (empty by default). 

        For now, I'm going to use the web3 library to go from private key to address, because this process seems quite complex
        to do with the ecdsa library. But for a better understanding, this should be done with ecdsa.
        In that case, I would go from private key -> public key -> address.
    """

    def __init__(
        self,
        _private_key: str = "",  # if supplied, account becomes an EOA. Else it becomes a contract.
        _address: str = "",  # derived from private key if EOA. Set explicitly if contract.
        _nonce: int = 0,
        _balance: float = 0,
        _code: str = "",
        _storage: dict = {},
    ):
        assert len(_private_key) in [66, 0]
        self.private_key = _private_key
        self.address = (
            _address
            if _private_key == ""
            else web3_account.from_key(_private_key).address
        )
        self.nonce = _nonce
        self.balance = _balance
        self.code = _code
        self.storage = _storage

    def set_balance(self, _balance):
        self.balance = _balance

    def send_transaction(
        self, to: str, amount: float, data: dict = {}, gas_price: float = 1
    ) -> Transaction:
        message = encode_defunct(
            text=f"{self.address}{to}({amount})({self.nonce})({gas_price})({json.dumps(data)})"
        )
        signature = (
            web3_account.from_key(self.private_key).sign_message(message).signature
        )
        return Transaction(
            _fr=self.address,
            _to=to,
            _amount=amount,
            _nonce=self.nonce,
            _signature=signature,
            _data=data,
            _gas_price=gas_price,
        )

    def __str__(self) -> str:
        return f"Addr: {self.address[:5]}...{self.address[-3:]}, Balance: {self.balance}, Nonce: {self.nonce}, PK: {self.private_key[:5]}...{self.private_key[-3:]}"

    def serialize(self) -> str:
        account_json = {
            "private_key": self.private_key,
            "address": self.address,
            "nonce": self.nonce,
            "balance": self.balance,
            "code": self.code,
            "storage": self.storage,
        }
        return json.dumps(account_json)


def get_account(accounts: list[Account], address: str) -> Account:
    for a in accounts:
        if a.address == address:
            return a
    raise AccountNotFound()


def generate_accounts() -> list[Account]:
    return [Account(_private_key="0x" + str(i + 1).zfill(64)) for i in range(ADDR_COUNT)] + [Account(_address=ZERO_ADDRESS)]


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
            txs_str = "\n".join([tx.get_tx_hash() for t in self.txs])
            return hashlib.sha256(
                f"Block {self.number}, Timestamp: {self.timestamp}, Nonce: {self.nonce}, PrevHash: {self.prev_hash}, Tx Hashes: {txs_str}".encode()
            ).hexdigest()

    # Will try to find a nonce such that the block hash ends with {difficulty} zeros.
    def mine_nonce(self, target):
        i = 0
        print(f"Looking for nonce such that hash < {target}")
        while True:
            self.nonce = i
            self.timestamp = time()
            h = self.get_block_hash()
            if int(h, 16) < target:
                print(f"Found nonce {i} that makes the hash < {target}:")
                print(h)
                break
            else:
                i += 1


def execute_block(accounts: list[Account], block: Block):
    for t in block.txs:
        fr_account = get_account(accounts, t.fr)
        to_account = get_account(accounts, t.to)
        if (
            t.amount <= fr_account.balance
            and t.verify_signature()
            and t.nonce == fr_account.nonce
        ):
            fr_account.balance -= t.amount
            to_account.balance += t.amount
            fr_account.nonce += 1

        if t.to == ZERO_ADDRESS and t.data != {}:  # contract creation
            deploy_address = "0x" + hashlib.sha256((t.fr + str(t.nonce)).encode()).hexdigest()[:40]
            print(f"Creating contract at address {deploy_address}")
            fr_account = get_account(accounts, t.fr)
            to_account = get_account(accounts, t.to)
            code = t.data["code"]
            storage = t.data["variables"]
            accounts.append(
                Account(_address=deploy_address, _code=code, _storage=storage)
            )

        elif to_account.code != "" and t.data != {}:  # contract call
            to_execute = to_account.code + f'\n{t.data["call"]}'
            keys_before = [k for k in to_account.storage]
            print(f"Executing code:\n{to_execute}")
            print(f"Storage before: {to_account.storage}")
            exec(to_execute, to_account.storage)
            to_account.storage = {k: to_account.storage[k] for k in keys_before}
            print(f"Storage after: {to_account.storage}")
            # will execute for example:


"""
    def a(x):
        b += x
    
    a(5)
"""
"""
data = {
    "variables": {"a": 0, "b": 0},
    "code": 'all functions here in plain text..'
}
When calling, the code will be ran with exec(code + \ny(k))
"""


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

    def save_state(self):
        state = {
            "difficulty": self.difficulty,
            "target": self.target,
            "recalculate_every_x_blocks": self.recalculate_every_x_blocks,
            "xth_last_block_time": self.xth_last_block_time
            or self.blocks[-self.recalculate_every_x_blocks].timestamp,
            "last_block_time": self.blocks[-1].timestamp,
            "last_block_number": self.blocks[-1].number,
            "last_block_hash": self.blocks[-1].get_block_hash(),
            "genesis_time": self.genesis_time,
            "expected_block_time": self.expected_block_time,
            "accounts": [a.serialize() for a in self.accounts],
        }
        with open("state.json", "w") as s:
            s.write(json.dumps(state))

    def load_state(self):
        if os.path.isfile("state.json"):
            with open("state.json", "r") as s:
                state = json.load(s)
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


if __name__ == "__main__":
    blockchain = Blockchain(
        _difficulty=1,
        _target=(2**256) - 1,
        _expected_block_time=2,
        _recalculate_every_x_blocks=10,
        _xth_last_block_time=0,  # init
        _blocks=[],
        _accounts=[],
    )

    blockchain.load_state()
    accounts = blockchain.accounts
    a = accounts[0]
    data = {"code": "def set_a(n):\n\tglobal a; a = increment(n)\ndef increment(x):\n\t return x + 1", "variables": {"a": 0}}

    data2 = {"call": "set_a(5)"}
    tx = a.send_transaction(
        to=ZERO_ADDRESS, amount=0, data=data
    )
    deploy_address = "0x" + hashlib.sha256((a.address + str(a.nonce)).encode()).hexdigest()[:40]
    tx2 = a.send_transaction(to=deploy_address, amount=0, data=data2)
    block = Block(
        _number=blockchain.blocks[-1].number + 1,
        _timestamp=0,
        _nonce=0,
        _prev_hash=blockchain.blocks[-1].get_block_hash(),
        _txs=[tx, tx2],
    )

    execute_block(accounts, block)
    block.mine_nonce(blockchain.target)
    blockchain.add_block(block)

    """for i in range(30):
        block = Block(
            _number=blockchain.blocks[-1].number + 1,
            _timestamp=0,
            _nonce=0,
            _prev_hash=blockchain.blocks[-1].get_block_hash(),
            _txs=[],
        )
        execute_block(accounts, block)
        block.mine_nonce(blockchain.target)
        blockchain.add_block(block)
        prev_hash = blockchain.blocks[-1].get_block_hash()
    """
    # blockchain.save_state()
