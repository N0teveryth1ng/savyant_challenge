def customer_sales(db, date_from=None, date_to=None):
    join = " LEFT JOIN sales_orders o ON o.customer_id = c.id AND o.status = 'confirmed'"
    params = []
    if date_from:
        join += " AND DATE(o.created_at) >= %s"
        params.append(date_from)
    if date_to:
        join += " AND DATE(o.created_at) <= %s"
        params.append(date_to)

    query = (
        "SELECT c.id, c.customer_name AS name, COUNT(o.id) AS order_count, "
        "COALESCE(SUM(o.total), 0) AS sales_total FROM customers c"
        + join
        + " GROUP BY c.id, c.customer_name ORDER BY sales_total DESC"
    )
    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def product_sales(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT p.id, p.sku AS product_code, p.product_name AS name, "
            "SUM(i.quantity) AS quantity_sold, SUM(i.line_total) AS gross_item_value "
            "FROM sales_order_items i "
            "JOIN sales_orders o ON o.id = i.sales_order_id "
            "JOIN products p ON p.id = i.product_id "
            "WHERE o.status = 'confirmed' "
            "GROUP BY p.id, p.sku, p.product_name "
            "ORDER BY quantity_sold DESC"
        )
        return cur.fetchall()


def low_stock(db, threshold):
    with db.cursor() as cur:
        cur.execute(
            "SELECT sku AS product_code, product_name AS name, category, stock_quantity "
            "FROM products WHERE stock_quantity < %s ORDER BY stock_quantity",
            (threshold,),
        )
        return cur.fetchall()


def stock_movement_history(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT p.sku AS product_code, p.product_name AS name, "
            "CASE WHEN m.quantity_change >= 0 THEN 'IN' ELSE 'OUT' END AS movement_type, "
            "m.quantity_change, o.order_number, m.reason, m.created_at, u.name AS changed_by "
            "FROM stock_movements m JOIN products p ON p.id = m.product_id "
            "LEFT JOIN sales_orders o ON o.id = m.sales_order_id "
            "LEFT JOIN users u ON u.id = m.changed_by "
            "ORDER BY m.created_at DESC"
        )
        return cur.fetchall()
