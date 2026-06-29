-- ============================================================
-- HEDEF VERİTABANI — demo_target (DWH şeması)
-- Pipeline'ın veri yazacağı tablolar burada tanımlanır
-- ============================================================

-- Boyut tablo: Müşteriler
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key  SERIAL PRIMARY KEY,
    customer_id   INTEGER UNIQUE,
    customer_no   VARCHAR(20),
    full_name     VARCHAR(200),
    email         VARCHAR(200),
    phone         VARCHAR(30),
    city          VARCHAR(100),
    country       VARCHAR(50),
    load_date     TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- Boyut tablo: Ürünler
CREATE TABLE IF NOT EXISTS dim_products (
    product_key   SERIAL PRIMARY KEY,
    product_id    INTEGER UNIQUE,
    sku           VARCHAR(50),
    product_name  VARCHAR(200),
    category      VARCHAR(100),
    unit_price    NUMERIC(12,2),
    load_date     TIMESTAMP DEFAULT NOW()
);

-- Gerçek tablo: Siparişler (hedef pipeline tablosu)
CREATE TABLE IF NOT EXISTS fact_orders (
    order_key     SERIAL PRIMARY KEY,
    order_id      INTEGER UNIQUE,
    order_no      VARCHAR(30),
    customer_id   INTEGER,
    order_date    DATE,
    status        VARCHAR(30),
    total_amount  NUMERIC(14,2),
    currency      VARCHAR(3),
    load_date     TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- Gerçek tablo: Sipariş kalemleri
CREATE TABLE IF NOT EXISTS fact_order_items (
    item_key      SERIAL PRIMARY KEY,
    item_id       INTEGER UNIQUE,
    order_id      INTEGER,
    product_id    INTEGER,
    quantity      INTEGER,
    unit_price    NUMERIC(12,2),
    line_total    NUMERIC(14,2),
    load_date     TIMESTAMP DEFAULT NOW()
);

-- Log tablosu (isteğe bağlı — hangi kayıtların yüklendiğini izlemek için)
CREATE TABLE IF NOT EXISTS etl_load_log (
    log_id        SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(200),
    table_name    VARCHAR(200),
    rows_loaded   INTEGER,
    load_start    TIMESTAMP,
    load_end      TIMESTAMP,
    status        VARCHAR(30)
);
