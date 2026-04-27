import pytest
from app import app, db, User, Item


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(username="coach1", password="password", role="coach")
        manager = User(username="manager1", password="password", role="inventory_manager")
        item = Item(name="Football", category="Equipment", quantity=10, price=15.0)

        db.session.add_all([user, manager, item])
        db.session.commit()

    return app.test_client()


def login(client, username="coach1", password="password"):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password
        },
        follow_redirects=True
    )


def test_login(client):
    response = login(client)
    assert b"Dashboard" in response.data


def test_items_page(client):
    login(client)
    response = client.get("/items")
    assert b"Football" in response.data


def test_create_purchase_order(client):
    login(client)

    response = client.post(
        "/create-order",
        data={
            "item_id": 1,
            "quantity": 5
        },
        follow_redirects=True
    )

    assert b"Purchase order created successfully" in response.data


def test_unauthorised_approval_blocked(client):
    login(client, "coach1", "password")

    client.post(
        "/create-order",
        data={
            "item_id": 1,
            "quantity": 5
        },
        follow_redirects=True
    )

    response = client.get("/approve-order/1", follow_redirects=True)

    assert b"You do not have permission" in response.data


def test_manager_can_approve_order(client):
    login(client, "coach1", "password")

    client.post(
        "/create-order",
        data={
            "item_id": 1,
            "quantity": 5
        },
        follow_redirects=True
    )

    client.get("/logout")

    login(client, "manager1", "password")

    response = client.get("/approve-order/1", follow_redirects=True)

    assert b"Order approved and inventory updated" in response.data