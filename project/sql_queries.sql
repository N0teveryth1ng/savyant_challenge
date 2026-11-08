-- 1. Confirmed sales totals by customer
SELECT c.id, c.customer_name, COUNT(o.id) AS order_count,
       COALESCE(SUM(o.total), 0) AS sales_total
FROM customers c
LEFT JOIN sales_orders o
    ON o.customer_id = c.id AND o.status = 'confirmed'
GROUP BY c.id, c.customer_name
ORDER BY sales_total DESC;

-- 2. Confirmed units sold by product (line sales are before order discount)
SELECT p.sku AS product_code, p.product_name,
       SUM(i.quantity) AS units_sold, SUM(i.line_total) AS line_sales
FROM sales_order_items i
JOIN sales_orders o ON o.id = i.sales_order_id
JOIN products p ON p.id = i.product_id
WHERE o.status = 'confirmed'
GROUP BY p.id, p.sku, p.product_name
ORDER BY units_sold DESC;

-- 3. Confirmed sales by month
SELECT DATE_FORMAT(created_at, '%Y-%m') AS month,
       COUNT(*) AS order_count, SUM(total) AS sales_total
FROM sales_orders
WHERE status = 'confirmed'
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY month;

-- 4. Current product inventory
SELECT sku AS product_code, product_name, category, stock_quantity,
       unit_price, is_active
FROM products
ORDER BY product_name;

-- 5. Items in one order (change 1 to the order ID to inspect)
SELECT o.id AS order_id, o.status, p.sku AS product_code,
       p.product_name, i.quantity, i.unit_price, i.line_total
FROM sales_orders o
JOIN sales_order_items i ON i.sales_order_id = o.id
JOIN products p ON p.id = i.product_id
WHERE o.id = 1;
