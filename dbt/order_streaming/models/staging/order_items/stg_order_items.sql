SELECT
    id,
    order_id,
    name,
    brand,
    price,
    quantity,
    op,          -- Giữ cột 'op' để tham chiếu hoặc gỡ lỗi
    ts_ms,       -- Giữ cột 'ts_ms' để tham chiếu, là dấu thời gian của sự kiện CDC
    _is_deleted  -- Giữ cột '_is_deleted' cho mục đích minh bạch, mặc dù chúng ta đã lọc nó
FROM (
    SELECT
        *,
        -- Sử dụng ROW_NUMBER để xếp hạng các phiên bản của mỗi mục hàng.
        -- Chúng ta phân vùng theo 'id' và 'order_id' để định danh duy nhất một mục hàng cụ thể
        -- trong một đơn hàng. Sắp xếp giảm dần theo 'ts_ms' để phiên bản mới nhất lên đầu.
        ROW_NUMBER() OVER (PARTITION BY id, order_id ORDER BY ts_ms DESC) as rn
    FROM
        {{ source('order_streaming', 'order_items_cdc') }}
) AS ranked_data
WHERE
    -- Chỉ chọn bản ghi có số thứ tự là 1, tức là phiên bản mới nhất
    rn = 1
    -- Lọc bỏ các bản ghi đã bị đánh dấu là xóa mềm (khi _is_deleted = 1)
    AND _is_deleted = 0