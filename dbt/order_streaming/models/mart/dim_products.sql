-- -- models/mart/dim_products.sql
-- SELECT
--     -- Tạo một ID sản phẩm duy nhất, có thể dùng hàm băm nếu cần, 
--     -- hoặc kết hợp các thuộc tính nếu 'id' trong order_items không phải là product_id
--     -- Giả sử 'name' và 'brand' là đủ để định danh sản phẩm duy nhất trong ngữ cảnh này.
--     -- Trong thực tế, bạn sẽ có một product_id từ hệ thống nguồn.
--     FARM_FINGERPRINT(concat(name, '_', brand)) as product_key, 
--     name AS product_name,
--     brand AS product_brand
-- FROM
--     {{ ref('stg_order_items') }}
-- GROUP BY
--     name, brand


-- models/mart/dim_products.sql
SELECT
    -- Thay FARM_FINGERPRINT thành farmFingerprint64
    farmFingerprint64(concat(name, '_', brand)) as product_key,
    name AS product_name,
    brand AS product_brand
FROM
    {{ ref('stg_order_items') }}
GROUP BY
    name, brand