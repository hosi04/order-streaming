-- models/mart/fact_order_items.sql
SELECT
    oi.id AS order_item_id,
    oi.order_id,
    o.created_at AS order_created_at, -- Lấy thời gian tạo từ bảng đơn hàng
    p.product_key,                   -- Khóa ngoại đến bảng dim_products
    -- oi.name AS product_name,         -- Có thể giữ lại để dễ truy vấn
    -- oi.brand AS product_brand,       -- Có thể giữ lại để dễ truy vấn
    oi.price AS item_price,
    oi.quantity AS item_quantity,
    (oi.price * oi.quantity) AS item_total_amount,
    oi.ts_ms AS processed_at         -- Thời gian dữ liệu được xử lý gần nhất
FROM
    {{ ref('stg_order_items') }} oi
JOIN
    {{ ref('stg_orders') }} o ON oi.order_id = o.id
LEFT JOIN
    {{ ref('dim_products') }} p ON oi.name = p.product_name AND oi.brand = p.product_brand