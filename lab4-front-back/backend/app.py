from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
import sys

app = Flask(__name__)

# Updated CORS configuration to be more permissive during development
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins during development
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 600
    }
})

app.secret_key = 'tomer'

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    # Allow all origins during development
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def setup_mongodb():
    try:
        # Connect to MongoDB with error handling
        try:
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
            # Test the connection
            client.server_info()
            db = client['ecommerce_db']
        except Exception as e:
            print(f"Failed to connect to MongoDB: {str(e)}")
            sys.exit(1)
        
        # Create collections if they don't exist
        if 'users' not in db.list_collection_names():
            users_collection = db.create_collection('users')
            users_collection.create_index([('username', ASCENDING)], unique=True)
            print("Users collection created with indexes")
        else:
            users_collection = db['users']
            
        if 'products' not in db.list_collection_names():
            products_collection = db.create_collection('products')
            products_collection.create_index([('name', ASCENDING)])
            print("Products collection created with indexes")
        else:
            products_collection = db['products']
            
        print("MongoDB setup completed successfully!")
        return client, db, users_collection, products_collection
        
    except Exception as e:
        print(f"MongoDB setup error: {str(e)}", file=sys.stderr)
        sys.exit(1)

# Initialize MongoDB
client, db, users_collection, products_collection = setup_mongodb()

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'collections': db.list_collection_names()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    print("Received registration request")
    try:
        data = request.get_json()  # Changed from request.json for better error handling
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        # Check if user already exists
        if users_collection.find_one({'username': username}):
            return jsonify({'message': 'Username already exists'}), 409
        
        user = {
            'username': username,
            'password': generate_password_hash(password)
        }
        users_collection.insert_one(user)
        
        return jsonify({'message': 'Registration successful'}), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = list(users_collection.find({}, {'password': 0}))
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify(users)
    except Exception as e:
        return jsonify({'message': f'Error fetching users: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
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
    except Exception as e:
        return jsonify({'message': f'Login error: {str(e)}'}), 500

# Product routes
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = list(products_collection.find())
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify(products)
    except Exception as e:
        return jsonify({'message': f'Error fetching products: {str(e)}'}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        data = request.json
        product = {
            'name': data.get('name'),
            'price': float(data.get('price')),
            'description': data.get('description')
        }
        result = products_collection.insert_one(product)
        product['_id'] = str(result.inserted_id)
        return jsonify({'message': 'Product added successfully', 'product': product}), 201
    except Exception as e:
        return jsonify({'message': f'Error adding product: {str(e)}'}), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        result = products_collection.delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count:
            return jsonify({'message': 'Product deleted successfully'}), 200
        return jsonify({'message': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'message': f'Error deleting product: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')