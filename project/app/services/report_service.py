def sales_by_customer(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT c.id, c.customer_name AS name, COUNT(o.id) AS order_count, "
            "COALESCE(SUM(o.total), 0) AS sales_total "
            "FROM customers c LEFT JOIN sales_orders o "
            "ON o.customer_id = c.id AND o.status = 'confirmed' "
            "GROUP BY c.id, c.customer_name ORDER BY sales_total DESC"
        )
        return cur.fetchall()


def sales_by_product(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT p.id, p.sku AS product_code, p.product_name AS name, "
            "SUM(i.quantity) AS units_sold, SUM(i.line_total) AS line_sales "
            "FROM sales_order_items i "
            "JOIN sales_orders o ON o.id = i.sales_order_id "
            "JOIN products p ON p.id = i.product_id "
            "WHERE o.status = 'confirmed' "
            "GROUP BY p.id, p.sku, p.product_name ORDER BY units_sold DESC"
        )
        return cur.fetchall()


def monthly_sales(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, "
            "COUNT(*) AS order_count, SUM(total) AS sales_total "
            "FROM sales_orders WHERE status = 'confirmed' "
            "GROUP BY DATE_FORMAT(created_at, '%Y-%m') ORDER BY month"
        )
        return cur.fetchall()


def inventory(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT sku AS product_code, product_name AS name, category, "
            "stock_quantity, unit_price, is_active "
            "FROM products ORDER BY product_name"
        )
        return cur.fetchall()
