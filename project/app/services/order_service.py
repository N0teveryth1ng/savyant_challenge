from decimal import Decimal


def calculate_totals(items, discount_percent):
    total = Decimal("0.00")
    for item in items:
        amount = item["unit_price"] * item["quantity"]
        total += amount

    subtotal = total.quantize(Decimal("0.01"))
    total = subtotal * (100 - discount_percent) / 100
    return subtotal, total.quantize(Decimal("0.01"))


def get_order_data(db, requested_items):
    items = []
    product_ids = set()

    with db.cursor() as cur:
        for requested in requested_items:
            if requested.product_id in product_ids:
                raise ValueError("A product can only appear once in an order")
            product_ids.add(requested.product_id)

            cur.execute(
                "SELECT unit_price FROM products WHERE id = %s",
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
        items = get_order_data(db, data.items)
        subtotal, total = calculate_totals(items, data.discount_percent)

        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO sales_orders "
                "(customer_id, created_by, status, discount_percent, subtotal, total) "
                "VALUES (%s, %s, 'draft', %s, %s, %s)",
                (data.customer_id, user_id, data.discount_percent, subtotal, total),
            )
            order_id = cur.lastrowid
            save_order_items(cur, order_id, items)

        db.commit()
        return order_id
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
        items = get_order_data(db, data.items)
        subtotal, total = calculate_totals(items, data.discount_percent)

        with db.cursor() as cur:
            cur.execute(
                "UPDATE sales_orders SET customer_id = %s, discount_percent = %s, "
                "subtotal = %s, total = %s WHERE id = %s",
                (data.customer_id, data.discount_percent, subtotal, total, order_id),
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
