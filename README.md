# Sales & Inventory Management

A simple local application for managing customer records, products, sales orders, and stock. It replaces spreadsheet-based tracking with a browser interface and a MySQL database.

The application files and local setup resources are in the **project** folder.

**AI use disclosure:** [Read AI_USAGE.md](AI_USAGE.md)

## At a glance

- **Application:** Sales Order and Inventory Management
- **Technology:** Python, FastAPI, HTML, CSS, JavaScript, and MySQL
- **Intended use:** Local demonstration and coursework
- **Currency and stock:** One currency and one stock location
- **Quantities:** Whole numbers
- **Taxes, delivery, purchasing, and payments:** Not included

## What you can do

### Manage customers and products

Administrators can add, view, edit, and remove customers and products. They can search and filter records, deactivate records that should no longer be used, and adjust product stock with a reason. Products have a unique code, category, price, available quantity, and active status.

Sales users can view active customers and products. They cannot change customer or product records, adjust stock, import products, or view reports. These permissions are checked by the application, including for direct requests.

### Create and manage orders

Users can create Draft orders for active customers using active products. The application uses each product’s current saved price, checks quantities, prevents duplicate products in an order, and calculates the subtotal, discount, and total. Discounts may be from zero to twenty percent.

Users can edit their own Draft orders. Administrators can view and manage all orders; Sales users can access only their own. Confirming an order checks stock and deducts it. Cancelling a confirmed order restores the stock. The order and its stock changes are saved together, and repeating a confirmation or cancellation does not repeat the stock change.

### Review reports and import products

Administrators can review customer sales, product sales, low stock, and stock movement history. Customer sales can be limited to a date range, and the low stock report accepts a quantity threshold. The project also includes five standalone SQL report queries.

Administrators can import products from a CSV file. The application checks the full file before importing; if any row is invalid, no products are added. Errors identify the row and reason. Opening quantities from a successful import are recorded in stock history. Example valid and invalid files are in the sample data folder.

## API examples

Sample requests and responses for login, product lookup, and order workflows are in [project/API_EXAMPLES.md](project/API_EXAMPLES.md). The interactive API reference is available locally at **http://localhost:8000/docs**.

## Roles

| Role | Access |
| --- | --- |
| Administrator | Manage customers and products, adjust stock, manage all orders, import products, and view reports |
| Sales user | View active customers and products, create and manage their own orders |

## Run locally

The application requires Python 3.10 or newer and MySQL 8. Install the Python dependencies listed in **project/requirements.txt**, configure a local database connection using **project/.env.example** as a guide, and initialize the database using **project/schema.sql**. The schema creates the database tables and demonstration records.

For an existing database created from the earlier project schema, apply **project/migrations/001_order_number_discount.sql** once instead of recreating the database. It adds the order number and discount amount while preserving existing records. New databases already include those fields in the main schema.

Once the database and settings are ready, start the application from the **project** folder using the local FastAPI server setup and open **http://localhost:8000** in a browser. The interactive API reference is available at **http://localhost:8000/docs**.

## Demonstration accounts

Both sample accounts use the same demonstration password, **ChangeMe123!**

| Role | Email |
| --- | --- |
| Administrator | admin@example.com |
| Sales user | sales@example.com |

These accounts are for local demonstration only. Passwords are stored as bcrypt hashes in the database. The project does not include account creation, user management, or password recovery screens.

## Data and reliability

The database contains six related tables: users, customers, products, sales orders, sales order items, and stock movements. Foreign keys protect records that are referenced by orders or stock history. Such customers and products cannot be deleted; they can be deactivated instead.

Prices and order totals are stored using fixed-precision decimal values and calculated on the server. Browser totals are previews only. On confirmation, the application locks the relevant database rows, checks all requested stock, then saves the deduction and movement history in one transaction. If stock is short, the confirmation makes no changes.

Only confirmed orders are included in sales reports. Product sales show the gross value of sold items before order discounts. Customer sales show the confirmed order total after discount and include customers with no matching orders in the selected period.

## Tests

The project includes automated tests for total calculations, invalid quantities and discounts, order permissions, stock confirmation and cancellation, and all-or-nothing CSV imports. Tests use a separate database named sales_inventory_test, load the supplied schema, and reset its tables before each test. They do not clear the normal SAVYANT database. The test files are in **project/tests**.

The current test suite contains 20 tests. Configure the local MySQL connection, open the **project** folder in a terminal, and run `pytest -v`.

## Debugging exercise

The original calculation bug assigned the current item amount to the running total on every loop, overwriting amounts from earlier items. The fixed `calculate_total()` adds each item amount to the running total. The required example with quantities and rates of 2 × 100 and 3 × 50 returns 350. An empty list returns zero; missing quantity or rate, zero or negative quantity, and negative rate are rejected. The tests cover these behaviors.

## Project contents

- **Database schema and sample data:** project/schema.sql
- **Earlier database update:** project/migrations
- **Application and browser interface:** project/app
- **Standalone report queries:** project/sql_queries.sql
- **API request and response examples:** project/API_EXAMPLES.md
- **CSV examples:** project/sample_data
- **Automated tests:** project/tests
- **AI assistance disclosure:** AI_USAGE.md (also included in project/AI_USAGE.md)

## Demo walkthrough

The assignment demo should take five to eight minutes. Show both roles, demonstrate that Sales users cannot change master data, create and confirm an order, cancel an order, review a report, import a CSV file, and show the test results. The recording is a separate submission item and is not included in the application.
