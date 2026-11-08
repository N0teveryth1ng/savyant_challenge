# Sales Order and Inventory Management

A small local sales and stock application built with Python 3.10+, FastAPI, MySQL, HTML, CSS, and JavaScript. The API is JSON based and the page uses `fetch()` to call it.

## Setup and run

1. Install MySQL and create a local database user.
2. From this folder, copy `.env.example` to `.env` and set `DB_USER`, `DB_PASSWORD`, and a long random `SECRET_KEY`.
3. For a new database, run `schema.sql` in MySQL. It creates `SAVYANT`, its six tables, and sample users, customers, and products. If upgrading the existing earlier project database, run `migrations/001_order_number_discount.sql` once instead; it adds the order number and discount amount while preserving existing rows.
4. From this folder, install and start the app:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. Interactive API documentation is at <http://localhost:8000/docs>.

Python 3.10 or newer and MySQL 8 are expected. The dependency list is in `requirements.txt`.

## Sample accounts

Both local sample accounts use `ChangeMe123!`:

| Role | Email |
| --- | --- |
| Admin | `admin@example.com` |
| Sales | `sales@example.com` |

These are demonstration credentials only. The database stores bcrypt password hashes. Do not reuse these credentials outside this local project.

## What it does

- Admins can manage customers and products, adjust stock, manage all orders, import products, and view reports.
- Sales users can see active customers and products, create and edit their own Draft orders, and confirm or cancel their own orders.
- The backend checks role, order ownership, active records, quantities, prices, and discounts. Browser totals are only a preview.
- Order prices are copied from the current product price when a Draft is created or edited. The order stores its own rate and item amount.
- Confirming an order locks its order and product rows in one MySQL transaction. It checks all quantities before deducting any stock and writing stock movements. A cancellation restores stock in the same transaction. Repeated actions do not repeat stock changes.
- Money uses `DECIMAL(12,2)` in MySQL and Python `Decimal` calculations rounded to two decimal places.
- Foreign keys prevent deleting customers or products that are referenced by orders or stock movements; deactivate them instead.

This assignment assumes one currency and one stock location, whole-number quantities, and no tax, delivery, purchasing, or payment processing. Only confirmed orders appear in sales reports. There is no password reset or user management screen; demo users are inserted by `schema.sql`.

## API examples

The session cookie from login authenticates subsequent calls. Login and logout:

```http
POST /api/login
Content-Type: application/json

{"email":"sales@example.com","password":"ChangeMe123!"}
```

```http
POST /api/logout
```

Get active products (optional `search`, `category`, `is_active`, `limit`, and `offset`; sales users always see active products):

```http
GET /api/products?search=lamp&limit=20&offset=0
```

Create a Draft order (the server looks up product prices):

```http
POST /api/orders
Content-Type: application/json

{"customer_id":1,"items":[{"product_id":1,"quantity":2}],"discount_percent":10}
```

The response includes the generated order number and ID, for example:

```json
{"id":1,"order_number":"SO-0123456789AB","status":"draft"}
```

Other order calls are `GET /api/orders/{id}`, `PUT /api/orders/{id}` (Draft only), `POST /api/orders/{id}/confirm`, and `POST /api/orders/{id}/cancel`. A Sales user receives 404 when requesting another user's order. Unauthenticated requests return 401, forbidden actions return 403, invalid inputs return 4xx JSON details, and unexpected errors do not return tracebacks.

Customer routes are under `/api/customers`; product routes are under `/api/products`. The admin stock adjustment route is `POST /api/products/{id}/stock-adjustments`. Four admin reports are under `/api/reports`: `customer-sales`, `product-sales`, `low-stock`, and `stock-movements`. Customer-sales accepts `date_from` and `date_to`; low-stock accepts `threshold`.

## CSV import

Admins can import a CSV through `POST /api/products/import-csv` using multipart field `file`. Required headers, in order, are `product_code,product_name,category,price,stock_quantity,status`; status is `active` or `inactive`. It validates the full file first and imports nothing if any row is invalid. Errors include row numbers. Imported opening quantities are recorded as stock movements. Examples are in `sample_data/products_valid.csv` and `sample_data/products_invalid.csv`.

## Tests and debugging exercise

Set valid local MySQL credentials in `.env`. From this folder:

```powershell
pytest -v
```

Tests use the separate `sales_inventory_test` database and load `schema.sql` there; they do not clear the normal `SAVYANT` database. The fixture clears and seeds test tables before each test.

`calculate_totals()` adds each line amount to the running total. The original bug assigned `total = amount` on every loop, so only the last item's amount remained. An empty item list returns zero subtotal, discount, and total. Missing quantity or rate, zero or negative quantity, negative rate, and discounts outside 0–20 are rejected. The tests cover these cases and the required order, stock, access, and CSV scenarios.

## Project files

- `schema.sql`: database tables, keys, constraints, and local sample data.
- `migrations/`: additive SQL for the earlier local database schema.
- `app/routers/`: HTTP routes and request validation.
- `app/services/`: SQL and application rules.
- `sql_queries.sql`: the five standalone report queries.
- `tests/`: pytest coverage.
- `AI_USAGE.md`: AI assistance disclosure and review notes.

For the assignment demo, record a 5–8 minute walkthrough covering login as both roles, master data permissions, an order and stock confirmation/cancellation, a report, CSV import, and the tests. A video file is not generated by the app and must be recorded separately.
