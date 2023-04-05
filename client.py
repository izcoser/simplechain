from time import time, sleep
import hashlib
import os
import sys
from account.account import Account, ZERO_ADDRESS
from transaction.transaction import Transaction
from block.block import Block
from blockchain.blockchain import Blockchain
from node.node import Node


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
    to_execute = acct.code + f"\n{call}"
    acct.storage["MSGSENDER"] = sender
    keys_before = [k for k in acct.storage]
    exec(to_execute, acct.storage)
    acct.storage = {k: acct.storage[k] for k in keys_before if k != "MSGSENDER"}


def read_contract(accounts: list[Account], address: str, variable: str = ""):
    acct = get_account(accounts, address)
    if variable == "":
        print(acct.storage)
    elif variable in acct.storage:
        print(acct.storage[variable])
    else:
        print(f"Variable {variable} not found in contract {address}")


def get_account(accounts: list[Account], address: str) -> Account:
    for a in accounts:
        if a.address == address:
            return a
    raise AccountNotFound()


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


def get_node_port(args: list[str]) -> int:
    for a in args:
        if a.startswith("--port="):
            return int(a.replace("--port=", ""))
    return -1


def get_peers_ports(args: list[str]) -> list[int]:
    for a in args:
        if a.startswith("--peers="):
            return [int(i) for i in a.replace("--peers=", "").split(",")]
    return []


LOCALHOST = "127.0.0.1"

if __name__ == "__main__":
    node = None
    peers = []
    mine = "--mine" in sys.argv
    if "--networked" in sys.argv:
        node_port = get_node_port(sys.argv)
        peers = get_peers_ports(sys.argv)
        print(f"Creating node on port {node_port} and peers = {peers}")
        node = Node(LOCALHOST, node_port)
        node.start()
        for p in peers:
            node.connect_with_node(LOCALHOST, p)

    if peers == []:
        # No peers. Start a new blockchain from scratch.
        blockchain = Blockchain(
            _difficulty=1,
            _target=(2**256) - 1,
            _expected_block_time=10,
            _recalculate_every_x_blocks=10,
            _xth_last_block_time=0,  # init
            _blocks=[],
            _accounts=[],
        )

        node.blockchain = blockchain

    else:
        print("Peer list detected. Will sync chain.")
        blockchain = Blockchain(
            _difficulty=1,
            _target=(2**256) - 1,
            _expected_block_time=10,
            _recalculate_every_x_blocks=10,
            _xth_last_block_time=time(),  # init
            _blocks=[],
            _accounts=[],
        )
        node.blockchain = blockchain
        node.blockchain.synced = False

        # Wait for a peer to send the blockchain state.
        while not node.blockchain.synced:
            print("Waiting to sync.")
            sleep(1)

        print("Blockchain synced.")

    if mine:
        while True:
            block = Block(
                _number=node.blockchain.blocks[-1].number + 1,
                _timestamp=0,
                _nonce=0,
                _prev_hash=node.blockchain.blocks[-1].get_block_hash(),
                _txs=node.blockchain.pending_txs,
            )

            block.mine_nonce(node.blockchain.target, node)

            if node.block_found_by_peer:
                # new_block is stored as JSON in call back.
                node.blockchain.append_new_blocks()
                node.block_found_by_peer = False
            else:
                node.blockchain.execute_block(block)
                node.blockchain.add_block(block)
                print("broadcasting block to peers: ", block.to_dict())
                node.send_to_nodes({"new_block": block.to_dict()})

            prev_hash = node.blockchain.blocks[-1].get_block_hash()

            # processed_txs = block.to_dict()['txs']
            # node.blockchain.pending_txs = [t for t in node.blockchain.pending_txs if t.__dict__ not in processed_txs]
            node.blockchain.pending_txs = []

    else:
        # a = node.blockchain.accounts[0]
        # b = node.blockchain.accounts[1]
        # nonce = 0
        while True:
            # val = int(
            #    input(
            #        f"Enter a transaction value from account 0 {a.short_address()} to account 1: "
            #    )
            # )
            # (tx, _) = a.send_transaction(to=b.address, amount=val, nonce=nonce)
            # print(tx.__dict__)
            # node.send_to_nodes({"new_tx": tx.__dict__})
            # nonce += 1
            print(
                f"Watching blockchain. Current block: {node.blockchain.blocks[-1].number}"
            )
            node.blockchain.append_new_blocks()
            sleep(4)

    # blockchain.save_state()


"""    a = accounts[0]
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
"""


"""
    else:
        blockchain = Blockchain(
            _difficulty=1,
            _target=(2**256) - 1,
            _expected_block_time=2,
            _recalculate_every_x_blocks=10,
            _xth_last_block_time=0,  # init
            _blocks=[],
            _accounts=[],
        )
        node.blockchain = blockchain
        while len(node.blockchain.blocks) == 0: # waiting to receive state from peers.
            sleep(1)
        
        accounts = node.blockchain.accounts
"""
