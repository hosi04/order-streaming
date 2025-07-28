-- models/staging/stg_orders.sql
SELECT
    id,
    created_at,
    -- Giữ cột 'op' để tham chiếu hoặc gỡ lỗi, nếu cần
    op,
    -- Giữ cột 'ts_ms' để tham chiếu, có thể đổi tên nếu muốn
    ts_ms,
    -- Giữ cột '_is_deleted' cho mục đích minh bạch, mặc dù chúng ta đã lọc nó
    _is_deleted
FROM (
    SELECT
        *,
        -- Phân vùng theo ID đơn hàng và sắp xếp giảm dần theo thời gian
        -- để lấy phiên bản mới nhất (rn = 1)
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts_ms DESC) as rn
    FROM
        {{ source('order_streaming', 'orders_cdc') }}
) AS ranked_data
WHERE
    -- Chỉ chọn phiên bản mới nhất của mỗi bản ghi đơn hàng
    rn = 1
    -- Chỉ giữ các bản ghi KHÔNG bị đánh dấu là đã xóa
    AND _is_deleted = 0