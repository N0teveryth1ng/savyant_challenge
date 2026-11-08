-- 1. Top 3 customers by confirmed sales total (after discount)
SELECT c.id, c.customer_name, SUM(o.total) AS confirmed_sales
FROM customers c
JOIN sales_orders o ON o.customer_id = c.id
WHERE o.status = 'confirmed'
GROUP BY c.id, c.customer_name
ORDER BY confirmed_sales DESC
LIMIT 3;

-- 2. Top 3 products by quantity sold in confirmed orders
SELECT p.sku AS product_code, p.product_name, SUM(i.quantity) AS quantity_sold
FROM products p
JOIN sales_order_items i ON i.product_id = p.id
JOIN sales_orders o ON o.id = i.sales_order_id
WHERE o.status = 'confirmed'
GROUP BY p.id, p.sku, p.product_name
ORDER BY quantity_sold DESC
LIMIT 3;

-- 3. Customers who have never placed an order
SELECT c.id, c.customer_name, c.email
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM sales_orders o WHERE o.customer_id = c.id
);

-- 4. Confirmed sales totals by year and month
SELECT YEAR(created_at) AS sales_year, MONTH(created_at) AS sales_month,
       SUM(total) AS confirmed_sales
FROM sales_orders
WHERE status = 'confirmed'
GROUP BY YEAR(created_at), MONTH(created_at)
ORDER BY sales_year, sales_month;

-- 5. Products below a supplied threshold; set this value before running the query
SET @stock_threshold = 5;
SELECT sku AS product_code, product_name, stock_quantity
FROM products
WHERE stock_quantity < @stock_threshold
ORDER BY stock_quantity;
