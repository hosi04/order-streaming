-- MYSQL
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    name VARCHAR(255),
    brand VARCHAR(255),
    price INT,
    quantity INT,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);


-- CLICKHOUSE
CREATE TABLE IF NOT EXISTS orders_cdc (
    id UInt64,
    created_at DateTime64(3),
    op String,
    ts_ms DateTime64(3),
    _is_deleted UInt8 DEFAULT 0
)
ENGINE = ReplacingMergeTree(ts_ms)
ORDER BY (id);

CREATE TABLE IF NOT EXISTS order_items_cdc (
    id UInt64,
    order_id UInt64,
    name String,
    brand String,
    price Int64,
    quantity Int64,
    op String,
    ts_ms DateTime64(3),
    _is_deleted UInt8 DEFAULT 0
)
ENGINE = ReplacingMergeTree(ts_ms)
ORDER BY (id, order_id);