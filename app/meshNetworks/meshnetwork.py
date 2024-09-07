import json
import os
import random
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom exception for empty connections
class EmptyConnectionsError(Exception):
    pass

class Node:
    def __init__(self, node_id, storage_path):
        self.node_id = node_id
        self.connections = []
        self.messages = []
        self.storage_path = storage_path
        self.load_state()

    def add_connection(self, node):
        if node not in self.connections:
            self.connections.append(node)
            self.save_state()

    def send_message(self, message, target_id, ttl=10):
        if ttl <= 0:
            return  # Message expired

        if self.node_id == target_id:
            self.messages.append(message)
            self.save_state()
            print(f"Node {self.node_id} received: {message}")
        else:
            next_node = random.choice(self.connections)
            print(f"Node {self.node_id} forwarding to {next_node.node_id}, TTL: {ttl}")
            # TTL stands for "Time To Live", which is a counter that decreases with each hop to prevent infinite message loops
            next_node.send_message(message, target_id, ttl - 1)

    def save_state(self):
        state = {
            "node_id": self.node_id,
            "connections": [node.node_id for node in self.connections],
            "messages": self.messages
        }
        with open(os.path.join(self.storage_path, f"node_{self.node_id}.json"), "w") as f:
            json.dump(state, f)

    def load_state(self):
        try:
            with open(os.path.join(self.storage_path, f"node_{self.node_id}.json"), "r") as f:
                state = json.load(f)
                self.messages = state["messages"]
        except FileNotFoundError:
            pass  # No saved state yet

class DisasterMeshNetwork:
    def __init__(self, storage_path):
        self.nodes = {}
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def add_node(self, node_id):
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, self.storage_path)

    def connect_nodes(self, node_id1, node_id2):
        node1 = self.nodes[node_id1]
        node2 = self.nodes[node_id2]
        node1.add_connection(node2)

    def send_message(self, from_id, to_id, message):
        
        if from_id in self.nodes:
            self.nodes[from_id].send_message(message, to_id)

    def broadcast_emergency(self, from_id, message):
        for node in self.nodes.values():
            if node.node_id != from_id:
                self.send_message(from_id, node.node_id, f"EMERGENCY: {message}")

# Example usage
if __name__ == "__main__":
    network = DisasterMeshNetwork("disaster_mesh_data")

    # Add nodes (simulating different devices)
    for i in range(5):
        network.add_node(i)

    # Connect nodes (creating a simple mesh)
    network.connect_nodes(0, 1)
    network.connect_nodes(0, 2)
    network.connect_nodes(1, 3)
    network.connect_nodes(2, 3)
    network.connect_nodes(2, 4)
    network.connect_nodes(3, 4)

    # Simulate normal message
    network.send_message(0, 4, "Hello, Node 4!")

    # Simulate emergency broadcast
    # network.broadcast_emergency(2, "Evacuation required in sector 7")

    # Simulate node failure and message rerouting
    del network.nodes[1]
    network.send_message(0, 3, "Node 1 is down, but this message should still get through")
