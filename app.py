from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# =========================
# SECURITY
# =========================

app.config["SECRET_KEY"] = "farmconnect-secret-key-change-later"

# =========================
# DATABASE
# =========================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmconnect.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(150))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    description = db.Column(db.Text)
    image = db.Column(db.String(300))

    farmer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    status = db.Column(
        db.String(30),
        default="Order Placed"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]

        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash("Email already registered. Please login.")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            phone=phone,
            location=location
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please login.")

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if user.role == "farmer":

        products = Product.query.filter_by(
            farmer_id=user.id
        ).all()

        return render_template(
            "farmer_dashboard.html",
            user=user,
            products=products
        )

    return render_template(
        "buyer_dashboard.html",
        user=user
    )


# =========================
# BUYER MARKETPLACE
# =========================

@app.route("/marketplace")
def marketplace():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":
        return redirect(url_for("dashboard"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    query = Product.query

    # Search by product name
    if search:

        query = query.filter(
            Product.name.ilike(f"%{search}%")
        )

    # Filter by category
    if category:

        query = query.filter(
            Product.category == category
        )

    # Only products that have stock
    query = query.filter(
        Product.quantity > 0
    )

    products = query.order_by(
        Product.created_at.desc()
    ).all()

    # Get farmer names
    farmers = {}

    for product in products:

        farmer = User.query.get(
            product.farmer_id
        )

        farmers[product.farmer_id] = farmer

    return render_template(
        "marketplace.html",
        products=products,
        farmers=farmers,
        search=search,
        category=category
    )


# =========================
# ADD PRODUCT
# =========================

@app.route("/add-product", methods=["GET", "POST"])
def add_product():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":
        flash("Only farmers can add products.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form["name"].strip()
        category = request.form["category"]

        price = float(request.form["price"])
        quantity = float(request.form["quantity"])

        description = request.form.get(
            "description",
            ""
        ).strip()

        image = request.form.get(
            "image",
            ""
        ).strip()

        product = Product(
            name=name,
            category=category,
            price=price,
            quantity=quantity,
            description=description,
            image=image,
            farmer_id=session["user_id"]
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully! 🌱")

        return redirect(url_for("dashboard"))

    return render_template("add_product.html")


# =========================
# EDIT PRODUCT
# =========================

@app.route(
    "/edit-product/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":
        return redirect(url_for("dashboard"))

    product = Product.query.get_or_404(
        product_id
    )

    # Only product owner can edit
    if product.farmer_id != session["user_id"]:

        flash("You cannot edit this product.")

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        product.name = request.form["name"].strip()

        product.category = request.form["category"]

        product.price = float(
            request.form["price"]
        )

        product.quantity = float(
            request.form["quantity"]
        )

        product.description = request.form.get(
            "description",
            ""
        ).strip()

        product.image = request.form.get(
            "image",
            ""
        ).strip()

        db.session.commit()

        flash("Product updated successfully! ✏️")

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_product.html",
        product=product
    )


# =========================
# DELETE PRODUCT
# =========================

@app.route(
    "/delete-product/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":
        return redirect(url_for("dashboard"))

    product = Product.query.get_or_404(
        product_id
    )

    # Only product owner can delete
    if product.farmer_id != session["user_id"]:

        flash("You cannot delete this product.")

        return redirect(url_for("dashboard"))

    db.session.delete(product)

    db.session.commit()

    flash("Product deleted successfully. 🗑️")

    return redirect(url_for("dashboard"))


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================
# CREATE DATABASE
# =========================

with app.app_context():
    db.create_all()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)