from eth_account import Account as web3_account  # from web3py dependency.
from eth_account.messages import encode_defunct
import hashlib
import json


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
                text=f"{self.fr}{self.to}({self.amount})({self.nonce})({self.gas_price})({json.dumps(self.data)})"
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
