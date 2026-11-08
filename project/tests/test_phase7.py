from decimal import Decimal
from pathlib import Path

import pytest

from app.services.order_service import calculate_total, calculate_totals


def login(client, email="sales@example.com"):
    response = client.post(
        "/api/login",
        json={"email": email, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200


def create_order(client, items, discount=0):
    return client.post(
        "/api/orders",
        json={
            "customer_id": 1,
            "items": items,
            "discount_percent": discount,
        },
    )


def test_calculate_totals_for_multiple_items():
    items = [
        {"unit_price": Decimal("100.00"), "quantity": 1},
        {"unit_price": Decimal("250.00"), "quantity": 1},
    ]
    subtotal, _, total = calculate_totals(items)
    assert subtotal == Decimal("350.00")
    assert total == Decimal("350.00")


def test_debug_calculate_total_example():
    assert calculate_total([
        {"qty": 2, "rate": 100},
        {"qty": 3, "rate": 50},
    ]) == Decimal("350.00")


def test_calculate_totals_for_empty_list():
    assert calculate_totals([]) == (Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))


@pytest.mark.parametrize("item", [{"quantity": 1}, {"unit_price": 10}])
def test_calculate_totals_rejects_missing_quantity_or_rate(item):
    with pytest.raises(ValueError):
        calculate_totals([item])


@pytest.mark.parametrize("quantity", [0, -1])
def test_calculate_totals_rejects_zero_or_negative_quantity(quantity):
    with pytest.raises(ValueError):
        calculate_totals([{"unit_price": 10, "quantity": quantity}])


def test_calculate_totals_rejects_negative_rate():
    with pytest.raises(ValueError):
        calculate_totals([{"unit_price": -1, "quantity": 1}])


def test_order_totals_include_discount(client):
    login(client)
    response = create_order(
        client,
        [{"product_id": 1, "quantity": 1}, {"product_id": 2, "quantity": 1}],
        discount=10,
    )
    assert response.status_code == 201

    order = client.get(f"/api/orders/{response.json()['id']}").json()
    assert Decimal(str(order["subtotal"])) == Decimal("350.00")
    assert Decimal(str(order["discount_amount"])) == Decimal("35.00")
    assert Decimal(str(order["total"])) == Decimal("315.00")


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_rejects_zero_or_negative_quantity(client, quantity):
    login(client)
    response = create_order(client, [{"product_id": 1, "quantity": quantity}])
    assert response.status_code == 422


@pytest.mark.parametrize("discount", [-1, 21])
def test_order_rejects_discount_outside_range(client, discount):
    login(client)
    response = create_order(client, [{"product_id": 1, "quantity": 1}], discount)
    assert response.status_code == 422


def test_confirm_deducts_stock_and_logs_movement(client, db):
    login(client)
    response = create_order(client, [{"product_id": 1, "quantity": 2}])
    order_id = response.json()["id"]

    result = client.post(f"/api/orders/{order_id}/confirm")
    assert result.status_code == 200

    with db.cursor() as cur:
        cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
        assert cur.fetchone()["stock_quantity"] == 8
        cur.execute("SELECT status FROM sales_orders WHERE id = %s", (order_id,))
        assert cur.fetchone()["status"] == "confirmed"
        cur.execute("SELECT quantity_change FROM stock_movements WHERE sales_order_id = %s", (order_id,))
        assert cur.fetchall() == [{"quantity_change": -2}]


def test_confirm_with_not_enough_stock_changes_nothing(client, db):
    with db.cursor() as cur:
        cur.execute("UPDATE products SET stock_quantity = 1 WHERE id = 1")
    db.commit()

    login(client)
    response = create_order(client, [{"product_id": 1, "quantity": 2}])
    order_id = response.json()["id"]
    result = client.post(f"/api/orders/{order_id}/confirm")

    assert result.status_code == 409
    with db.cursor() as cur:
        cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
        assert cur.fetchone()["stock_quantity"] == 1
        cur.execute("SELECT status FROM sales_orders WHERE id = %s", (order_id,))
        assert cur.fetchone()["status"] == "draft"
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements")
        assert cur.fetchone()["count"] == 0


def test_repeated_confirm_deducts_stock_once(client, db):
    login(client)
    order_id = create_order(client, [{"product_id": 1, "quantity": 2}]).json()["id"]
    client.post(f"/api/orders/{order_id}/confirm")
    client.post(f"/api/orders/{order_id}/confirm")

    with db.cursor() as cur:
        cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
        assert cur.fetchone()["stock_quantity"] == 8
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements WHERE sales_order_id = %s", (order_id,))
        assert cur.fetchone()["count"] == 1


def test_cancel_confirmed_order_restores_stock_once(client, db):
    login(client)
    order_id = create_order(client, [{"product_id": 1, "quantity": 2}]).json()["id"]
    client.post(f"/api/orders/{order_id}/confirm")
    client.post(f"/api/orders/{order_id}/cancel")
    client.post(f"/api/orders/{order_id}/cancel")

    with db.cursor() as cur:
        cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
        assert cur.fetchone()["stock_quantity"] == 10
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements WHERE sales_order_id = %s", (order_id,))
        assert cur.fetchone()["count"] == 2


def test_sales_user_cannot_open_another_users_order(client, db):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO sales_orders "
            "(order_number, customer_id, created_by, status, discount_percent, subtotal, discount_amount, total) "
            "VALUES ('SO-OTHER00001', 1, 3, 'draft', 0, 100, 0, 100)"
        )
        other_order_id = cur.lastrowid
        cur.execute(
            "INSERT INTO sales_order_items "
            "(sales_order_id, product_id, quantity, unit_price, line_total) "
            "VALUES (%s, 1, 1, 100, 100)",
            (other_order_id,),
        )
    db.commit()

    login(client)
    response = client.get(f"/api/orders/{other_order_id}")
    assert response.status_code == 404


def test_sales_user_only_sees_active_master_data_and_cannot_change_it(client, db):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (customer_name, email, is_active) "
            "VALUES ('Inactive Customer', 'inactive@example.com', 0)"
        )
        cur.execute(
            "INSERT INTO products "
            "(sku, product_name, category, unit_price, stock_quantity, is_active) "
            "VALUES ('INACTIVE', 'Inactive Product', 'Test', 1, 1, 0)"
        )
    db.commit()

    login(client)
    customers = client.get("/api/customers").json()
    products = client.get("/api/products?limit=100").json()["items"]
    assert all(customer["is_active"] for customer in customers)
    assert all(product["is_active"] for product in products)

    customer_response = client.post(
        "/api/customers",
        json={"name": "New", "email": "new@example.com", "mobile": "555", "city": "Town"},
    )
    product_response = client.post(
        "/api/products",
        json={"product_code": "NEW", "name": "New", "category": "Test",
              "price": 1, "stock_quantity": 1},
    )
    assert customer_response.status_code == 403
    assert product_response.status_code == 403

    assert client.put("/api/customers/1", json={
        "name": "Changed", "email": "customer@example.com", "mobile": "5550100",
        "city": "Test City", "is_active": True,
    }).status_code == 403
    assert client.delete("/api/customers/1").status_code == 403
    assert client.put("/api/products/1", json={
        "product_code": "P-100", "name": "Changed", "category": "Test",
        "price": 100, "stock_quantity": 10, "is_active": True,
    }).status_code == 403
    assert client.delete("/api/products/1").status_code == 403
    assert client.post("/api/products/1/stock-adjustments", json={
        "quantity_change": 1, "reason": "test",
    }).status_code == 403


def test_invalid_csv_import_adds_nothing(client, db):
    login(client, "admin@example.com")
    csv_path = Path("sample_data/products_invalid.csv")
    with csv_path.open("rb") as csv_file:
        response = client.post(
            "/api/products/import-csv",
            files={"file": (csv_path.name, csv_file, "text/csv")},
        )

    assert response.status_code == 400
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM products")
        assert cur.fetchone()["count"] == 2
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements")
        assert cur.fetchone()["count"] == 0
