from flask import Flask,render_template, redirect, url_for, flash, request, abort
from functools import wraps
from form import LoginForm, RegistrationForm
from models import User, db, Product, CartItem, Order, OrderItem, Payment
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_migrate import Migrate
from flask_mail import Message, Mail
import requests
import os
from dotenv import load_dotenv
import psycopg2
import email_validator

load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail_1 = Mail(app)


login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "account"
login_manager.login_message = "Please login to access this page."
login_manager.login_message_category = "warning"



db.init_app(app)
migrate = Migrate(app, db)

@app.route('/init_db')
def init_db():
    db.create_all()
    return "✅ Database tables created successfully!"


@login_manager.user_loader
def load_user(user_id):
        return db.get_or_404(User, int(user_id))

def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return func(*args, **kwargs)
    return decorated_function

def get_eth_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "ethereum", "vs_currencies": "usd"}
    response = requests.get(url, params=params).json()
    return response["ethereum"]["usd"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy-policy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms-and-conditions")
def terms():
    return render_template("terms.html")

@app.route("/products")
def products():
    all_products = Product.query.all()
    return render_template("products.html", products=all_products)

@app.route("/products/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)

@app.route("/add_product", methods=["GET", "POST"])
@admin_only
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        description = request.form.get("description")
        image_url = request.form.get("image_url")
        stock = int(request.form.get("stock", 0))

        new_product = Product(
            name=name,
            price=price,
            description=description,
            image_url=image_url,
            stock=stock
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!", "success")
        return redirect(url_for("products"))

    return render_template("add_product.html")

@app.route("/dashboard")
@login_required
def dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    payments = Payment.query.filter_by(user_id=current_user.id).all()
    return render_template("user_dashboard.html", user=current_user, orders=orders, payments=payments)

@app.route("/account", methods=["GET", "POST"])
def account():
    login_form = LoginForm()
    register_form = RegistrationForm()

    # Registration
    if register_form.submit_register.data and register_form.validate_on_submit():
        hashed_password = generate_password_hash(
            register_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            username=register_form.username.data,
            email=register_form.email.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can now login.", "success")
        return redirect(url_for("account"))

    if login_form.submit_login.data and login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and check_password_hash(user.password, login_form.password.data):
            login_user(user, remember=login_form.remember_me.data)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")

    return render_template("account.html", login_form=login_form, register_form=register_form)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('reset_token', token=token, _external=True)

            msg = Message("Password Reset Request",
                          sender="noreply@teslix.com",
                          recipients=[user.email])
            msg.body = f"Click the link to reset your password: {reset_url}"
            mail_1.send(msg)

        flash("If an account with that email exists, a reset link has been sent.", "info")
        return redirect(url_for("login"))

    return render_template("reset_request.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    user = User.verify_reset_token(token)
    if not user:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("reset_request"))

    if request.method == "POST":
        new_password = request.form.get("password")
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Your password has been updated!", "success")
        return redirect(url_for("login"))

    return render_template("reset_token.html")


@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    username = request.form.get("username")
    email = request.form.get("email")

    if not username or not email:
        flash("Username and email are required.", "danger")
        return redirect(url_for("dashboard"))

    current_user.username = username
    current_user.email = email
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=1)
    db.session.add(cart_item)
    db.session.commit()
    flash(f"{product.name} has been added to your cart.", "success")
    return redirect(url_for("view_cart"))

@app.route("/remove_from_cart/<int:item_id>", methods=["POST", "GET"])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "success")
    return redirect(url_for("view_cart"))

@app.route("/cart")
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    total_items = sum(item.quantity for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total, total_items=total_items)

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("view_cart"))

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    tax = round(subtotal * 0.07, 2)
    total_usd = subtotal + tax

    eth_price = get_eth_price()
    total_eth = round(total_usd / eth_price, 6)


    if request.method == "POST":
        # Create new order
        order = Order(user_id=current_user.id, total_price=total_usd, status="Pending")
        db.session.add(order)
        db.session.commit()

        # Add order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            db.session.delete(item)  # clear cart after checkout

        db.session.commit()
        flash("Order placed successfully!", "success")
        return redirect(url_for("order_confirmation", order_id=order.id))

    return render_template("checkout.html", subtotal=subtotal,  cart_items=cart_items, tax=tax, total_usd=total_usd, total_eth=total_eth)

@app.route("/order/<int:order_id>")
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template("order_confirmation.html", order=order, order_items=order_items)

@app.route("/admin/orders")
@login_required
def admin_orders():
    if not current_user.is_authenticated or current_user.id != 1:
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    orders = Order.query.all()
    return render_template("admin_orders.html", orders=orders)

@app.route("/admin/update_order/<int:order_id>", methods=["POST"])
@login_required
def update_order(order_id):
    if not current_user.is_authenticated or current_user.id != 1:
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    order.status = new_status

    # also update related payment if exists
    payment = Payment.query.filter_by(order_id=order.id).first()
    if payment:
        if new_status == "Successful":
            payment.status = "Successful"
        elif new_status == "Delivered":
            payment.status = "Successful"  # keep successful but order is delivered

    db.session.commit()
    flash("Order and payment status updated successfully!", "success")
    return redirect(url_for("admin_orders"))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)