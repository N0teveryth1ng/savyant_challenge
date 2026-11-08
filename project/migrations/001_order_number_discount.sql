-- Run this once when upgrading a database created from the earlier schema.sql.
-- Fresh databases already have these columns and do not need this migration.
ALTER TABLE sales_orders
    ADD COLUMN order_number VARCHAR(20) NULL AFTER id,
    ADD COLUMN discount_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 AFTER subtotal;

UPDATE sales_orders
SET order_number = CONCAT('SO-', LPAD(id, 10, '0'))
WHERE order_number IS NULL;

ALTER TABLE sales_orders
    MODIFY order_number VARCHAR(20) NOT NULL,
    ADD UNIQUE KEY uq_sales_orders_number (order_number);
