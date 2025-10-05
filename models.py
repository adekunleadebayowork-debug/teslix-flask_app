from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")


    def get_reset_token(self, expires_sec=1800):
        """
        Generate a token for password reset.
        expires_sec = seconds before token expires (default 30 minutes).
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """
        Verify the token and return the user if valid, otherwise None.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=True)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    cart_items = db.relationship("CartItem", back_populates="product")
    order_items = db.relationship("OrderItem", back_populates="product")


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    # Relationships
    user = db.relationship("User", back_populates="cart_items")
    product = db.relationship("Product", back_populates="cart_items")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Relationships
    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)

    # Relationships
    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="payments")

    order = db.relationship("Order", back_populates="payment")

    def __repr__(self):
        return f"<Payment {self.id} - {self.status}>"


# from flask_sqlalchemy import SQLAlchemy
# from flask_login import UserMixin
#
# db = SQLAlchemy()
#
#
# class Product(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)  # e.g., "Model S"
#     image_url = db.Column(db.String, nullable=False)
#     price = db.Column(db.Float, nullable=False)
#     description = db.Column(db.Text)
#     # Add image URL, stock, etc.
#
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(128))  # Use hashing for security
#
# class CartItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
#     quantity = db.Column(db.Integer, default=1)
#
# class Order(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     total_price = db.Column(db.Float, nullable=False)
#     status = db.Column(db.String(50), default='Pending')  # e.g., Pending, Paid, Shipped
#     # Add items as a relationship or separate OrderItem model

