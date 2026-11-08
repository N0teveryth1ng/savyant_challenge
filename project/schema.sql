CREATE DATABASE IF NOT EXISTS SAVYANT
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE SAVYANT;

-- ----------- TABLES -------------
-- users 
CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'sales') NOT NULL DEFAULT 'sales',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;


-- --------- CUSTOMERS -----------
CREATE TABLE IF NOT EXISTS customers (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NULL,
    phone VARCHAR(30) NULL,
    address VARCHAR(500) NULL,
    city VARCHAR(100) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_customers_email (email)
) ENGINE=InnoDB;



-- products
CREATE TABLE IF NOT EXISTS products (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_name VARCHAR(150) NOT NULL,
    sku VARCHAR(64) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    stock_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_products_sku (sku)
) ENGINE=InnoDB;


-- sales_orders
CREATE TABLE IF NOT EXISTS sales_orders (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id INT UNSIGNED NOT NULL,
    created_by INT UNSIGNED NOT NULL,
    status ENUM('draft', 'confirmed', 'cancelled') NOT NULL DEFAULT 'draft',
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    subtotal DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_sales_orders_customer (customer_id),
    KEY idx_sales_orders_created_by (created_by),
    CONSTRAINT fk_sales_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers (id),
    CONSTRAINT fk_sales_orders_user
        FOREIGN KEY (created_by) REFERENCES users (id)
) ENGINE=InnoDB;


-- sales order items
CREATE TABLE IF NOT EXISTS sales_order_items (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    sales_order_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    line_total DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_order_product (sales_order_id, product_id),
    KEY idx_order_items_product (product_id),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (sales_order_id) REFERENCES sales_orders (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB;

-- stock movements
CREATE TABLE IF NOT EXISTS stock_movements (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_id INT UNSIGNED NOT NULL,
    sales_order_id INT UNSIGNED NULL,
    changed_by INT UNSIGNED NULL,
    quantity_change INT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_stock_movements_product (product_id),
    KEY idx_stock_movements_order (sales_order_id),
    KEY idx_stock_movements_user (changed_by),
    CONSTRAINT fk_stock_movements_product
        FOREIGN KEY (product_id) REFERENCES products (id),
    CONSTRAINT fk_stock_movements_order
        FOREIGN KEY (sales_order_id) REFERENCES sales_orders (id)
        ON DELETE SET NULL,
    CONSTRAINT fk_stock_movements_user
        FOREIGN KEY (changed_by) REFERENCES users (id)
        ON DELETE SET NULL
) ENGINE=InnoDB;



 
-- Demo password for both sample accounts: ChangeMe123!
-- Change these credentials before using the application beyond local development.
INSERT INTO users (name, email, password_hash, role) VALUES
    ('System Admin', 'admin@example.com', '$2b$12$ygcr5Td1N9J5KF5rz8.0FOSBcHGpcRV55Jzg95jYxS96JFNg.ktYG', 'admin'),
    ('Sales User', 'sales@example.com', '$2b$12$ygcr5Td1N9J5KF5rz8.0FOSBcHGpcRV55Jzg95jYxS96JFNg.ktYG', 'sales');

INSERT INTO customers (customer_name, email, phone, address) VALUES
    ('Acme Retail', 'buyer@acme.example', '555-0101', '100 Market Street'),
    ('Northwind Stores', 'orders@northwind.example', '555-0102', '25 Lake Avenue');

INSERT INTO products (product_name, sku, category, description, unit_price, stock_quantity) VALUES
    ('Desk Lamp', 'LAMP-001', 'Lighting', 'Adjustable LED desk lamp', 39.99, 25),
    ('Office Chair', 'CHAIR-001', 'Furniture', 'Ergonomic office chair', 149.50, 12),
    ('Notebook Pack', 'NOTE-001', 'Stationery', 'Pack of five ruled notebooks', 8.25, 100);




