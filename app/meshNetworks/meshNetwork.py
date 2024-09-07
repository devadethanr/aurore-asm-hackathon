import random
import time
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom exception for empty connections
class EmptyConnectionsError(Exception):
    pass

class Node:
    def __init__(self, node_id, db):
        self.node_id = node_id
        self.db = db
        self.connections = []
        self.load_state()

    def add_connection(self, node):
        if node not in self.connections:
            self.connections.append(node)
            self.save_state()

    def send_message(self, message, target_id, ttl=10):
        if ttl <= 0:
            return  # Message expired

        if self.node_id == target_id:
            self.db.messages.insert_one({"node_id": self.node_id, "message": message})
            logger.info(f"Node {self.node_id} received: {message}")
        else:
            next_node = random.choice(self.connections)
            logger.info(f"Node {self.node_id} forwarding to {next_node.node_id}, TTL: {ttl}")
            next_node.send_message(message, target_id, ttl - 1)

    def save_state(self):
        state = {
            "node_id": self.node_id,
            "connections": [node.node_id for node in self.connections],
        }
        self.db.nodes.update_one({"node_id": self.node_id}, {"$set": state}, upsert=True)

    def load_state(self):
        state = self.db.nodes.find_one({"node_id": self.node_id})
        if state:
            self.connections = [Node(node_id, self.db) for node_id in state.get("connections", [])]

class DisasterMeshNetwork:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.rescuenet
        self.nodes = {}

    def add_node(self, node_id):
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, self.db)

    def connect_nodes(self, node_id1, node_id2):
        node1 = self.nodes[node_id1]
        node2 = self.nodes[node_id2]
        node1.add_connection(node2)
        node2.add_connection(node1)

    def send_message(self, from_id, to_id, message):
        if from_id in self.nodes:
            self.nodes[from_id].send_message(message, to_id)

    def broadcast_emergency(self, from_id, message):
        for node in self.nodes.values():
            if node.node_id != from_id:
                self.send_message(from_id, node.node_id, f"EMERGENCY: {message}")

# Example usage
if __name__ == "__main__":
    # Replace with your actual MongoDB connection string
    mongo_uri = "mongodb+srv://admin:admin@cluster0.y9yngcg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    network = DisasterMeshNetwork(mongo_uri)

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
    network.broadcast_emergency(2, "Evacuation required in sector 7")

    # Simulate node failure and message rerouting
    del network.nodes[1]
    network.send_message(0, 3, "Node 1 is down, but this message should still get through")

    # Close the MongoDB connection
    network.client.close()
