import pymysql


def create_customer(db, data):
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO customers "
                "(customer_name, email, phone, city, is_active) "
                "VALUES (%s, %s, %s, %s, %s)",
                (data.name, data.email, data.mobile, data.city, data.is_active),
            )
        db.commit()
    except pymysql.err.IntegrityError as error:
        db.rollback()
        raise ValueError("A customer with this email already exists") from error


def list_customers(db, search, is_active):
    query = (
        "SELECT id, customer_name AS name, email, phone AS mobile, city, is_active "
        "FROM customers WHERE 1=1"
    )
    params = []

    if search:
        query += " AND (customer_name LIKE %s OR email LIKE %s OR phone LIKE %s)"
        search_value = f"%{search}%"
        params += [search_value, search_value, search_value]

    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)

    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_customer(db, customer_id):
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, customer_name AS name, email, phone AS mobile, city, is_active "
            "FROM customers WHERE id = %s",
            (customer_id,),
        )
        return cur.fetchone()


def update_customer(db, customer_id, data):
    if not get_customer(db, customer_id):
        return False

    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE customers SET customer_name = %s, email = %s, phone = %s, "
                "city = %s, is_active = %s WHERE id = %s",
                (data.name, data.email, data.mobile, data.city, data.is_active, customer_id),
            )
        db.commit()
    except pymysql.err.IntegrityError as error:
        db.rollback()
        raise ValueError("A customer with this email already exists") from error
    return True


def delete_customer(db, customer_id):
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
            deleted = cur.rowcount > 0
        db.commit()
        return deleted
    except pymysql.err.IntegrityError as error:
        db.rollback()
        raise ValueError("Customer has orders; deactivate it instead") from error
