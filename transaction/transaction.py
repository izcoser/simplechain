from eth_account import Account as web3_account  # from web3py dependency.
from eth_account.messages import encode_defunct
import hashlib
import json
from hexbytes import HexBytes


class BadSignatureException(Exception):
    "Raised when a transaction is not signed by the from address"
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
        **kwargs,
    ):
        self.fr = _fr
        self.to = _to
        self.amount = _amount
        self.nonce = _nonce
        self.signature = _signature
        self.data = _data
        self.gas_price = _gas_price

        if "_tx_dict" in kwargs:
            self.from_dict(kwargs["_tx_dict"])

    def verify_signature(self) -> bool:
        try:
            message = encode_defunct(
                text=f"{self.fr}{self.to}({self.amount})({self.nonce})({self.gas_price})({json.dumps(self.data)})"
            )
            if self.fr != web3_account.recover_message(
                message, signature=HexBytes(self.signature)
            ):
                raise BadSignatureException
            return True
        except BadSignatureException:
            return False

    def get_tx_hash(self) -> str:
        return hashlib.sha256(
            f"{self.fr}{self.to}({self.amount})({self.nonce})({self.gas_price})({self.data})".encode()
        ).hexdigest()

    def to_dict(self) -> dict:
        return self.__dict__

    def from_dict(self, tx: dict):
        self.fr = tx["fr"]
        self.to = tx["to"]
        self.amount = tx["amount"]
        self.nonce = tx["nonce"]
        self.signature = tx["signature"]
        self.data = tx["data"]
        self.gas_price = tx["gas_price"]
