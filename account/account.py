from transaction.transaction import Transaction
from eth_account import Account as web3_account  # from web3py dependency.
from eth_account.messages import encode_defunct
import json
import hashlib

ADDR_COUNT = 3
ZERO_ADDRESS = "0x" + "0" * 40


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
        self, to: str, amount: float, nonce: int, data: dict = {}, gas_price: float = 1
    ) -> (Transaction, str):
        message = encode_defunct(
            text=f"{self.address}{to}({amount})({nonce})({gas_price})({json.dumps(data)})"
        )
        signature = (
            web3_account.from_key(self.private_key).sign_message(message).signature
        )
        return (
            Transaction(
                _fr=self.address,
                _to=to,
                _amount=amount,
                _nonce=nonce,
                _signature=signature,
                _data=data,
                _gas_price=gas_price,
            ),
            "0x" + hashlib.sha256((self.address + str(nonce)).encode()).hexdigest()[:40]
            if to == ZERO_ADDRESS and data != {}
            else "",
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


def generate_accounts() -> list[Account]:
    return [
        Account(_private_key="0x" + str(i + 1).zfill(64)) for i in range(ADDR_COUNT)
    ] + [Account(_address=ZERO_ADDRESS)]
