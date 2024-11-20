# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS  # To handle CORS issues
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://192.168.254.42:3000"],  # Add your IP address
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
app.secret_key = 'tomer'

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
users_collection = db['users']
products_collection = db['products']

# User routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        if users_collection.find_one({'username': username}):
            return jsonify({'message': 'Username already exists'}), 400
        
        user = {
            'username': username,
            'password': generate_password_hash(password)
        }
        users_collection.insert_one(user)
        
        return jsonify({'message': 'Registration successful'}), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")  # This will show in your Flask server logs
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500
    
@app.route('/api/users', methods=['GET'])
def get_users():
    users = list(users_collection.find({}, {'_id': 0, 'username': 1, 'password': 1}))
    return jsonify(users)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = users_collection.find_one({'username': username})
    
    if user and check_password_hash(user['password'], password):
        return jsonify({
            'message': 'Login successful',
            'username': username
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

# Product routes
@app.route('/api/products', methods=['GET'])
def get_products():
    products = list(products_collection.find({}, {'_id': 0, 'name': 1, 'price': 1, 'description': 1}))
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    product = {
        'name': data.get('name'),
        'price': float(data.get('price')),
        'description': data.get('description')
    }
    products_collection.insert_one(product)
    return jsonify({'message': 'Product added successfully'}), 201

@app.route('/api/products/<int:product_index>', methods=['DELETE'])
def delete_product(product_index):
    products = list(products_collection.find())
    if 0 <= product_index < len(products):
        product_id = products[product_index]['_id']
        products_collection.delete_one({'_id': product_id})
        return jsonify({'message': 'Product deleted successfully'}), 200
    return jsonify({'message': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')