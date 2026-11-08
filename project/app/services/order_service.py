from decimal import Decimal
import uuid


def calculate_total(items):
    total = Decimal("0.00")
    for item in items:
        if "qty" not in item or "rate" not in item or item["qty"] is None or item["rate"] is None:
            raise ValueError("Each item needs a quantity and rate")
        try:
            quantity_value = Decimal(str(item["qty"]))
            rate = Decimal(str(item["rate"]))
        except (TypeError, ValueError, ArithmeticError):
            raise ValueError("Quantity and rate must be valid numbers")
        if not quantity_value.is_finite() or quantity_value != quantity_value.to_integral_value():
            raise ValueError("Quantity must be a whole number")
        quantity = int(quantity_value)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if not rate.is_finite() or rate < 0:
            raise ValueError("Rate cannot be negative")
        amount = rate * quantity
        total += amount
    return total.quantize(Decimal("0.01"))


def calculate_totals(items, discount_percent=0):
    discount = Decimal(str(discount_percent))
    if not discount.is_finite() or discount < 0 or discount > 20:
        raise ValueError("Discount must be between 0 and 20 percent")

    subtotal = calculate_total([
        {"qty": item.get("quantity"), "rate": item.get("unit_price")}
        for item in items
    ])

    discount_amount = (subtotal * discount / 100).quantize(Decimal("0.01"))
    total = subtotal - discount_amount
    return subtotal, discount_amount, total


def get_order_data(db, customer_id, requested_items):
    items = []
    product_ids = set()

    with db.cursor() as cur:
        cur.execute("SELECT id FROM customers WHERE id = %s AND is_active = 1", (customer_id,))
        if not cur.fetchone():
            raise ValueError("Active customer not found")

        for requested in requested_items:
            if requested.product_id in product_ids:
                raise ValueError("A product can only appear once in an order")
            product_ids.add(requested.product_id)

            cur.execute(
                "SELECT unit_price FROM products WHERE id = %s AND is_active = 1",
                (requested.product_id,),
            )
            product = cur.fetchone()
            if not product:
                raise ValueError("Product not found")

            items.append({
                "product_id": requested.product_id,
                "quantity": requested.quantity,
                "unit_price": product["unit_price"],
            })

    return items


def save_order_items(cur, order_id, items):
    rows = [
        (order_id, item["product_id"], item["quantity"], item["unit_price"],
         item["unit_price"] * item["quantity"])
        for item in items
    ]
    cur.executemany(
        "INSERT INTO sales_order_items "
        "(sales_order_id, product_id, quantity, unit_price, line_total) "
        "VALUES (%s, %s, %s, %s, %s)",
        rows,
    )


def create_order(db, data, user_id):
    try:
        items = get_order_data(db, data.customer_id, data.items)
        subtotal, discount_amount, total = calculate_totals(items, data.discount_percent)
        order_number = "SO-" + uuid.uuid4().hex[:12].upper()

        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO sales_orders "
                "(order_number, customer_id, created_by, status, discount_percent, "
                "subtotal, discount_amount, total) "
                "VALUES (%s, %s, %s, 'draft', %s, %s, %s, %s)",
                (order_number, data.customer_id, user_id, data.discount_percent,
                 subtotal, discount_amount, total),
            )
            order_id = cur.lastrowid
            save_order_items(cur, order_id, items)

        db.commit()
        return order_id, order_number
    except Exception:
        db.rollback()
        raise


def list_orders(db, user):
    with db.cursor() as cur:
        if user["role"] == "sales":
            cur.execute(
                "SELECT * FROM sales_orders WHERE created_by = %s ORDER BY id DESC",
                (user["id"],),
            )
        else:
            cur.execute("SELECT * FROM sales_orders ORDER BY id DESC")
        return cur.fetchall()


def get_order(db, order_id, user):
    with db.cursor() as cur:
        if user["role"] == "sales":
            cur.execute(
                "SELECT * FROM sales_orders WHERE id = %s AND created_by = %s",
                (order_id, user["id"]),
            )
        else:
            cur.execute("SELECT * FROM sales_orders WHERE id = %s", (order_id,))

        order = cur.fetchone()
        if not order:
            return None

        cur.execute(
            "SELECT product_id, quantity, unit_price, line_total "
            "FROM sales_order_items WHERE sales_order_id = %s",
            (order_id,),
        )
        order["items"] = cur.fetchall()
        return order


def update_draft_order(db, order_id, data, user):
    order = get_order(db, order_id, user)
    if not order:
        return False
    if order["status"] != "draft":
        raise ValueError("Only draft orders can be edited")

    try:
        items = get_order_data(db, data.customer_id, data.items)
        subtotal, discount_amount, total = calculate_totals(items, data.discount_percent)

        with db.cursor() as cur:
            cur.execute(
                "UPDATE sales_orders SET customer_id = %s, discount_percent = %s, "
                "subtotal = %s, discount_amount = %s, total = %s WHERE id = %s",
                (data.customer_id, data.discount_percent, subtotal,
                 discount_amount, total, order_id),
            )
            cur.execute(
                "DELETE FROM sales_order_items WHERE sales_order_id = %s",
                (order_id,),
            )
            save_order_items(cur, order_id, items)

        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def confirm_order(db, order_id, user):
    try:
        with db.cursor() as cur:
            if user["role"] == "sales":
                cur.execute(
                    "SELECT status FROM sales_orders WHERE id = %s AND created_by = %s FOR UPDATE",
                    (order_id, user["id"]),
                )
            else:
                cur.execute("SELECT status FROM sales_orders WHERE id = %s FOR UPDATE", (order_id,))
            order = cur.fetchone()

        if not order:
            db.rollback()
            return None
        if order["status"] != "draft":
            db.commit()
            return False

        with db.cursor() as cur:
            cur.execute(
                "SELECT product_id, quantity FROM sales_order_items "
                "WHERE sales_order_id = %s ORDER BY product_id",
                (order_id,),
            )
            items = cur.fetchall()

            for item in items:
                cur.execute(
                    "SELECT stock_quantity FROM products WHERE id = %s FOR UPDATE",
                    (item["product_id"],),
                )
                product = cur.fetchone()
                if product["stock_quantity"] < item["quantity"]:
                    raise ValueError("Not enough stock to confirm this order")

            for item in items:
                cur.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - %s WHERE id = %s",
                    (item["quantity"], item["product_id"]),
                )
                cur.execute(
                    "INSERT INTO stock_movements "
                    "(product_id, sales_order_id, changed_by, quantity_change, reason) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (item["product_id"], order_id, user["id"], -item["quantity"], "Order confirmed"),
                )

            cur.execute("UPDATE sales_orders SET status = 'confirmed' WHERE id = %s", (order_id,))

        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def cancel_order(db, order_id, user):
    try:
        with db.cursor() as cur:
            if user["role"] == "sales":
                cur.execute(
                    "SELECT status FROM sales_orders WHERE id = %s AND created_by = %s FOR UPDATE",
                    (order_id, user["id"]),
                )
            else:
                cur.execute("SELECT status FROM sales_orders WHERE id = %s FOR UPDATE", (order_id,))
            order = cur.fetchone()

        if not order:
            db.rollback()
            return None
        if order["status"] == "cancelled":
            db.commit()
            return False

        if order["status"] == "confirmed":
            with db.cursor() as cur:
                cur.execute(
                    "SELECT product_id, quantity FROM sales_order_items "
                    "WHERE sales_order_id = %s ORDER BY product_id",
                    (order_id,),
                )
                items = cur.fetchall()

                for item in items:
                    cur.execute(
                        "SELECT id FROM products WHERE id = %s FOR UPDATE",
                        (item["product_id"],),
                    )
                    cur.fetchone()
                    cur.execute(
                        "UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s",
                        (item["quantity"], item["product_id"]),
                    )
                    cur.execute(
                        "INSERT INTO stock_movements "
                        "(product_id, sales_order_id, changed_by, quantity_change, reason) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (item["product_id"], order_id, user["id"], item["quantity"], "Order cancelled"),
                    )

        with db.cursor() as cur:
            cur.execute("UPDATE sales_orders SET status = 'cancelled' WHERE id = %s", (order_id,))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
