# import copy
from eth_account import Account as web3_account

from hexbytes import HexBytes
from time import time
import hashlib

import os

from account.account import Account, ZERO_ADDRESS
from transaction.transaction import Transaction
from block.block import Block
from blockchain.blockchain import Blockchain

# Y(S, T)= S'

MAX_SUPPLY = 1000


class AccountNotFound(Exception):
    "Raised when an account is not found on the list of accounts."
    pass


class InsufficientBalance(Exception):
    "Raised when the sender does not have enough funds for a transaction."
    pass


def deploy_contract(
    sender: str,
    code: str,
    variables: dict,
    deploy_address: str,
    accounts: list[Account],
):
    storage = variables
    storage["MSGSENDER"] = sender
    keys_before = [k for k in storage]
    # run constructor:
    to_execute = code + "\nconstructor()"
    exec(to_execute, storage)
    storage = {k: storage[k] for k in keys_before if k != "MSGSENDER"}
    accounts.append(Account(_address=deploy_address, _code=code, _storage=storage))

def call_contract(accounts: list[Account], sender: str, address: str, call: str):
    acct = get_account(accounts, address)
    to_execute = acct.code + f'\n{call}'
    acct.storage["MSGSENDER"] = sender
    keys_before = [k for k in acct.storage]
    exec(to_execute, acct.storage)
    acct.storage = {
        k: acct.storage[k] for k in keys_before if k != "MSGSENDER"
    }

def read_contract(accounts: list[Account], address: str, variable: str = ""):
    acct = get_account(accounts, address)
    if variable == "":
        print(acct.storage)
    elif variable in acct.storage:
        print(acct.storage[variable])
    else:
        print(f'Variable {variable} not found in contract {address}')


def get_account(accounts: list[Account], address: str) -> Account:
    for a in accounts:
        if a.address == address:
            return a
    raise AccountNotFound()


def execute_block(accounts: list[Account], block: Block):
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
                "0x" + hashlib.sha256((t.fr + str(t.nonce)).encode()).hexdigest()[:40]
            )
            print(f"Creating contract at address {deploy_address}")
            deploy_contract(
                t.fr, t.data["code"], t.data["variables"], deploy_address, accounts
            )

        elif to_account.code != "" and t.data != {}:  # contract call
            call_contract(accounts, t.fr, t.to, t.data["call"])


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
    data = {
        "code": "def constructor():\n\tpass\ndef set_a(n):\n\tglobal a; a = increment(n)\ndef increment(x):\n\t return x + 1",
        "variables": {"a": 0},
    }

    data2 = {"call": "set_a(5)"}
    (tx, deploy_address) = a.send_transaction(
        to=ZERO_ADDRESS, amount=0, nonce=0, data=data
    )
    (tx2, _) = a.send_transaction(to=deploy_address, amount=0, nonce=1, data=data2)

    with open("contracts/ERC-20.py", "r") as e:
        erc20 = e.read()
    data3 = {
        "code": erc20,
        "variables": {
            "ticker": "BTC",
            "name": "Bitcoin",
            "supply": 21_000_000,
            "balances": {},
            "allowances": "",
        },
    }
    (tx3, deploy_address_erc20) = a.send_transaction(
        to=ZERO_ADDRESS, amount=0, nonce=2, data=data3
    )
    data4 = {"call": f"transfer('{accounts[1].address}', 10_000_000)"}

    (tx4, _) = a.send_transaction(
        to=deploy_address_erc20, amount=0, nonce=3, data=data4
    )
    block = Block(
        _number=blockchain.blocks[-1].number + 1,
        _timestamp=0,
        _nonce=0,
        _prev_hash=blockchain.blocks[-1].get_block_hash(),
        _txs=[tx, tx2, tx3, tx4],
    )

    execute_block(accounts, block)
    block.mine_nonce(blockchain.target)
    blockchain.add_block(block)

    read_contract(accounts, deploy_address_erc20, "ticker")
    read_contract(accounts, deploy_address_erc20, "balances")

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
