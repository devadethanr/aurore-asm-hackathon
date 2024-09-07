from flask import Blueprint, jsonify, request, render_template
from app import mongo
import datetime
import hashlib
from app.meshNetworks.meshNetwork import DisasterMeshNetwork
from bson import ObjectId

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        # Here you would typically process the login/signup
        # For now, we'll just print the received data
        print(f"Received: Name - {name}, Phone - {phone}")
        # You might want to add the user to the database here
        return jsonify({'status': 'success', 'message': 'Login/Signup successful'})
    return render_template('index.html')

@main.route('/send_location', methods=['POST'])
def send_location():
    data = request.get_json()
    if not data or 'username' not in data or 'lat' not in data or 'lon' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    print("test for mongo")
    mongo.db.user_locations.update_one(
        {'username': data['username']},
        {"$set": {
            'lat': data['lat'],
            'lon': data['lon'],
            'message': data.get('message', '')
        }},
        upsert=True
    )

    return jsonify({'status': 'Location updated'})

@main.route('/get_locations', methods=['GET'])
def get_locations():
    users = mongo.db.user_locations.find()
    locations = {}
    for user in users:
        locations[user['username']] = {
            'lat': user['lat'],
            'lon': user['lon'],
            'message': user.get('message', '')
        }

    return jsonify(locations)

def get_device_identifier():
    user_agent = request.headers.get('User-Agent')
    accept_language = request.headers.get('Accept-Language')
    ip_address = request.remote_addr
    
    # Combine available information
    device_info = f"{user_agent}|{accept_language}|{ip_address}"
    
    # Create a hash of the device info
    device_hash = hashlib.md5(device_info.encode()).hexdigest()
    
    return device_hash

@main.route('/auth', methods=['POST'])
def auth():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    if not name or not phone:
        return jsonify({'error': 'Invalid data'}), 400

    # Get a unique identifier for the device
    device_id = get_device_identifier()

    user = mongo.db.users.find_one({'phone': phone})
    if user:
        # User exists, update name if different and update device_id
        update_data = {
            '$set': {
                'name': name,
                'device_id': device_id,
                'last_login': datetime.datetime.utcnow()
            }
        }
        mongo.db.users.update_one({'phone': phone}, update_data)
        message = 'Login successful'
    else:
        # New user, create account with device_id
        mongo.db.users.insert_one({
            'name': name,
            'phone': phone,
            'device_id': device_id,
            'created_at': datetime.datetime.utcnow(),
            'last_login': datetime.datetime.utcnow()
        })
        message = 'Signup successful'

    return jsonify({'status': 'success', 'message': message, 'device_id': device_id})

@main.route('/send_emergency_message', methods=['POST'])
def send_emergency_message():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    message = data.get('message')

    if not name or not phone or not message:
        return jsonify({'error': 'Invalid data'}), 400

    # Initialize the DisasterMeshNetwork
    mongo_uri = "mongodb+srv://admin:admin@cluster0.y9yngcg.mongodb.net/rescuenet?retryWrites=true&w=majority&appName=Cluster0"
    network = DisasterMeshNetwork(mongo_uri)

    # Add the user as a node (if not already added)
    network.add_node(phone)

    # Broadcast the emergency message
    network.broadcast_emergency(phone, f"Emergency from {name}: {message}")

    # Save the emergency message to the database
    mongo.db.emergency_messages.insert_one({
        'name': name,
        'phone': phone,
        'message': message,
        'timestamp': datetime.datetime.utcnow()
    })

    return jsonify({'status': 'success', 'message': 'Emergency message sent'})

@main.route('/admin', methods=['GET', 'POST'])
def admin():
    emergency_messages = list(mongo.db.emergency_messages.find())
    return render_template('admin.html', emergency_messages=emergency_messages)

@main.route('/assign_responders', methods=['POST'])
def assign_responders():
    message_id = request.form.get('message_id')
    # Logic to assign first responders (not implemented in this example)
    return jsonify({'status': 'success', 'message': 'First responders assigned'})

@main.route('/broadcast_message', methods=['POST'])
def broadcast_message():
    message_id = request.form.get('message_id')
    # Logic to broadcast message (not implemented in this example)
    return jsonify({'status': 'success', 'message': 'Message broadcasted'})

@main.route('/relieve_message', methods=['POST'])
def relieve_message():
    message_id = request.form.get('message_id')
    mongo.db.emergency_messages.delete_one({'_id': ObjectId(message_id)})
    return jsonify({'status': 'success', 'message': 'Message relieved and deleted'})