import pymysql


def create_product(db, data):
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO products "
                "(sku, product_name, category, unit_price, stock_quantity, is_active) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (data.product_code, data.name, data.category, data.price,
                 data.stock_quantity, data.is_active),
            )
        db.commit()
    except pymysql.err.IntegrityError as error:
        db.rollback()
        raise ValueError("Product code already exists") from error


def list_products(db, search, category, is_active):
    query = (
        "SELECT id, sku AS product_code, product_name AS name, category, "
        "unit_price AS price, stock_quantity, is_active FROM products WHERE 1=1"
    )
    params = []

    if search:
        query += " AND (sku LIKE %s OR product_name LIKE %s)"
        search_value = f"%{search}%"
        params += [search_value, search_value]

    if category is not None:
        query += " AND category = %s"
        params.append(category)

    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)

    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_product(db, product_id):
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, sku AS product_code, product_name AS name, category, "
            "unit_price AS price, stock_quantity, is_active "
            "FROM products WHERE id = %s",
            (product_id,),
        )
        return cur.fetchone()


def update_product(db, product_id, data):
    if not get_product(db, product_id):
        return False

    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE products SET sku = %s, product_name = %s, category = %s, "
                "unit_price = %s, stock_quantity = %s, is_active = %s WHERE id = %s",
                (data.product_code, data.name, data.category, data.price,
                 data.stock_quantity, data.is_active, product_id),
            )
        db.commit()
    
    except pymysql.err.IntegrityError as error:
        db.rollback()
        raise ValueError("Product code already exists") from error
    return True


def delete_product(db, product_id):
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            deleted = cur.rowcount > 0
        db.commit()
        return deleted
    except pymysql.err.IntegrityError as error:
        db.rollback()
        raise ValueError(
            "Product is used by an order or stock movement; deactivate it instead"
        ) from error


def adjust_stock(db, product_id, quantity_change, reason, user_id):
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT stock_quantity FROM products WHERE id = %s FOR UPDATE",
                (product_id,),
            )
            product = cur.fetchone()
            if not product:
                db.rollback()
                return False

            new_quantity = product["stock_quantity"] + quantity_change
            if new_quantity < 0:
                raise ValueError("Stock cannot be negative")

            cur.execute(
                "UPDATE products SET stock_quantity = %s WHERE id = %s",
                (new_quantity, product_id),
            )
            cur.execute(
                "INSERT INTO stock_movements "
                "(product_id, changed_by, quantity_change, reason) "
                "VALUES (%s, %s, %s, %s)",
                (product_id, user_id, quantity_change, reason),
            )

        db.commit()
        return True
    
    except Exception:
        db.rollback()
        raise
