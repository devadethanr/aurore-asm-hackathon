import hashlib
import json
import time

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class BlockchainMeshNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.chain = [self.create_genesis_block()]
        self.pending_messages = []

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_message(self, sender, recipient, message):
        self.pending_messages.append({
            "sender": sender,
            "recipient": recipient,
            "message": message,
            "timestamp": time.time()
        })

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
        self.pending_messages = []
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

# Example usage
node1 = BlockchainMeshNode(1)
node1.add_message("Node1", "Node2", "Hello from blockchain mesh!")
node1.mine_block()

print(f"Blockchain valid: {node1.validate_chain()}")
print(f"Latest block: {json.dumps(node1.get_latest_block().__dict__, indent=2)}")