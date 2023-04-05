from transaction.transaction import Transaction
from p2pnetwork.node import Node as p2pNode
from hexbytes import HexBytes

# p2pNode is the Node implementation as provided by the p2pnetwork package.
# We have to extend it to do blockchain stuff.


class Node(p2pNode):
    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(Node, self).__init__(host, port, id, callback, max_connections)
        self.block_found_by_peer = False

    def outbound_node_connected(self, connected_node):
        print(f"outbound_node_connected: {connected_node.port}")

    def inbound_node_connected(self, connected_node):
        print(f"inbound_node_connected: {connected_node.port}")
        print(f"sending blockchain state to: {connected_node.port}")
        self.send_to_nodes({"state": self.blockchain.save_state()})

    def inbound_node_disconnected(self, connected_node):
        print(f"inbound_node_disconnected: {connected_node.port}")

    def outbound_node_disconnected(self, connected_node):
        print(f"outbound_node_disconnected: {connected_node.port}")

    def node_message(self, connected_node, data):
        # print(f"node_message from {connected_node.port}" + ": " + str(data))
        print(f"node_message from {connected_node.port}.")
        # self.block_found_by_peer = True
        if "state" in data and not self.blockchain.synced:  # Initial sync.
            print(f"Got initial blockchain state from {connected_node.port}")
            self.blockchain.load_state(data["state"])
            self.blockchain.synced = True
        elif "new_block" in data:  # Someone else found a block.
            self.blockchain.new_blocks.append(data["new_block"])
            print(f"{connected_node.port} found a block: {data['new_block']}")
            self.block_found_by_peer = True
        elif "new_tx" in data:
            print(f"{connected_node.port} sent a tx: {data['new_tx']}")
            tx = Transaction(
                _fr="",
                _to="",
                _amount="",
                _nonce="",
                _signature="",
                _data="",
                _gas_price="",
                _tx_dict=data["new_tx"],
            )
            self.blockchain.pending_txs.append(tx)
        else:
            print(f"received unexpected message. {data}")
            exit(0)

    def node_disconnect_with_outbound_node(self, connected_node):
        print(
            f"node wants to disconnect with other outbound node: {connected_node.port}"
        )

    def node_request_to_stop(self):
        print("node is requested to stop!")
