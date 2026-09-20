from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "farmconnect-secret-key-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmconnect.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# DATABASE MODELS
# =========================================================

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
    farmer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="Order Placed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship("User", backref="orders")
    product = db.relationship("Product", backref="orders")


# =========================================================
# NEW: HISTORICAL SALES DATA FOR AI DEMAND FORECASTING
# =========================================================

class SalesHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        nullable=False
    )

    quantity_sold = db.Column(
        db.Float,
        nullable=False
    )

    product = db.relationship(
        "Product",
        backref="sales_history"
    )


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Float, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship("User", backref="cart_items")
    product = db.relationship("Product", backref="cart_items")


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship("User", backref="reviews")
    product = db.relationship("Product", backref="reviews")


# =========================================================
# GLOBAL CART VARIABLES
# =========================================================

@app.context_processor
def inject_cart_variables():
    """Make cart variables available to every template."""

    cart_count = 0
    delivery_charge = 0

    if "user_id" in session:

        cart_items = CartItem.query.filter_by(
            buyer_id=session["user_id"]
        ).all()

        cart_count = sum(
            item.quantity
            for item in cart_items
        )

        subtotal = sum(
            item.product.price * item.quantity
            for item in cart_items
        )

        delivery_charge = (
            0
            if subtotal >= 500 or subtotal == 0
            else 40
        )

    return {
        "cart_count": int(cart_count),
        "delivery_charge": delivery_charge
    }


# =========================================================
# DEMO PRODUCTS
# =========================================================

DEMO_PRODUCTS = [
    (
        "Fresh Tomatoes",
        45,
        "Vegetables",
        "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Potatoes",
        35,
        "Vegetables",
        "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Carrots",
        55,
        "Vegetables",
        "https://images.unsplash.com/photo-1445282768818-728615cc910a?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Broccoli",
        80,
        "Vegetables",
        "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Red Onions",
        40,
        "Vegetables",
        "https://images.unsplash.com/photo-1508747703725-719777637510?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Alphonso Mango",
        140,
        "Fruits",
        "https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Apples",
        160,
        "Fruits",
        "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Bananas",
        55,
        "Fruits",
        "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Oranges",
        90,
        "Fruits",
        "https://images.unsplash.com/photo-1547514701-42782101795e?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Pomegranate",
        180,
        "Fruits",
        "https://images.unsplash.com/photo-1541344999736-83eca272f6fc?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Premium Rice",
        75,
        "Grains",
        "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Whole Wheat",
        42,
        "Grains",
        "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Yellow Maize",
        38,
        "Grains",
        "https://commons.wikimedia.org/wiki/Special:FilePath/Yellow%20corn%20kernels.jpg?width=1000"
    ),
    (
        "Ragi Millet",
        85,
        "Grains",
        ""
    ),
    (
        "Natural Oats",
        120,
        "Grains",
        "https://images.unsplash.com/photo-1517093728432-2f6d4c6f4c8a?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Green Chilli",
        120,
        "Spices",
        "https://commons.wikimedia.org/wiki/Special:FilePath/Green-chillies.jpg?width=1000"
    ),
    (
        "Red Chilli",
        240,
        "Spices",
        "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Black Pepper",
        520,
        "Spices",
        "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Green Cardamom",
        1100,
        "Spices",
        "https://images.unsplash.com/photo-1622824497447-b284a5493027?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Cumin Seeds",
        320,
        "Spices",
        "https://www.spicekitchenuk.com/cdn/shop/files/SK_SpiceShop_CuminSeeds-small.jpg?v=1757430030"
    ),
    (
        "Fresh Farm Milk",
        60,
        "Dairy",
        "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Curd",
        70,
        "Dairy",
        "https://images.unsplash.com/photo-1571212515416-fef01fc43637?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Fresh Paneer",
        320,
        "Dairy",
        "https://commons.wikimedia.org/wiki/Special:FilePath/Homemade%20Paneer%20cut%20into%20pieces%20for%20cooking%20Cheese%20Fromage%20India.jpg?width=1000"
    ),
    (
        "Farm Butter",
        540,
        "Dairy",
        "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=900&q=85"
    ),
    (
        "Pure Farm Ghee",
        650,
        "Dairy",
        "https://www.milcodairy.org/public/assets/admin/uploads/blog/blog_image1658729710.jpg"
    ),
]


# =========================================================
# SEED DEMO PRODUCTS
# =========================================================

def seed_demo_products():
    """Create the 25 marketplace products used by the existing design."""

    demo_email = "demo@farmconnect.local"

    farmer = User.query.filter_by(
        email=demo_email
    ).first()

    if not farmer:
        farmer = User(
            name="FarmConnect Demo Farm",
            email=demo_email,
            password=generate_password_hash(
                "demo-farmer-password"
            ),
            role="farmer",
            phone="9999999999",
            location="Telangana"
        )

        db.session.add(farmer)
        db.session.flush()

    for name, price, category, image in DEMO_PRODUCTS:

        marker = f"[FARMCONNECT_DEMO] {name}"

        product = Product.query.filter_by(
            farmer_id=farmer.id,
            name=name
        ).first()

        if not product:

            product = Product(
                name=name,
                category=category,
                price=price,
                quantity=1000,
                description=marker,
                image=image,
                farmer_id=farmer.id
            )

            db.session.add(product)

        else:

            product.category = category
            product.price = price
            product.image = image

            if product.quantity <= 0:
                product.quantity = 1000

            product.description = marker

    db.session.commit()


# =========================================================
# DEMO HISTORICAL SALES + DEMAND FORECASTING
# =========================================================

def seed_sales_history():
    """
    Create demo sales history for every product that does not have history yet.

    IMPORTANT:
    Do not return just because some SalesHistory rows already exist.
    New products can be added after the original demo history was created.
    Those products also need their own history for AI forecasting.
    """
    products = Product.query.all()
    today = datetime.utcnow().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    category_base = {
        "Vegetables": 35,
        "Fruits": 28,
        "Grains": 20,
        "Spices": 12,
        "Dairy": 30
    }

    added_any = False

    for product in products:

        # If this product already has history, keep it unchanged.
        if SalesHistory.query.filter_by(
            product_id=product.id
        ).first():
            continue

        base = category_base.get(
            product.category,
            20
        )

        factor = 0.70 + (product.id % 7) * 0.10

        for days_ago in range(89, -1, -1):

            day = today - timedelta(
                days=days_ago
            )

            trend = (
                0.85
                + ((89 - days_ago) / 89) * 0.30
            )

            weekday = (
                1.10
                if day.weekday() in (4, 5)
                else 0.95
                if day.weekday() == 0
                else 1.0
            )

            noise = random.Random(
                product.id * 1000 + days_ago
            ).uniform(
                0.82,
                1.18
            )

            qty = round(
                max(
                    1,
                    base
                    * factor
                    * trend
                    * weekday
                    * noise
                ),
                2
            )

            db.session.add(
                SalesHistory(
                    product_id=product.id,
                    date=day,
                    quantity_sold=qty
                )
            )

        added_any = True

    if added_any:
        db.session.commit()

def build_demand_forecasts(products):
    forecasts = []
    for product in products:
        history = SalesHistory.query.filter_by(product_id=product.id).order_by(SalesHistory.date.asc()).all()
        if not history:
            continue
        values = [x.quantity_sold for x in history[-28:]]
        avg_28 = sum(values) / len(values)
        recent = values[-7:]
        previous = values[-14:-7] if len(values) >= 14 else values
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        trend_pct = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg else 0
        trend_factor = max(0.80, min(1.25, 1 + trend_pct / 100 * 0.5))
        predicted_7 = max(1, round(avg_28 * 7 * trend_factor, 1))
        if trend_pct >= 10:
            trend, icon = "Increasing", "📈"
        elif trend_pct <= -10:
            trend, icon = "Decreasing", "📉"
        else:
            trend, icon = "Stable", "➡️"
        daily_need = predicted_7 / 7
        coverage = product.quantity / daily_need if daily_need else 0
        if coverage < 3:
            action = "Consider increasing supply"
        elif coverage > 14:
            action = "Stock is high; avoid overproduction"
        else:
            action = "Current stock is aligned with forecast"
        forecasts.append({"product": product, "predicted_7": predicted_7, "recent_avg": round(recent_avg,1), "trend_pct": round(trend_pct,1), "trend": trend, "trend_icon": icon, "coverage": round(coverage,1), "action": action})
    return forecasts


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()

        if User.query.filter_by(email=email).first():

            flash(
                "Email already registered. Please login."
            )

            return redirect(url_for("login"))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            phone=phone,
            location=location
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully! Please login."
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

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

            return redirect(
                url_for("dashboard")
            )

        flash("Invalid email or password.")

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(
        session["user_id"]
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if user.role == "farmer":

        products = Product.query.filter_by(
            farmer_id=user.id
        ).all()

        orders = (
            Order.query
            .join(
                Product,
                Order.product_id == Product.id
            )
            .filter(
                Product.farmer_id == user.id
            )
            .order_by(
                Order.created_at.desc()
            )
            .all()
        )

        # Make sure newly added products also have AI sales history.
        seed_sales_history()
        forecasts = build_demand_forecasts(products)

        return render_template(
            "farmer_dashboard.html",
            user=user,
            products=products,
            orders=orders,
            forecasts=forecasts,
            ai_result=None
        )

    return render_template(
        "buyer_dashboard.html",
        user=user
    )


# =========================================================
# MARKETPLACE
# =========================================================

@app.route("/marketplace")
def marketplace():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":

        return redirect(
            url_for("dashboard")
        )

    demo_products = {}

    for name, *_ in DEMO_PRODUCTS:

        product = (
            Product.query
            .filter_by(name=name)
            .filter(
                Product.description.like(
                    f"[FARMCONNECT_DEMO] {name}"
                )
            )
            .first()
        )

        if product:
            demo_products[name] = product

    cart_count = sum(
        item.quantity
        for item in CartItem.query.filter_by(
            buyer_id=session["user_id"]
        ).all()
    )

    return render_template(
        "marketplace.html",
        products=[],
        farmers={},
        search=request.args.get(
            "search",
            ""
        ).strip(),
        category=request.args.get(
            "category",
            ""
        ).strip(),
        demo_products=demo_products,
        cart_count=int(cart_count)
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route(
    "/add-product",
    methods=["GET", "POST"]
)
def add_product():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":

        flash(
            "Only farmers can add products."
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        try:

            price = float(
                request.form["price"]
            )

            quantity = float(
                request.form["quantity"]
            )

        except ValueError:

            flash(
                "Price and quantity must be valid numbers."
            )

            return redirect(
                url_for("add_product")
            )

        product = Product(
            name=request.form["name"].strip(),
            category=request.form["category"],
            price=price,
            quantity=quantity,
            description=request.form.get(
                "description",
                ""
            ).strip(),
            image=request.form.get(
                "image",
                ""
            ).strip(),
            farmer_id=session["user_id"]
        )

        db.session.add(product)
        db.session.commit()

        flash(
            "Product added successfully! 🌱"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "add_product.html"
    )


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route(
    "/edit-product/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":

        flash(
            "Only farmers can edit products."
        )

        return redirect(
            url_for("dashboard")
        )

    product = Product.query.get_or_404(
        product_id
    )

    if product.farmer_id != session["user_id"]:

        flash(
            "You cannot edit this product."
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        try:

            product.price = float(
                request.form["price"]
            )

            product.quantity = float(
                request.form["quantity"]
            )

        except ValueError:

            flash(
                "Price and quantity must be valid numbers."
            )

            return redirect(
                url_for(
                    "edit_product",
                    product_id=product_id
                )
            )

        product.name = request.form[
            "name"
        ].strip()

        product.category = request.form[
            "category"
        ]

        product.description = request.form.get(
            "description",
            ""
        ).strip()

        product.image = request.form.get(
            "image",
            ""
        ).strip()

        db.session.commit()

        flash(
            "Product updated successfully! ✏️"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "edit_product.html",
        product=product
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route(
    "/delete-product/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":

        flash(
            "Only farmers can delete products."
        )

        return redirect(
            url_for("dashboard")
        )

    product = Product.query.get_or_404(
        product_id
    )

    if product.farmer_id != session["user_id"]:

        flash(
            "You cannot delete this product."
        )

        return redirect(
            url_for("dashboard")
        )

    CartItem.query.filter_by(
        product_id=product.id
    ).delete()

    db.session.delete(product)
    db.session.commit()

    flash(
        "Product deleted successfully. 🗑️"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADD TO CART
# =========================================================

@app.route(
    "/add-to-cart/<int:product_id>",
    methods=["POST"]
)
def add_to_cart(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":

        flash(
            "Only buyers can add products to cart."
        )

        return redirect(
            url_for("dashboard")
        )

    product = Product.query.get_or_404(
        product_id
    )

    if product.quantity <= 0:

        flash(
            "This product is out of stock."
        )

        return redirect(
            url_for("marketplace")
        )

    item = CartItem.query.filter_by(
        buyer_id=session["user_id"],
        product_id=product.id
    ).first()

    if item:

        if item.quantity + 1 > product.quantity:

            flash(
                "Not enough stock available."
            )

            return redirect(
                url_for("marketplace")
            )

        item.quantity += 1

    else:

        db.session.add(
            CartItem(
                buyer_id=session["user_id"],
                product_id=product.id,
                quantity=1
            )
        )

    db.session.commit()

    flash(
        f"{product.name} added to cart 🛒"
    )

    return redirect(
        url_for("marketplace")
    )


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":

        return redirect(
            url_for("dashboard")
        )

    cart_items = (
        CartItem.query
        .filter_by(
            buyer_id=session["user_id"]
        )
        .order_by(
            CartItem.created_at.desc()
        )
        .all()
    )

    subtotal = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    delivery = (
        0
        if subtotal >= 500 or subtotal == 0
        else 40
    )

    total = subtotal + delivery

    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=subtotal,
        delivery=delivery,
        delivery_charge=delivery,
        total=total
    )


# =========================================================
# UPDATE CART
# =========================================================

@app.route(
    "/cart/update/<int:item_id>",
    methods=["POST"]
)
def update_cart(item_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    item = CartItem.query.filter_by(
        id=item_id,
        buyer_id=session["user_id"]
    ).first_or_404()

    try:

        quantity = float(
            request.form.get(
                "quantity",
                1
            )
        )

    except ValueError:

        quantity = 1

    if quantity <= 0:

        db.session.delete(item)

    elif quantity > item.product.quantity:

        flash(
            "Requested quantity is greater than available stock."
        )

    else:

        item.quantity = quantity

    db.session.commit()

    return redirect(
        url_for("cart")
    )


# =========================================================
# REMOVE FROM CART
# =========================================================

@app.route(
    "/cart/remove/<int:item_id>",
    methods=["POST"]
)
def remove_from_cart(item_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    item = CartItem.query.filter_by(
        id=item_id,
        buyer_id=session["user_id"]
    ).first_or_404()

    db.session.delete(item)
    db.session.commit()

    flash(
        "Item removed from cart."
    )

    return redirect(
        url_for("cart")
    )


# =========================================================
# CLEAR CART
# =========================================================

@app.route(
    "/cart/clear",
    methods=["POST"]
)
def clear_cart():

    if "user_id" not in session:
        return redirect(url_for("login"))

    CartItem.query.filter_by(
        buyer_id=session["user_id"]
    ).delete()

    db.session.commit()

    flash(
        "Cart cleared."
    )

    return redirect(
        url_for("cart")
    )


# =========================================================
# CHECKOUT
# =========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":

        return redirect(
            url_for("dashboard")
        )

    cart_items = (
        CartItem.query
        .filter_by(
            buyer_id=session["user_id"]
        )
        .order_by(
            CartItem.created_at.desc()
        )
        .all()
    )

    if not cart_items:

        flash(
            "Your cart is empty."
        )

        return redirect(
            url_for("marketplace")
        )

    subtotal = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    delivery = (
        0
        if subtotal >= 500
        else 40
    )

    total = subtotal + delivery

    if request.method == "POST":

        address = request.form.get(
            "address",
            ""
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            "Cash on Delivery"
        )

        if not address:

            flash(
                "Please enter your delivery address."
            )

            return redirect(
                url_for("checkout")
            )

        if payment_method not in [
            "Cash on Delivery",
            "UPI",
            "Demo Card"
        ]:

            payment_method = "Cash on Delivery"

        # Re-check stock before creating orders.
        for item in cart_items:

            if item.quantity > item.product.quantity:

                flash(
                    f"Not enough stock for "
                    f"{item.product.name}. "
                    f"Available: "
                    f"{item.product.quantity:g}"
                )

                return redirect(
                    url_for("cart")
                )

        # Store one Order row per cart product.
        for item in cart_items:

            item.product.quantity -= item.quantity

            order = Order(
                buyer_id=session["user_id"],
                product_id=item.product_id,
                quantity=item.quantity,
                total_price=(
                    item.product.price *
                    item.quantity
                ),
                status="Order Placed"
            )

            db.session.add(order)

        CartItem.query.filter_by(
            buyer_id=session["user_id"]
        ).delete()

        db.session.commit()

        flash(
            f"Order placed successfully! "
            f"Payment method: {payment_method}. "
            "This is a demo payment flow."
        )

        return redirect(
            url_for("my_orders")
        )

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        subtotal=subtotal,
        delivery=delivery,
        total=total
    )


# =========================================================
# BUYER ORDERS
# =========================================================

@app.route("/orders")
def my_orders():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":

        return redirect(
            url_for("dashboard")
        )

    orders = (
        Order.query
        .filter_by(
            buyer_id=session["user_id"]
        )
        .order_by(
            Order.created_at.desc()
        )
        .all()
    )

    return render_template(
        "orders.html",
        orders=orders
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route(
    "/product/<int:product_id>"
)
def product_details(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    product = Product.query.get_or_404(
        product_id
    )

    reviews = (
        Review.query
        .filter_by(
            product_id=product.id
        )
        .order_by(
            Review.created_at.desc()
        )
        .all()
    )

    average_rating = (
        sum(
            review.rating
            for review in reviews
        ) / len(reviews)
        if reviews
        else 0
    )

    return render_template(
        "product_details.html",
        product=product,
        reviews=reviews,
        average_rating=average_rating
    )


# =========================================================
# ADD REVIEW
# =========================================================

@app.route(
    "/product/<int:product_id>/review",
    methods=["POST"]
)
def add_review(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "buyer":

        flash(
            "Only buyers can submit reviews."
        )

        return redirect(
            url_for(
                "product_details",
                product_id=product_id
            )
        )

    product = Product.query.get_or_404(
        product_id
    )

    purchased = Order.query.filter_by(
        buyer_id=session["user_id"],
        product_id=product.id
    ).first()

    if not purchased:

        flash(
            "You can review a product after purchasing it."
        )

        return redirect(
            url_for(
                "product_details",
                product_id=product.id
            )
        )

    try:

        rating = int(
            request.form.get(
                "rating",
                5
            )
        )

    except (
        TypeError,
        ValueError
    ):

        rating = 5

    rating = max(
        1,
        min(5, rating)
    )

    comment = request.form.get(
        "comment",
        ""
    ).strip()

    existing = Review.query.filter_by(
        buyer_id=session["user_id"],
        product_id=product.id
    ).first()

    if existing:

        existing.rating = rating
        existing.comment = comment
        existing.created_at = datetime.utcnow()

        flash(
            "Your review was updated. ⭐"
        )

    else:

        db.session.add(
            Review(
                buyer_id=session["user_id"],
                product_id=product.id,
                rating=rating,
                comment=comment
            )
        )

        flash(
            "Review added successfully. ⭐"
        )

    db.session.commit()

    return redirect(
        url_for(
            "product_details",
            product_id=product.id
        )
    )


# =========================================================
# FARMER ORDERS
# =========================================================

@app.route("/farmer/orders")
def farmer_orders():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":

        return redirect(
            url_for("dashboard")
        )

    orders = (
        Order.query
        .join(
            Product,
            Order.product_id == Product.id
        )
        .filter(
            Product.farmer_id ==
            session["user_id"]
        )
        .order_by(
            Order.created_at.desc()
        )
        .all()
    )

    return render_template(
        "farmer_orders.html",
        orders=orders
    )


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

@app.route(
    "/farmer/orders/<int:order_id>/status",
    methods=["POST"]
)
def update_order_status(order_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "farmer":

        return redirect(
            url_for("dashboard")
        )

    order = Order.query.get_or_404(
        order_id
    )

    if order.product.farmer_id != session["user_id"]:

        flash(
            "You cannot update this order."
        )

        return redirect(
            url_for("farmer_orders")
        )

    allowed_statuses = [
        "Order Placed",
        "Confirmed",
        "Packed",
        "Shipped",
        "Delivered"
    ]

    status = request.form.get(
        "status",
        ""
    ).strip()

    if status not in allowed_statuses:

        flash(
            "Invalid order status."
        )

        return redirect(
            url_for("farmer_orders")
        )

    order.status = status

    db.session.commit()

    flash(
        f"Order #FC{order.id:05d} "
        f"updated to {status}."
    )

    return redirect(
        url_for("farmer_orders")
    )


# =========================================================
# AI PRICE RECOMMENDATION
# =========================================================

@app.route("/ai-price-recommendation", methods=["POST"])
def ai_price_recommendation():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") != "farmer":
        return redirect(url_for("dashboard"))
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    products = Product.query.filter_by(farmer_id=user.id).all()
    orders = Order.query.join(Product, Order.product_id == Product.id).filter(Product.farmer_id == user.id).order_by(Order.created_at.desc()).all()
    # Ensure the selected/new product has sales history before
    # calculating its AI price recommendation.
    seed_sales_history()
    forecasts = build_demand_forecasts(products)

    try:
        product_id = int(request.form.get("product_id", 0))
    except (TypeError, ValueError):
        return redirect(url_for("dashboard"))
    product = Product.query.filter_by(id=product_id, farmer_id=user.id).first()
    if not product:
        flash("Please select one of your products.")
        return redirect(url_for("dashboard"))
    forecast = next((f for f in forecasts if f["product"].id == product.id), None)
    if not forecast:
        flash("Forecast is not available for this product yet.")
        return redirect(url_for("dashboard"))
    trend_factor = max(-0.08, min(0.10, forecast["trend_pct"] / 100 * 0.35))
    stock_factor = 0.04 if forecast["coverage"] < 3 else -0.04 if forecast["coverage"] > 14 else 0
    recommended = round(max(product.price * 0.85, min(product.price * 1.20, product.price * (1 + trend_factor + stock_factor))), 2)
    change = round((recommended - product.price) / product.price * 100, 1)
    ai_result = {"product": product, "current_price": product.price, "recommended_price": recommended, "change": change, "forecast": forecast, "reason": f"Based on the recent sales trend ({forecast['trend_pct']:+.1f}%) and estimated 7-day demand of {forecast['predicted_7']:g} kg."}
    return render_template("farmer_dashboard.html", user=user, products=products, orders=orders, forecasts=forecasts, ai_result=ai_result)

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

with app.app_context():

    db.create_all()
    seed_demo_products()
    seed_sales_history()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)