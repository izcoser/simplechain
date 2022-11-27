from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
import copy

# Y(S, T)= S'
# Initial blockchain state: all addresses have 0 coins,
# except address 0 which has `MAX_SUPPLY`.

# Address private keys `pk` are 32 bytes byte string.
# Addresses are SigningKey.from_string(pk, curve=SECP256k1).verifying_key.to_string().
# Addresses can send coins between one another.

MAX_SUPPLY = 1000
ADDR_COUNT = 256


def to_bytes(num: int) -> bytes:
    return (num).to_bytes(16, byteorder="big")


def address(pk: bytes) -> bytes:
    return SigningKey.from_string(pk, curve=SECP256k1).verifying_key.to_string()


class Account:
    "Holds information about an account."

    def __init__(self, _pk: bytes):
        self.pk = _pk
        self.address = address(_pk)


class State:
    "Holds the state of the blockchain."

    def __init__(self):
        self.balances = {bytes(str(i).zfill(32).encode()): 0 for i in range(ADDR_COUNT)}
        self.balances[bytes(str(0).zfill(32).encode())] = MAX_SUPPLY
        self.nonces = {bytes(str(i).zfill(32).encode()): 0 for i in range(ADDR_COUNT)}


class Transaction:
    "Represents a transaction."

    def __init__(
        self, _fr: bytes, _to: bytes, _amount: int, _nonce: int, _signature: bytes
    ):
        self.fr = _fr
        self.to = _to
        self.amount = _amount
        self.nonce = _nonce
        self.signature = _signature

    def verify_signature(self):
        try:
            vk = VerifyingKey.from_string(self.fr, SECP256k1)
            message = self.fr + self.to + to_bytes(self.amount) + to_bytes(self.nonce)
            vk.verify(self.signature, message)
            return True
        except BadSignatureError:
            return False


def create_transaction(pk: bytes, to: bytes, amount: int, nonce: int) -> Transaction:
    fr = address(pk)
    message = fr + to + to_bytes(amount) + to_bytes(nonce)
    signature = SigningKey.from_string(pk, SECP256k1).sign(message)
    return Transaction(fr, to, amount, nonce, signature)


def mine_block(state: State, transactions: list[Transaction]):
    for t in transactions:
        if (
            t.amount <= state.balances[t.fr]
            and t.verify_signature()
            and t.nonce > state.nonces[t.fr]
        ):
            state.balances[t.fr] -= t.amount
            state.balances[t.to] += t.amount
            state.nonces[t.fr] += 1


def test_signatures():
    pk = bytes(str(0).zfill(32).encode())
    to = address(bytes(str(1).zfill(32).encode()))
    tx = create_transaction(pk, to, 100, 1)
    tx_bad = copy.deepcopy(tx)
    tx_bad.signature += to_bytes(1)

    for t in [tx, tx_bad]:
        if t.verify_signature():
            print("Verified.")
        else:
            print("Bad sig.")


if __name__ == "__main__":
    test_signatures()
