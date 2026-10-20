-- ============================================================================
-- Analytical queries untuk PT KopiDate Indonesia
-- Database: KopiDate.duckdb
-- Tables: orders, menu
-- Run:    duckdb KopiDate.duckdb < queries.sql
-- ============================================================================

-- ── 1. Daily revenue by outlet (time series) ───────────────────────────────
SELECT
    order_date,
    outlet,
    COUNT(*)        AS n_orders,
    SUM(revenue_idr) AS revenue_idr
FROM orders
WHERE order_date BETWEEN DATE '2024-01-01' AND DATE '2024-01-31'
GROUP BY order_date, outlet
ORDER BY order_date, outlet;


-- ── 2. Menu master JOIN orders: revenue per category ──────────────────────
SELECT
    m.category,
    COUNT(DISTINCT o.order_id) AS n_orders,
    SUM(o.qty)                 AS cups_sold,
    SUM(o.revenue_idr)         AS revenue_idr,
    ROUND(AVG(o.price_idr), 0) AS avg_price_idr
FROM menu  m
JOIN orders o ON m.menu_item = o.menu_item
GROUP BY m.category
ORDER BY revenue_idr DESC;


-- ── 3. Payment mix (penting untuk finance & BD) ───────────────────────────
SELECT
    payment_method,
    COUNT(*)        AS n_orders,
    SUM(revenue_idr) AS revenue_idr,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS pct_of_orders
FROM orders
GROUP BY payment_method
ORDER BY n_orders DESC;


-- ── 4. Top menu per outlet (pivot-style via window function) ──────────────
WITH ranked AS (
    SELECT
        outlet,
        menu_item,
        SUM(revenue_idr) AS revenue,
        ROW_NUMBER() OVER (
            PARTITION BY outlet
            ORDER BY SUM(revenue_idr) DESC
        ) AS rnk
    FROM orders
    GROUP BY outlet, menu_item
)
SELECT outlet, menu_item, revenue, rnk
FROM ranked
WHERE rnk <= 3
ORDER BY outlet, rnk;


-- ── 5. Shift performance — JOIN menu & orders ─────────────────────────────
SELECT
    o.outlet,
    o.shift,
    COUNT(*)        AS orders_count,
    SUM(o.revenue_idr) AS revenue_idr,
    ROUND(AVG(o.revenue_idr), 0) AS avg_ticket_idr
FROM orders o
LEFT JOIN menu m ON o.menu_item = m.menu_item
WHERE o.shift IS NOT NULL
GROUP BY o.outlet, o.shift
ORDER BY o.outlet, o.shift;


-- ── 6. Data quality check (harus dijalankan setelah pipeline) ─────────────
-- detect: outlet NULL, payment NULL, qty <= 0, price_idr == 0
SELECT
    'outlet NULL'       AS issue, COUNT(*) AS n FROM orders WHERE outlet IS NULL
UNION ALL
SELECT 'payment NULL',           COUNT(*) FROM orders WHERE payment_method IS NULL
UNION ALL
SELECT 'qty <= 0',               COUNT(*) FROM orders WHERE qty <= 0
UNION ALL
SELECT 'price_idr = 0',          COUNT(*) FROM orders WHERE price_idr = 0
UNION ALL
SELECT 'order_date NULL',        COUNT(*) FROM orders WHERE order_date IS NULL;
