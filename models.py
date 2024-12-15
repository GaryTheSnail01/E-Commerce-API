from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, DateTime, Float, Column, UniqueConstraint
from datetime import datetime
from typing import List

# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:WaTers01#@localhost/ec_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Creating our Base Class
class Base(DeclarativeBase):
    pass

# Order - Product Association Table
order_product = Table(
    'order_product',
    Base.metadata,
    Column('order_id', ForeignKey('orders.id')),
    Column('product_id', ForeignKey('products.id')),
    UniqueConstraint('order_id', 'product_id', name='uq_order_product') # Prevents duplicate entries for the same product in each order
)

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True) # email must be unique to each user
    
    orders: Mapped[List['Order']] = relationship(back_populates='user', cascade='all, delete-orphan') # One to Many relationship from a user to their orders

class Order(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # Saves what time the order was placed
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    
    user: Mapped[List['User']] = relationship(back_populates='orders') # Many to One relationship, multiple orders to the same user
    
    # One to Many relationship between an order and their products using the 'order_product' table
    products: Mapped[List['Product']] = relationship(secondary='order_product', back_populates='orders')
    
class Product(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # One to Many relationship between a product and their orders using the 'order_product' table
    orders: Mapped[List['Order']] = relationship(secondary='order_product', back_populates='products')
    
# Initialize SQLAlchemy and Marshmallow extensions
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)
    
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        
    id = fields.Integer()
    product_name = fields.String()
    price = fields.Float()
    
class OrderSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Order

    id = fields.Integer()
    user_id = fields.Integer()
    order_date = fields.DateTime()
    products = fields.List(fields.Nested(ProductSchema))
    
    
user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)