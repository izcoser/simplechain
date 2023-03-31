from p2pnetwork.node import Node as p2pNode

# p2pNode is the Node implementation as provided by the p2pnetwork package.
# We have to extend it to do blockchain stuff.

class Node(p2pNode):
    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(Node, self).__init__(host, port, id, callback, max_connections)
        self.block_found_by_peer = False
        self.blockchain = ""

    def outbound_node_connected(self, connected_node):
        print(f"outbound_node_connected: {connected_node.port}")
        
    def inbound_node_connected(self, connected_node):
        print(f"inbound_node_connected: {connected_node.port}")
        print(f"sending blockchain state to: {connected_node.port}")
        self.send_to_nodes({"message": self.blockchain.save_state()})

    def inbound_node_disconnected(self, connected_node):
        print(f"inbound_node_disconnected: {connected_node.port}")

    def outbound_node_disconnected(self, connected_node):
        print(f"outbound_node_disconnected: {connected_node.port}")

    def node_message(self, connected_node, data):
        print(f"node_message from {connected_node.port}" + ": " + str(data))
        #self.block_found_by_peer = True
        self.blockchain.load_state(data['message'])
        
    def node_disconnect_with_outbound_node(self, connected_node):
        print(f"node wants to disconnect with other outbound node: {connected_node.port}")
        
    def node_request_to_stop(self):
        print("node is requested to stop!")