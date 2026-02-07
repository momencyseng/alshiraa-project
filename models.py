from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Models

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=True) # Nullable for Google users
    email = db.Column(db.String(150), unique=True, nullable=True) # For Google login
    password_hash = db.Column(db.String(200), nullable=True) # Nullable for Google users
    role = db.Column(db.String(50), nullable=False, default='customer') # admin, staff, customer
    google_id = db.Column(db.String(200), unique=True, nullable=True) # Google ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False) # solar, security, inverter
    image_filename = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0) # Price in IQD
    stock = db.Column(db.Integer, nullable=False, default=0) # Stock quantity
    is_special_offer = db.Column(db.Boolean, default=False) # For special offers page
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship('User', backref='posts')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for guest checkout if allowed
    customer_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    delivery_date = db.Column(db.Date, nullable=False) # User selected delivery date
    delivery_cost = db.Column(db.Float, nullable=False, default=5000.0) # Adjustable by employee
    total_price = db.Column(db.Float, nullable=False) # Includes delivery
    status = db.Column(db.String(50), default='New') # New, Processing, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False) # Price at the time of order

    product = db.relationship('Product')

class MaintenanceBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    location_latitude = db.Column(db.Float, nullable=True)
    location_longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='Pending') # Pending, Scheduled, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
