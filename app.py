from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sports_club.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(40), nullable=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(100), default="sports_logo.svg")


class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(40), default="Pending")
    creator = db.relationship("User")


class PurchaseOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_order.id"))
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"))
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship("PurchaseOrder", backref="order_items")
    item = db.relationship("Item")


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    team = db.relationship("Team")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_data():
    if User.query.count() == 0:
        db.session.add_all([
            User(username="admin", password="password", role="admin"),
            User(username="coach1", password="password", role="coach"),
            User(username="manager1", password="password", role="inventory_manager"),
            User(username="player1", password="password", role="player"),
        ])

    if Item.query.count() == 0:
        db.session.add_all([
            Item(name="Football", category="Equipment", quantity=20, price=15.00, image="football.svg"),
            Item(name="Jersey", category="Clothing", quantity=30, price=25.00, image="jersey.svg"),
            Item(name="Training Cones", category="Equipment", quantity=50, price=2.50, image="cones.svg"),
            Item(name="Goalkeeper Gloves", category="Equipment", quantity=10, price=35.00, image="gloves.svg"),
            Item(name="Water Bottles", category="Accessories", quantity=40, price=5.00, image="bottles.svg"),
            Item(name="Basketball", category="Equipment", quantity=15, price=18.00, image="football.svg"),
            Item(name="First Aid Kit", category="Medical", quantity=8, price=30.00, image="sports_logo.svg"),
            Item(name="Whistle", category="Coaching", quantity=25, price=4.00, image="sports_logo.svg"),
            Item(name="Training Bibs", category="Clothing", quantity=35, price=7.00, image="jersey.svg"),
            Item(name="Agility Ladder", category="Training", quantity=12, price=22.00, image="cones.svg"),
        ])

    if Team.query.count() == 0:
        team1 = Team(name="Senior Team")
        team2 = Team(name="Under 21 Team")
        db.session.add_all([team1, team2])
        db.session.flush()

        db.session.add_all([
            Player(name="John Murphy", position="Forward", team_id=team1.id),
            Player(name="Adam Byrne", position="Midfielder", team_id=team1.id),
            Player(name="Liam Kelly", position="Defender", team_id=team2.id),
            Player(name="Sean O'Brien", position="Goalkeeper", team_id=team2.id),
        ])

    db.session.commit()


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        item_count=Item.query.count(),
        order_count=PurchaseOrder.query.count(),
        player_count=Player.query.count()
    )


@app.route("/items")
@login_required
def items():
    return render_template("items.html", items=Item.query.all())


@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html", orders=PurchaseOrder.query.all())


@app.route("/create-order", methods=["GET", "POST"])
@login_required
def create_order():
    items = Item.query.all()

    if request.method == "POST":
        quantity = int(request.form["quantity"])

        if quantity <= 0:
            flash("Quantity must be greater than zero")
            return redirect(url_for("create_order"))

        order = PurchaseOrder(created_by=current_user.id, status="Pending")
        db.session.add(order)
        db.session.flush()

        order_item = PurchaseOrderItem(
            purchase_order_id=order.id,
            item_id=int(request.form["item_id"]),
            quantity=quantity
        )

        db.session.add(order_item)
        db.session.commit()

        flash("Purchase order created successfully")
        return redirect(url_for("orders"))

    return render_template("create_order.html", items=items)


@app.route("/approve-order/<int:order_id>")
@login_required
def approve_order(order_id):
    if current_user.role not in ["admin", "inventory_manager"]:
        flash("You do not have permission to approve orders")
        return redirect(url_for("orders"))

    order = PurchaseOrder.query.get_or_404(order_id)

    if order.status != "Pending":
        flash("Only pending orders can be approved")
        return redirect(url_for("orders"))

    order.status = "Approved"

    for order_item in order.order_items:
        order_item.item.quantity += order_item.quantity

    db.session.commit()
    flash("Order approved and inventory updated")
    return redirect(url_for("orders"))


@app.route("/reject-order/<int:order_id>")
@login_required
def reject_order(order_id):
    if current_user.role not in ["admin", "inventory_manager"]:
        flash("You do not have permission to reject orders")
        return redirect(url_for("orders"))

    order = PurchaseOrder.query.get_or_404(order_id)
    order.status = "Rejected"
    db.session.commit()

    flash("Order rejected")
    return redirect(url_for("orders"))


@app.route("/players")
@login_required
def players():
    return render_template("players.html", players=Player.query.all())


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()

    app.run(debug=True)