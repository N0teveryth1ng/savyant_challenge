# Sales Order and Inventory Project

## Run the tests

Make sure MySQL is running and `project/.env` has valid database credentials. From the `project` folder, run:

```powershell
pip install -r requirements.txt
pytest -v
```

The tests use a separate `sales_inventory_test` database. The test fixture loads `schema.sql` there and resets its tables before each test; it does not use the normal `SAVYANT` database.

## Debugging exercise

The total was wrong because `total = amount` replaced the running total on every loop. Using `total += amount` adds each item's amount to the running total.
