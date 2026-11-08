import os
import sys
from pathlib import Path

import pymysql
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

PROJECT_DIR = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

TEST_DB_NAME = "sales_inventory_test"
PASSWORD_HASH = "$2b$12$ygcr5Td1N9J5KF5rz8.0FOSBcHGpcRV55Jzg95jYxS96JFNg.ktYG"


def connect_to_test_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=TEST_DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


@pytest.fixture(scope="session", autouse=True)
def load_test_schema():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        autocommit=True,
    )
    try:
        with connection.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS {TEST_DB_NAME} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE {TEST_DB_NAME}")
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in (
                "stock_movements", "sales_order_items", "sales_orders",
                "products", "customers", "users",
            ):
                cur.execute(f"DROP TABLE IF EXISTS {table}")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")

            schema = (PROJECT_DIR / "schema.sql").read_text(encoding="utf-8")
            schema = schema.replace("SAVYANT", TEST_DB_NAME)
            for statement in schema.split(";"):
                if statement.strip():
                    cur.execute(statement)
    finally:
        connection.close()


@pytest.fixture(autouse=True)
def clear_and_seed_test_tables(load_test_schema):
    connection = connect_to_test_db()
    with connection.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in (
            "stock_movements", "sales_order_items", "sales_orders",
            "products", "customers", "users",
        ):
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

        cur.executemany(
            "INSERT INTO users (name, email, password_hash, role) "
            "VALUES (%s, %s, %s, %s)",
            [
                ("Admin", "admin@example.com", PASSWORD_HASH, "admin"),
                ("Sales One", "sales@example.com", PASSWORD_HASH, "sales"),
                ("Sales Two", "sales2@example.com", PASSWORD_HASH, "sales"),
            ],
        )
        cur.execute(
            "INSERT INTO customers (customer_name, email, phone, city, is_active) "
            "VALUES ('Test Customer', 'customer@example.com', '5550100', 'Test City', 1)"
        )
        cur.executemany(
            "INSERT INTO products "
            "(sku, product_name, category, unit_price, stock_quantity, is_active) "
            "VALUES (%s, %s, %s, %s, %s, 1)",
            [
                ("P-100", "Product 100", "Test", 100, 10),
                ("P-250", "Product 250", "Test", 250, 10),
            ],
        )
    connection.commit()
    connection.close()


@pytest.fixture
def db():
    connection = connect_to_test_db()
    yield connection
    connection.close()


@pytest.fixture
def client():
    from app.database import get_db
    from app.main import app

    def test_database_dependency():
        connection = connect_to_test_db()
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[get_db] = test_database_dependency
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
