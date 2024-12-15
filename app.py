from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from sqlalchemy import select
from models import Base, User, Order, Product, order_product
from models import user_schema, order_schema, product_schema, users_schema, orders_schema, products_schema

# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:WaTers01#@localhost/ec_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow extensions
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

#-------API ENDPOINTS / ROUTES--------
# User Endpoints
@app.route('/users', methods=['GET']) # Retrieve all users
def get_users():
    query = select(User) # Constructs an SQL query to select all records from the User table
    users = db.session.execute(query).scalars().all() # Executes the query and retrieves all user records from db as a list
    
    return users_schema.jsonify(users), 200 # Serializes the list of users in JSON format and returns list w/ a 200 status code

@app.route('/users/<int:user_id>', methods=['GET']) # Retrieve a user by ID [GET]
def get_user(user_id):
    user = db.session.get(User, user_id) # Queries db to retrieve user object based on the provided id
    
    if not user:
        return jsonify({'message': 'Invalid user id'}), 400 # If user is not found return error message w/ code 400
    else:
        return user_schema.jsonify(user), 200

@app.route('/users', methods=['POST']) # Create a new user [POST]
def create_user():
    try:
        # Uses Marshmallow to validate and deserialize the incoming JSON into a user object
        user_data = user_schema.load(request.json) # 'request.json' Retrieves the JSON data from the incoming request
    except ValidationError as e:
        return jsonify(e.messages), 400 # Catches any validation errors and returns a 400 status w/ error messages if invalid data is provided
    
    # When deserializing a JSON into python it becomes a dictionary. So you use the key of 'name' to find the value of whatever the user entered
    new_user = User(name=user_data['name'], address=user_data['address'], email=user_data['email'])
    db.session.add(new_user) 
    db.session.commit() # Adds and saves the new user to the database
    
    return user_schema.jsonify(new_user), 201 # Returns the newly created user in JSON format w/ a 201 status

@app.route('/users/<int:user_id>', methods=['PUT']) # Update a user by ID [PUT]
def update_user(user_id):
    user = db.session.get(User, user_id) # Queries db to retrieve user object based on the provided id
    
    if not user:
        return jsonify({'message': 'Invalid user id'}), 400 # If no user is found return code 400 w/ error message
    
    try:
        user_data = user_schema.load(request.json) # Attempts to load updated data from request, handles validation errors
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Update the user's info
    user.name = user_data['name']
    user.address = user_data['address']
    user.email = user_data['email']
    
    # Save and return new data w/ code 200
    db.session.commit()
    return user_schema.jsonify(user), 200

@app.route('/users/<int:user_id>', methods=['DELETE']) # Delete a user by ID
def delete_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({'message': 'Invalid user id'}), 400 # If no user is found return code 400 w/ error message
    
    db.session.delete(user) # Delete the user and save the changes
    db.session.commit()
    return jsonify({'message': f"Successfully deleted user {user_id}"}), 200

# Product Endpoints
@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()
    
    return products_schema.jsonify(products), 200

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    
    if not product:
        return jsonify({'message': 'Invalid product id'}), 400
    else:
        return product_schema.jsonify(product), 200
    
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    
    return product_schema.jsonify(new_product), 201
    
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = db.session.get(Product, product_id)
    
    if not product:
        return jsonify({'message': 'Invalid product id'}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({'message': 'Invalid product id'}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': f"Successfully deleted product {product_id}"}), 200

# Order Endpoints
@app.route('/orders/user/<int:user_id>', methods=['GET']) # Get all orders under one user
def get_orders(user_id):
        query = select(Order).where(Order.user_id == user_id)
        orders = db.session.execute(query).scalars().all()
        
        if not orders:
            return jsonify({'message': f'No orders found under user id {user_id}'}), 404
        
        return orders_schema.jsonify(orders), 200

@app.route('/orders/<int:order_id>/products', methods=['GET']) # Get all products for an order
def get_order(order_id):
    order = db.session.get(Order, order_id)
    
    if not order:
        return jsonify({'message': 'Invalid order id'}), 400
    
    products = order.products
    
    if not products:
        return jsonify({'message': f'No products found under order id {order_id}'}), 404
    
    return products_schema.jsonify(products)
    
@app.route('/orders', methods=['POST']) # Create an order
def create_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    user_id = order_data['user_id']
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'Invalid user id'}), 400

    new_order = Order(user_id=user_id)
    db.session.add(new_order)
    db.session.commit()

    return jsonify({'message': 'Order created successfully', 'order_id': new_order.id}), 201
    
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['GET']) # Add product to an order
def add_product(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)
    
    if not product:
        return jsonify({'message': 'Invalid product id'}), 400
    elif not order:
        return jsonify({'message': 'Invalid order id'}), 400
    
    if product not in order.products:
        order.products.append(product)
        db.session.commit()
        
        return jsonify({'message': f'Product id {product_id} has been added to order id {order_id}'}), 200
    else:
        return jsonify({'message': 'Cannot add duplicate product to an order'}), 400

@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE']) # Delete a product from an order
def remove_product(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)
    
    if not product:
        return jsonify({'message': 'Invalid product id'}), 400
    elif not order:
        return jsonify({'message': 'Invalid order id'}), 400
    
    if product not in order.products:
        return jsonify({'message': f'Product id {product_id} is not in order id {order_id}'}), 400

    order.products.remove(product)
    db.session.commit()
    
    return jsonify({'message': f'Product id {product_id} has been removed from order id {order_id}'}), 200



if __name__ == '__main__':
    
    with app.app_context():
        #db.drop_all()
        db.create_all()
        
    app.run(debug=True)