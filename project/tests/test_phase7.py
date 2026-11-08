from decimal import Decimal
from pathlib import Path

import pytest

from app.services.order_service import calculate_totals


def login(client, email="sales@example.com"):
    response = client.post(
        "/api/login",
        json={"email": email, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200


def create_order(client, items, discount=0):
    return client.post(
        "/orders",
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
    subtotal, total = calculate_totals(items)
    assert subtotal == Decimal("350.00")
    assert total == Decimal("350.00")


def test_calculate_totals_for_empty_list():
    assert calculate_totals([]) == (Decimal("0.00"), Decimal("0.00"))


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
    assert response.status_code == 200

    order = client.get(f"/orders/{response.json()['id']}").json()
    assert Decimal(str(order["subtotal"])) == Decimal("350.00")
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

    result = client.post(f"/orders/{order_id}/confirm")
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
    result = client.post(f"/orders/{order_id}/confirm")

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
    client.post(f"/orders/{order_id}/confirm")
    client.post(f"/orders/{order_id}/confirm")

    with db.cursor() as cur:
        cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
        assert cur.fetchone()["stock_quantity"] == 8
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements WHERE sales_order_id = %s", (order_id,))
        assert cur.fetchone()["count"] == 1


def test_cancel_confirmed_order_restores_stock_once(client, db):
    login(client)
    order_id = create_order(client, [{"product_id": 1, "quantity": 2}]).json()["id"]
    client.post(f"/orders/{order_id}/confirm")
    client.post(f"/orders/{order_id}/cancel")
    client.post(f"/orders/{order_id}/cancel")

    with db.cursor() as cur:
        cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
        assert cur.fetchone()["stock_quantity"] == 10
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements WHERE sales_order_id = %s", (order_id,))
        assert cur.fetchone()["count"] == 2


def test_sales_user_cannot_open_another_users_order(client, db):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO sales_orders "
            "(customer_id, created_by, status, discount_percent, subtotal, total) "
            "VALUES (1, 3, 'draft', 0, 100, 100)"
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
    response = client.get(f"/orders/{other_order_id}")
    assert response.status_code == 404


def test_invalid_csv_import_adds_nothing(client, db):
    login(client, "admin@example.com")
    csv_path = Path("sample_data/products_invalid.csv")
    with csv_path.open("rb") as csv_file:
        response = client.post(
            "/products/import-csv",
            files={"file": (csv_path.name, csv_file, "text/csv")},
        )

    assert response.status_code == 400
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM products")
        assert cur.fetchone()["count"] == 2
        cur.execute("SELECT COUNT(*) AS count FROM stock_movements")
        assert cur.fetchone()["count"] == 0
