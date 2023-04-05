import sys
from blockchain.blockchain import Blockchain
from node.node import Node
from time import time, sleep

LOCALHOST = "127.0.0.1"
# Usage: python send.py --from=0 --to=1 --val=10


def get_arg(args: list[str], arg: str) -> int:
    for a in args:
        if a.startswith(f"--{arg}"):
            return int(a.replace(f"--{arg}=", ""))


if __name__ == "__main__":
    peers = [10000]
    node_port = 10005
    node = Node(LOCALHOST, node_port)

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

    node.start()
    for p in peers:
        node.connect_with_node(LOCALHOST, p)

    # Wait for a peer to send the blockchain state.
    while not node.blockchain.synced:
        print("Waiting to sync.")
        sleep(1)

    print("Blockchain synced.")

    fr = get_arg(sys.argv, "from")
    to = get_arg(sys.argv, "to")
    val = get_arg(sys.argv, "val")
    a = node.blockchain.accounts[fr]
    b = node.blockchain.accounts[to]

    (tx, _) = a.send_transaction(to=b.address, amount=val, nonce=a.nonce)
    node.send_to_nodes({"new_tx": tx.__dict__})
    print(f"Sent tx: {tx}")

    sleep(3)
    node.stop()
