import hashlib
import json
import time
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index, timestamp, data, previous_hash, _id=None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
        self._id = _id

    def calculate_hash(self):
        block_string = json.dumps({k: v for k, v in self.__dict__.items() if k != '_id'}, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "_id": self._id,
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class BlockchainMeshNode:
    def __init__(self, node_id, mongo_uri):
        self.node_id = node_id
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client.blockchain_mesh_network
            self.chain = self.load_chain()
            if not self.chain:
                self.chain = [self.create_genesis_block()]
                self.save_block(self.chain[0])
            self.pending_messages = self.load_pending_messages()
        except Exception as e:
            logger.error(f"Failed to initialize BlockchainMeshNode: {str(e)}")
            raise

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_message(self, sender, recipient, message):
        new_message = {
            "sender": sender,
            "recipient": recipient,
            "message": message,
            "timestamp": time.time()
        }
        self.pending_messages.append(new_message)
        inserted_message = self.db.pending_messages.insert_one(new_message)
        new_message['_id'] = str(inserted_message.inserted_id)  # Convert ObjectId to string
        logger.info(f"Message added: {new_message}")

    def mine_block(self):
        if not self.pending_messages:
            return False

        new_block = Block(
            len(self.chain),
            time.time(),
            self.pending_messages,
            self.get_latest_block().hash
        )
        self.chain.append(new_block)
        self.save_block(new_block)
        self.clear_pending_messages()
        logger.info(f"New block mined: {new_block.to_dict()}")
        return True

    def validate_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def save_block(self, block):
        result = self.db.blocks.insert_one(block.to_dict())
        block._id = result.inserted_id

    def load_chain(self):
        blocks = list(self.db.blocks.find().sort("index", 1))
        return [Block(index=block['index'], 
                      timestamp=block['timestamp'], 
                      data=block['data'], 
                      previous_hash=block['previous_hash'], 
                      _id=block['_id']) for block in blocks]

    def load_pending_messages(self):
        return list(self.db.pending_messages.find())

    def clear_pending_messages(self):
        self.pending_messages = []
        self.db.pending_messages.delete_many({})

    def close_connection(self):
        self.client.close()

# Example usage
if __name__ == "__main__":
    # Replace with your actual MongoDB connection string
    mongo_uri = "mongodb://localhost:27017/blockchain_mesh_network"
    try:
        node1 = BlockchainMeshNode(1, mongo_uri)

        node1.add_message("Node1", "Node2", "Hello from blockchain mesh!")
        node1.mine_block()

        print(f"Blockchain valid: {node1.validate_chain()}")
        print(f"Latest block: {json.dumps(node1.get_latest_block().to_dict(), indent=2, default=str)}")

        node1.close_connection()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")