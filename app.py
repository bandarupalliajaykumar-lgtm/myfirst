from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime, timedelta

import random


# ============================================================
# FARMCONNECT
# COMPLETE BACKEND - PART 1
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "farmconnect-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmconnect.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# MODELS
# ============================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    phone = db.Column(db.String(20))

    location = db.Column(db.String(200))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Product(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    category = db.Column(
        db.String(80),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    quantity = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    description = db.Column(db.Text)

    image = db.Column(db.String(500))

    farmer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    farmer = db.relationship(
        "User",
        foreign_keys=[farmer_id],
        backref="products"
    )


class Order(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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

    quantity = db.Column(
        db.Float,
        nullable=False
    )

    total_price = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="Order Placed"
    )

    delivery_address = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        backref="orders"
    )

    product = db.relationship(
        "Product",
        backref="orders"
    )


class CartItem(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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

    quantity = db.Column(
        db.Float,
        nullable=False,
        default=1
    )

    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        backref="cart_items"
    )

    product = db.relationship(
        "Product",
        backref="cart_items"
    )


class Review(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    product = db.relationship(
        "Product",
        backref="reviews"
    )

    user = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        backref="reviews"
    )


class SalesHistory(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
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


# ============================================================
# OFFICIAL 25 PRODUCTS
# ============================================================

DEMO_PRODUCTS = [

    (
        "Fresh Tomatoes",
        "Vegetables",
        45,
        "/static/images/Fresh Tomatoes.jpg"
    ),

    (
        "Fresh Potatoes",
        "Vegetables",
        35,
        "/static/images/Fresh Potatoes.jpg"
    ),

    (
        "Fresh Carrots",
        "Vegetables",
        55,
        "/static/images/Fresh Carrots.jpg"
    ),

    (
        "Fresh Broccoli",
        "Vegetables",
        80,
        "/static/images/Fresh Broccoli.jpg"
    ),

    (
        "Red Onions",
        "Vegetables",
        40,
        "/static/images/Red Onions.jpg"
    ),

    (
        "Alphonso Mango",
        "Fruits",
        140,
        "/static/images/Alphonso Mango.jpg"
    ),

    (
        "Fresh Apples",
        "Fruits",
        160,
        "/static/images/Fresh Apples.jpg"
    ),

    (
        "Fresh Bananas",
        "Fruits",
        55,
        "/static/images/Fresh Bananas.jpg"
    ),

    (
        "Fresh Oranges",
        "Fruits",
        90,
        "/static/images/Fresh Oranges.jpg"
    ),

    (
        "Pomegranate",
        "Fruits",
        180,
        "/static/images/Pomegranate.jpg"
    ),

    (
        "Premium Rice",
        "Grains",
        75,
        "/static/images/Premium Rice.jpg"
    ),

    (
        "Whole Wheat",
        "Grains",
        42,
        "/static/images/Whole Wheat.jpg"
    ),

    (
        "Yellow Maize",
        "Grains",
        38,
        "/static/images/Yellow Maize.jpg"
    ),

    (
        "Ragi Millet",
        "Grains",
        85,
        "/static/images/Ragi Millet.jpg"
    ),

    (
        "Natural Oats",
        "Grains",
        120,
        "/static/images/Natural Oats.jpg"
    ),

    (
        "Green Chilli",
        "Spices",
        120,
        "/static/images/Green Chilli.jpg"
    ),

    (
        "Red Chilli",
        "Spices",
        240,
        "/static/images/Red Chilli.jpg"
    ),

    (
        "Black Pepper",
        "Spices",
        520,
        "/static/images/Black Pepper.jpg"
    ),

    (
        "Green Cardamom",
        "Spices",
        1100,
        "/static/images/Green Cardamom.jpeg"
    ),

    (
        "Cumin Seeds",
        "Spices",
        320,
        "/static/images/Cumin Seeds.jpg"
    ),

    (
        "Fresh Farm Milk",
        "Dairy",
        60,
        "/static/images/Fresh Farm Milk.jpg"
    ),

    (
        "Fresh Curd",
        "Dairy",
        70,
        "/static/images/Fresh Curd.jpg"
    ),

    (
        "Fresh Paneer",
        "Dairy",
        320,
        "/static/images/Fresh Paneer.jpg"
    ),

    (
        "Farm Butter",
        "Dairy",
        540,
        "/static/images/Farm Butter.jpg"
    ),

    (
        "Pure Farm Ghee",
        "Dairy",
        650,
        "/static/images/Pure Farm Ghee.jpg"
    )

]


# ============================================================
# HELPER
# ============================================================

def get_current_user():

    if "user_id" not in session:
        return None

    return db.session.get(
        User,
        session["user_id"]
    )


# ============================================================
# SEED OFFICIAL PRODUCTS
# ============================================================

def seed_demo_products():

    farmer = User.query.filter_by(
        email="demo_farmer@farmconnect.com"
    ).first()

    if not farmer:

        farmer = User(
            name="Demo Farmer",
            email="demo_farmer@farmconnect.com",
            password=generate_password_hash("demo123"),
            role="farmer",
            phone="9999999999",
            location="Hyderabad"
        )

        db.session.add(farmer)

        db.session.commit()


    official_names = {
        item[0]
        for item in DEMO_PRODUCTS
    }


    # --------------------------------------------------------
    # REMOVE OLD DEMO PRODUCTS
    # --------------------------------------------------------

    old_products = Product.query.filter_by(
        farmer_id=farmer.id
    ).all()


    for product in old_products:

        if product.name not in official_names:

            CartItem.query.filter_by(
                product_id=product.id
            ).delete(
                synchronize_session=False
            )

            Review.query.filter_by(
                product_id=product.id
            ).delete(
                synchronize_session=False
            )

            SalesHistory.query.filter_by(
                product_id=product.id
            ).delete(
                synchronize_session=False
            )

            # Do not remove products having orders.
            # Instead make them unavailable.

            if Order.query.filter_by(
                product_id=product.id
            ).first():

                product.quantity = 0

            else:

                db.session.delete(product)


    db.session.commit()


    # --------------------------------------------------------
    # CREATE / UPDATE EXACT 25 PRODUCTS
    # --------------------------------------------------------

    for name, category, price, image in DEMO_PRODUCTS:

        product = Product.query.filter_by(
            name=name,
            farmer_id=farmer.id
        ).first()


        if not product:

            product = Product(
                name=name,
                category=category,
                price=price,
                quantity=1000,
                description=(
                    f"[FARMCONNECT_DEMO] "
                    f"Fresh {name} directly from farmers."
                ),
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

            if not product.description:

                product.description = (
                    f"[FARMCONNECT_DEMO] "
                    f"Fresh {name} directly from farmers."
                )


    db.session.commit()


# ============================================================
# SALES HISTORY
# ============================================================

def seed_sales_history():

    products = Product.query.all()

    today = datetime.utcnow().date()


    category_base = {

        "Vegetables": 35,
        "Fruits": 28,
        "Grains": 20,
        "Spices": 12,
        "Dairy": 30,
        "Pulses": 18,
        "Other": 20

    }


    for product in products:

        exists = SalesHistory.query.filter_by(
            product_id=product.id
        ).first()

        if exists:
            continue


        base = category_base.get(
            product.category,
            20
        )


        factor = (
            1 +
            ((product.id % 5) * 0.08)
        )


        for days_ago in range(
            89,
            -1,
            -1
        ):

            current_date = (
                today -
                timedelta(days=days_ago)
            )


            weekend = (
                1.12
                if current_date.weekday() in [5, 6]
                else 1
            )


            trend = (
                1 +
                ((90 - days_ago) / 90)
                * 0.18
            )


            random.seed(
                product.id * 1000 +
                days_ago
            )


            noise = random.uniform(
                0.82,
                1.18
            )


            quantity = max(

                1,

                round(
                    base *
                    factor *
                    weekend *
                    trend *
                    noise,
                    1
                )

            )


            db.session.add(

                SalesHistory(
                    product_id=product.id,
                    date=current_date,
                    quantity_sold=quantity
                )

            )


    db.session.commit()


# ============================================================
# DEMAND FORECAST
# ============================================================

def build_demand_forecasts(products):

    forecasts = []


    today = datetime.utcnow().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )


    start_date = (
        today -
        timedelta(days=27)
    )


    for product in products:

        daily_sales = {}


        for i in range(28):

            day = (
                start_date +
                timedelta(days=i)
            ).date()

            daily_sales[day] = 0


        real_orders = Order.query.filter(

            Order.product_id == product.id,

            Order.created_at >= start_date

        ).order_by(
            Order.created_at.asc()
        ).all()


        for order in real_orders:

            day = order.created_at.date()

            if day in daily_sales:

                daily_sales[day] += order.quantity


        real_total = sum(
            daily_sales.values()
        )


        if real_total > 0:

            values = list(
                daily_sales.values()
            )

            data_source = (
                "Based on real FarmConnect orders"
            )

        else:

            history = SalesHistory.query.filter_by(

                product_id=product.id

            ).order_by(
                SalesHistory.date.asc()
            ).all()


            if not history:
                continue


            values = [
                item.quantity_sold
                for item in history[-28:]
            ]

            data_source = (
                "Demo historical sales data"
            )


        recent = values[-7:]

        previous = values[-14:-7]


        if not previous:

            previous = values


        recent_avg = (
            sum(recent) / len(recent)
            if recent
            else 0
        )


        previous_avg = (
            sum(previous) / len(previous)
            if previous
            else 0
        )


        if previous_avg > 0:

            trend_pct = (

                (
                    recent_avg -
                    previous_avg
                )
                /
                previous_avg
            ) * 100

        else:

            trend_pct = 0


        factor = max(
            0.70,
            min(
                1.30,
                1 + (
                    trend_pct /
                    100 *
                    0.50
                )
            )
        )


        predicted_daily = max(
            1,
            recent_avg * factor
        )


        predicted_7 = max(
            1,
            round(
                predicted_daily * 7,
                1
            )
        )


        if trend_pct >= 10:

            trend = "Increasing"
            trend_icon = "📈"

        elif trend_pct <= -10:

            trend = "Decreasing"
            trend_icon = "📉"

        else:

            trend = "Stable"
            trend_icon = "➡️"


        if trend_pct >= 15:

            demand_level = "High Demand"
            demand_icon = "🔥"

        elif trend_pct >= 5:

            demand_level = "Growing Demand"
            demand_icon = "📈"

        elif trend_pct <= -15:

            demand_level = "Low Demand"
            demand_icon = "📉"

        else:

            demand_level = "Stable Demand"
            demand_icon = "➡️"


        coverage = (
            product.quantity /
            predicted_daily
            if predicted_daily > 0
            else 0
        )


        if coverage < 3:

            action = (
                "Demand is strong compared "
                "with current stock. "
                "Consider increasing supply."
            )

        elif coverage > 14:

            action = (
                "Current stock is high compared "
                "with forecast demand. "
                "Avoid overproduction."
            )

        elif trend == "Increasing":

            action = (
                "Customer demand is increasing. "
                "Keep sufficient stock available."
            )

        elif trend == "Decreasing":

            action = (
                "Customer demand is decreasing. "
                "Monitor sales before increasing supply."
            )

        else:

            action = (
                "Demand is stable. "
                "Current stock can be monitored normally."
            )


        forecasts.append({

            "product": product,

            "predicted_7": predicted_7,

            "predicted_daily": round(
                predicted_daily,
                1
            ),

            "recent_avg": round(
                recent_avg,
                1
            ),

            "previous_avg": round(
                previous_avg,
                1
            ),

            "trend_pct": round(
                trend_pct,
                1
            ),

            "trend": trend,

            "trend_icon": trend_icon,

            "demand_level": demand_level,

            "demand_icon": demand_icon,

            "coverage": round(
                coverage,
                1
            ),

            "total_sales_28": round(
                real_total,
                1
            ),

            "data_source": data_source,

            "action": action

        })


    return forecasts


# ============================================================
# GLOBAL VALUES
# ============================================================

@app.context_processor
def inject_global_values():

    cart_count = 0


    if "user_id" in session:

        cart_items = CartItem.query.filter_by(
            buyer_id=session["user_id"]
        ).all()


        cart_count = sum(
            item.quantity
            for item in cart_items
        )


    return {

        "cart_count": int(cart_count),

        "delivery_charge": 40

    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    products = Product.query.filter(
        Product.quantity > 0
    ).order_by(
        Product.created_at.desc()
    ).limit(8).all()


    return render_template(
        "index.html",
        products=products
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        role = request.form.get(
            "role",
            "buyer"
        ).strip().lower()


        phone = request.form.get(
            "phone",
            ""
        ).strip()


        location = request.form.get(
            "location",
            ""
        ).strip()


        if role not in [
            "buyer",
            "farmer"
        ]:

            role = "buyer"


        if not name or not email or not password:

            flash(
                "Please fill all required fields."
            )

            return redirect(
                url_for("register")
            )


        if User.query.filter_by(
            email=email
        ).first():

            flash(
                "Email already registered. Please login."
            )

            return redirect(
                url_for("login")
            )


        user = User(

            name=name,

            email=email,

            password=generate_password_hash(
                password
            ),

            role=role,

            phone=phone,

            location=location

        )


        db.session.add(user)

        db.session.commit()


        flash(
            "Account created successfully. Please login."
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        user = User.query.filter_by(
            email=email
        ).first()


        if (
            user
            and check_password_hash(
                user.password,
                password
            )
        ):

            session["user_id"] = user.id

            session["user_name"] = user.name

            session["role"] = user.role


            return redirect(
                url_for("dashboard")
            )


        flash(
            "Invalid email or password."
        )


    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    user = get_current_user()


    if not user:

        session.clear()

        return redirect(
            url_for("login")
        )


    if user.role == "farmer":

        products = Product.query.filter_by(

            farmer_id=user.id

        ).order_by(
            Product.created_at.desc()
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


        seed_sales_history()


        forecasts = build_demand_forecasts(
            products
        )


        return render_template(

            "farmer_dashboard.html",

            user=user,

            products=products,

            orders=orders,

            forecasts=forecasts

        )


    orders = Order.query.filter_by(

        buyer_id=user.id

    ).order_by(
        Order.created_at.desc()
    ).all()


    cart_items = CartItem.query.filter_by(
        buyer_id=user.id
    ).all()


    return render_template(

        "buyer_dashboard.html",

        user=user,

        orders=orders,

        cart_items=cart_items

    )


# ============================================================
# MARKETPLACE
# ============================================================

@app.route("/marketplace")
def marketplace():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    if user.role != "buyer":
        flash("Marketplace shopping is available for buyers.")
        return redirect(url_for("dashboard"))

    search_value = request.args.get("search", "").strip()
    category_value = request.args.get("category", "").strip()

    official_names = {item[0] for item in DEMO_PRODUCTS}
    official_order = {item[0]: index for index, item in enumerate(DEMO_PRODUCTS)}
    category_order = {"Vegetables": 1, "Fruits": 2, "Grains": 3, "Spices": 4, "Dairy": 5}

    query = Product.query.filter(Product.quantity > 0, Product.name.in_(official_names))
    if search_value:
        query = query.filter(Product.name.ilike(f"%{search_value}%"))
    if category_value:
        query = query.filter(Product.category == category_value)

    all_products = query.all()
    demo_farmer = User.query.filter_by(email="demo_farmer@farmconnect.com").first()
    demo_farmer_id = demo_farmer.id if demo_farmer else None
    selected = {}

    for product in all_products:
        name = product.name
        if name not in selected:
            selected[name] = product
            continue
        current = selected[name]
        if product.farmer_id == demo_farmer_id and current.farmer_id != demo_farmer_id:
            selected[name] = product

    products = list(selected.values())
    products.sort(key=lambda p: (category_order.get(p.category, 99), official_order.get(p.name, 999)))
    farmers = {product.farmer_id: product.farmer for product in products}

    return render_template("marketplace.html", products=products, farmers=farmers, search=search_value, category=category_value)

# ============================================================
# ADD PRODUCT
# ============================================================

@app.route(
    "/add-product",
    methods=["GET", "POST"]
)
def add_product():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "farmer":

        flash(
            "Only farmers can add products."
        )

        return redirect(
            url_for("dashboard")
        )


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        category = request.form.get(
            "category",
            ""
        ).strip()


        description = request.form.get(
            "description",
            ""
        ).strip()


        image = request.form.get(
            "image",
            ""
        ).strip()


        try:

            price = float(
                request.form.get(
                    "price",
                    0
                )
            )

            quantity = float(
                request.form.get(
                    "quantity",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            flash(
                "Enter valid price and quantity."
            )

            return redirect(
                url_for("add_product")
            )


        if not name or not category:

            flash(
                "Product name and category are required."
            )

            return redirect(
                url_for("add_product")
            )


        if price < 0 or quantity < 0:

            flash(
                "Price and quantity cannot be negative."
            )

            return redirect(
                url_for("add_product")
            )


        product = Product(

            name=name,

            category=category,

            price=price,

            quantity=quantity,

            description=description,

            image=image,

            farmer_id=user.id

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
        "add_product.html",
        user=user
    )


# ============================================================
# EDIT PRODUCT
# ============================================================
@app.route(
    "/edit-product/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    product = Product.query.get_or_404(
        product_id
    )


    if (
        user.role != "farmer"
        or product.farmer_id != user.id
    ):

        flash(
            "You are not allowed to edit this product."
        )

        return redirect(
            url_for("dashboard")
        )


    if request.method == "POST":

        product.name = request.form.get(
            "name",
            ""
        ).strip()


        product.category = request.form.get(
            "category",
            ""
        ).strip()


        product.description = request.form.get(
            "description",
            ""
        ).strip()


        product.image = request.form.get(
            "image",
            ""
        ).strip()


        try:

            product.price = float(
                request.form.get(
                    "price",
                    product.price
                )
            )

            product.quantity = float(
                request.form.get(
                    "quantity",
                    product.quantity
                )
            )

        except (
            TypeError,
            ValueError
        ):

            flash(
                "Enter valid price and quantity."
            )

            return redirect(
                url_for(
                    "edit_product",
                    product_id=product.id
                )
            )


        if (
            not product.name
            or not product.category
        ):

            flash(
                "Product name and category are required."
            )

            return redirect(
                url_for(
                    "edit_product",
                    product_id=product.id
                )
            )


        if (
            product.price < 0
            or product.quantity < 0
        ):

            flash(
                "Price and quantity cannot be negative."
            )

            return redirect(
                url_for(
                    "edit_product",
                    product_id=product.id
                )
            )


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


# ============================================================
# DELETE PRODUCT
# ============================================================

@app.route(
    "/delete-product/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    product = Product.query.get_or_404(
        product_id
    )


    if (
        user.role != "farmer"
        or product.farmer_id != user.id
    ):

        flash(
            "You cannot delete this product."
        )

        return redirect(
            url_for("dashboard")
        )


    if Order.query.filter_by(
        product_id=product.id
    ).first():

        product.quantity = 0

        db.session.commit()


        flash(
            "Product marked unavailable because it has previous orders."
        )


    else:

        CartItem.query.filter_by(
            product_id=product.id
        ).delete(
            synchronize_session=False
        )


        Review.query.filter_by(
            product_id=product.id
        ).delete(
            synchronize_session=False
        )


        SalesHistory.query.filter_by(
            product_id=product.id
        ).delete(
            synchronize_session=False
        )


        db.session.delete(product)

        db.session.commit()


        flash(
            "Product deleted successfully. 🗑️"
        )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# ADD TO CART
# ============================================================

@app.route(
    "/add-to-cart/<int:product_id>",
    methods=["POST"]
)
def add_to_cart(product_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "buyer":

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


    try:

        requested_quantity = float(
            request.form.get(
                "quantity",
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):

        requested_quantity = 1


    requested_quantity = max(
        0.1,
        requested_quantity
    )


    item = CartItem.query.filter_by(

        buyer_id=user.id,

        product_id=product.id

    ).first()


    current_quantity = (
        item.quantity
        if item
        else 0
    )


    new_quantity = (
        current_quantity +
        requested_quantity
    )


    if new_quantity > product.quantity:

        flash(
            "Not enough stock available."
        )

        return redirect(
            url_for("marketplace")
        )


    if item:

        item.quantity = new_quantity

    else:

        item = CartItem(

            buyer_id=user.id,

            product_id=product.id,

            quantity=requested_quantity

        )

        db.session.add(item)


    db.session.commit()


    flash(
        f"{product.name} added to cart 🛒"
    )


    return redirect(
        url_for("marketplace")
    )


# ============================================================
# CART
# ============================================================

@app.route("/cart")
def cart():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "buyer":

        return redirect(
            url_for("dashboard")
        )


    cart_items = CartItem.query.filter_by(

        buyer_id=user.id

    ).all()


    subtotal = sum(

        item.product.price *
        item.quantity

        for item in cart_items

    )


    delivery = (

        0

        if subtotal == 0
        or subtotal >= 500

        else 40

    )


    total = (
        subtotal +
        delivery
    )


    return render_template(

        "cart.html",

        cart_items=cart_items,

        subtotal=subtotal,

        delivery=delivery,

        delivery_charge=delivery,

        total=total

    )


# ============================================================
# UPDATE CART
# ============================================================

@app.route(
    "/cart/update/<int:item_id>",
    methods=["POST"]
)
def update_cart(item_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    item = CartItem.query.filter_by(

        id=item_id,

        buyer_id=user.id

    ).first_or_404()


    try:

        quantity = float(
            request.form.get(
                "quantity",
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):

        quantity = 1


    if quantity <= 0:

        db.session.delete(item)


    elif quantity > item.product.quantity:

        flash(
            "Requested quantity is greater than available stock."
        )

        return redirect(
            url_for("cart")
        )


    else:

        item.quantity = quantity


    db.session.commit()


    return redirect(
        url_for("cart")
    )


# ============================================================
# REMOVE CART ITEM
# ============================================================

@app.route(
    "/cart/remove/<int:item_id>",
    methods=["POST"]
)
def remove_from_cart(item_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    item = CartItem.query.filter_by(

        id=item_id,

        buyer_id=user.id

    ).first_or_404()


    db.session.delete(item)

    db.session.commit()


    flash(
        "Item removed from cart."
    )


    return redirect(
        url_for("cart")
    )


# ============================================================
# CLEAR CART
# ============================================================

@app.route(
    "/cart/clear",
    methods=["POST"]
)
def clear_cart():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "buyer":

        return redirect(
            url_for("dashboard")
        )


    CartItem.query.filter_by(

        buyer_id=user.id

    ).delete(
        synchronize_session=False
    )


    db.session.commit()


    flash(
        "Cart cleared successfully."
    )


    return redirect(
        url_for("cart")
    )


# ============================================================
# CHECKOUT
# ============================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "buyer":

        return redirect(
            url_for("dashboard")
        )


    cart_items = CartItem.query.filter_by(

        buyer_id=user.id

    ).all()


    if not cart_items:

        flash(
            "Your cart is empty."
        )

        return redirect(
            url_for("marketplace")
        )


    subtotal = sum(

        item.product.price *
        item.quantity

        for item in cart_items

    )


    delivery = (
        0
        if subtotal >= 500
        else 40
    )


    total = (
        subtotal +
        delivery
    )


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
                "Please enter delivery address."
            )

            return redirect(
                url_for("checkout")
            )


        for item in cart_items:

            if item.quantity > item.product.quantity:

                flash(
                    f"Not enough stock for "
                    f"{item.product.name}."
                )

                return redirect(
                    url_for("cart")
                )


        for item in cart_items:

            order = Order(

                buyer_id=user.id,

                product_id=item.product_id,

                quantity=item.quantity,

                total_price=(
                    item.product.price *
                    item.quantity
                ),

                status="Order Placed",

                delivery_address=address

            )


            item.product.quantity -= (
                item.quantity
            )


            db.session.add(order)

            db.session.delete(item)


        db.session.commit()


        flash(
            "Order placed successfully! "
            f"Payment: {payment_method}"
        )


        return redirect(
            url_for("my_orders")
        )


    return render_template(

        "checkout.html",

        user=user,

        cart_items=cart_items,

        subtotal=subtotal,

        delivery=delivery,

        total=total

    )


# ============================================================
# MY ORDERS
# ============================================================

@app.route("/buyer/orders")
def my_orders():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "buyer":

        return redirect(
            url_for("dashboard")
        )


    orders = Order.query.filter_by(

        buyer_id=user.id

    ).order_by(
        Order.created_at.desc()
    ).all()


    return render_template(

        "my_orders.html",

        user=user,

        orders=orders

    )


@app.route("/orders")
def buyer_orders():

    return redirect(
        url_for("my_orders")
    )


# ============================================================
# FARMER ORDERS
# ============================================================

@app.route("/farmer/orders")
def farmer_orders():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "farmer":

        flash(
            "Only farmers can access orders."
        )

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
            Product.farmer_id == user.id
        )

        .order_by(
            Order.created_at.desc()
        )

        .all()

    )


    return render_template(

        "farmer_orders.html",

        user=user,

        orders=orders

    )


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/farmer/orders/<int:order_id>/status",
    methods=["POST"]
)
def update_order_status(order_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "farmer":

        return redirect(
            url_for("dashboard")
        )


    order = Order.query.get_or_404(
        order_id
    )


    if order.product.farmer_id != user.id:

        flash(
            "You cannot update this order."
        )

        return redirect(
            url_for("farmer_orders")
        )


    allowed = [

        "Order Placed",
        "Confirmed",
        "Processing",
        "Packed",
        "Shipped",
        "Delivered",
        "Cancelled"

    ]


    status = request.form.get(
        "status",
        ""
    ).strip()


    if status not in allowed:

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


# ============================================================
# AI ROUTE OPTIMIZATION
# ============================================================

@app.route("/route-optimization")
def route_optimization():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    if user.role != "farmer":

        flash(
            "Only farmers can access route optimization."
        )

        return redirect(
            url_for("dashboard")
        )

    active_orders = (

        Order.query

        .join(
            Product,
            Order.product_id == Product.id
        )

        .filter(
            Product.farmer_id == user.id
        )

        .filter(
            Order.status.notin_([
                "Delivered",
                "Cancelled"
            ])
        )

        .order_by(
            Order.created_at.asc()
        )

        .all()

    )

    orders = []

    for order in active_orders:

        address = (
            order.delivery_address
            or order.buyer.location
            or "Hyderabad"
        )

        orders.append({

            "order_no": f"FC{order.id:05d}",

            "buyer_name": order.buyer.name,

            "product_name": order.product.name,

            "quantity": order.quantity,

            "address": address,

            "status": order.status

        })

    farmer_location = (
        user.location
        or "Hyderabad"
    )

    return render_template(

        "route_optimization.html",

        user=user,

        orders=orders,

        farmer_location=farmer_location

    )


# ============================================================
# PRODUCT DETAILS
# ============================================================

@app.route(
    "/product/<int:product_id>"
)
def product_details(product_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    product = Product.query.get_or_404(
        product_id
    )


    reviews = Review.query.filter_by(

        product_id=product.id

    ).order_by(
        Review.created_at.desc()
    ).all()


    average_rating = (

        sum(
            review.rating
            for review in reviews
        )
        /
        len(reviews)

        if reviews

        else 0

    )


    farmer = db.session.get(
        User,
        product.farmer_id
    )


    return render_template(

        "product_details.html",

        product=product,

        farmer=farmer,

        reviews=reviews,

        average_rating=average_rating

    )


# ============================================================
# ADD REVIEW
# ============================================================

@app.route(
    "/product/<int:product_id>/review",
    methods=["POST"]
)
def add_review(product_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    if user.role != "buyer":

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

        buyer_id=user.id,

        product_id=product.id

    ).first()


    if not purchased:

        flash(
            "You can review after purchasing."
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
        min(
            5,
            rating
        )
    )


    comment = request.form.get(
        "comment",
        ""
    ).strip()


    if not comment:

        flash(
            "Please write a review."
        )

        return redirect(
            url_for(
                "product_details",
                product_id=product.id
            )
        )


    existing = Review.query.filter_by(

        buyer_id=user.id,

        product_id=product.id

    ).first()


    if existing:

        existing.rating = rating

        existing.comment = comment

        existing.created_at = datetime.utcnow()

    else:

        db.session.add(

            Review(

                buyer_id=user.id,

                product_id=product.id,

                rating=rating,

                comment=comment

            )

        )


    db.session.commit()


    flash(
        "Review saved successfully. ⭐"
    )


    return redirect(
        url_for(
            "product_details",
            product_id=product.id
        )
    )


# ============================================================
# SEARCH
# ============================================================

@app.route("/search")
def search():

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    search_value = request.args.get(
        "q",
        ""
    ).strip()


    query = Product.query.filter(
        Product.quantity > 0
    )


    if search_value:

        query = query.filter(
            Product.name.ilike(
                f"%{search_value}%"
            )
        )


    products = query.order_by(
        Product.name.asc()
    ).all()


    farmers = {

        product.farmer_id:
        product.farmer

        for product in products

    }


    return render_template(

        "marketplace.html",

        products=products,

        farmers=farmers,

        search=search_value,

        category=""

    )


# ============================================================
# FARMER PROFILE
# ============================================================

@app.route(
    "/farmer/<int:farmer_id>"
)
def farmer_profile(farmer_id):

    user = get_current_user()


    if not user:

        return redirect(
            url_for("login")
        )


    farmer = User.query.get_or_404(
        farmer_id
    )


    products = Product.query.filter(

        Product.farmer_id == farmer.id,

        Product.quantity > 0

    ).order_by(
        Product.name.asc()
    ).all()


    farmers = {
        farmer.id: farmer
    }


    return render_template(

        "marketplace.html",

        products=products,

        farmers=farmers,

        search="",

        category=""

    )


# ============================================================
# ERROR 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """

    <div style="
        font-family:Arial;
        text-align:center;
        padding:80px;
    ">

        <h1>404</h1>

        <h2>Page Not Found</h2>

        <p>
            The requested FarmConnect page does not exist.
        </p>

        <br>

        <a
            href="/"
            style="
                color:#16a34a;
                font-weight:bold;
            "
        >
            ← Go Home
        </a>

    </div>

    """, 404


# ============================================================
# ERROR 500
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()


    return """

    <div style="
        font-family:Arial;
        text-align:center;
        padding:80px;
    ">

        <h1>500</h1>

        <h2>FarmConnect Server Error</h2>

        <p>
            Something went wrong on the server.
        </p>

        <br>

        <a
            href="/"
            style="
                color:#16a34a;
                font-weight:bold;
            "
        >
            ← Go Home
        </a>

    </div>

    """, 500


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def migrate_order_delivery_address():

    inspector = inspect(db.engine)

    columns = [
        column["name"]
        for column in inspector.get_columns("order")
    ]

    if "delivery_address" not in columns:

        with db.engine.begin() as connection:

            connection.execute(
                text(
                    'ALTER TABLE "order" ADD COLUMN delivery_address TEXT'
                )
            )


with app.app_context():

    db.create_all()

    migrate_order_delivery_address()

    seed_demo_products()

    seed_sales_history()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )


