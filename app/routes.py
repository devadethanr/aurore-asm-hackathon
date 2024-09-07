from flask import Blueprint, jsonify, request, render_template
from app import mongo

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/send_location', methods=['POST'])
def send_location():
    data = request.get_json()
    if not data or 'username' not in data or 'lat' not in data or 'lon' not in data:
        return jsonify({'error': 'Invalid data'}), 400

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