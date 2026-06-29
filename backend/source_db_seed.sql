-- ============================================================
-- KAYNAK VERİTABANI — demo_source
-- Bu SQL, docker compose up sırasında otomatik çalışır
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id   SERIAL PRIMARY KEY,
    customer_no   VARCHAR(20) UNIQUE NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(200),
    phone         VARCHAR(30),
    city          VARCHAR(100),
    country       VARCHAR(50) DEFAULT 'TR',
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    product_id    SERIAL PRIMARY KEY,
    sku           VARCHAR(50) UNIQUE NOT NULL,
    product_name  VARCHAR(200) NOT NULL,
    category      VARCHAR(100),
    unit_price    NUMERIC(12,2) NOT NULL,
    stock_qty     INTEGER DEFAULT 0,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      SERIAL PRIMARY KEY,
    order_no      VARCHAR(30) UNIQUE NOT NULL,
    customer_id   INTEGER REFERENCES customers(customer_id),
    order_date    DATE NOT NULL,
    status        VARCHAR(30) DEFAULT 'PENDING',
    total_amount  NUMERIC(14,2),
    currency      VARCHAR(3) DEFAULT 'TRY',
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id      SERIAL PRIMARY KEY,
    order_id     INTEGER REFERENCES orders(order_id),
    product_id   INTEGER REFERENCES products(product_id),
    quantity     INTEGER NOT NULL,
    unit_price   NUMERIC(12,2) NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW()
);

INSERT INTO customers (customer_no, first_name, last_name, email, phone, city) VALUES
('C-0001','Ahmet',  'Yılmaz', 'ahmet.yilmaz@ornek.com','05321234567','İstanbul'),
('C-0002','Fatma',  'Kaya',   'fatma.kaya@ornek.com',  '05334567890','Ankara'),
('C-0003','Mehmet', 'Demir',  'mehmet.demir@ornek.com','05356789012','İzmir'),
('C-0004','Ayşe',   'Çelik',  'ayse.celik@ornek.com',  '05378901234','Bursa'),
('C-0005','Mustafa','Şahin',  'mustafa.sahin@ornek.com','05390123456','Antalya'),
('C-0006','Zeynep', 'Arslan', 'zeynep.arslan@ornek.com','05312345678','Adana'),
('C-0007','Ali',    'Koç',    'ali.koc@ornek.com',     '05323456789','Gaziantep'),
('C-0008','Hatice', 'Güneş',  'hatice.gunes@ornek.com','05345678901','Konya'),
('C-0009','İbrahim','Aydın',  'ibrahim.aydin@ornek.com','05367890123','Mersin'),
('C-0010','Emine',  'Erdoğan','emine.erdogan@ornek.com','05389012345','Kayseri')
ON CONFLICT (customer_no) DO NOTHING;

INSERT INTO products (sku, product_name, category, unit_price, stock_qty) VALUES
('SKU-001','Laptop Pro 15"',   'Elektronik',24999.00,50),
('SKU-002','Kablosuz Mouse',   'Elektronik',  299.00,200),
('SKU-003','Mekanik Klavye',   'Elektronik',  799.00,150),
('SKU-004','USB-C Hub 7-in-1', 'Elektronik',  549.00,300),
('SKU-005','Monitör 27" 4K',   'Elektronik', 6999.00, 30),
('SKU-006','Ofis Sandalyesi',  'Mobilya',    2499.00, 40),
('SKU-007','Çalışma Masası',   'Mobilya',    3999.00, 20),
('SKU-008','Kulaklık BT',      'Elektronik',  999.00,100),
('SKU-009','Webcam HD 1080p',  'Elektronik',  649.00, 80),
('SKU-010','Yazıcı Laser',     'Elektronik', 2999.00, 25)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO orders (order_no,customer_id,order_date,status,total_amount) VALUES
('ORD-2024-0001',1,'2024-01-10','DELIVERED',25598.00),
('ORD-2024-0002',2,'2024-01-12','DELIVERED', 1847.00),
('ORD-2024-0003',3,'2024-01-15','DELIVERED', 7648.00),
('ORD-2024-0004',4,'2024-01-18','DELIVERED',  549.00),
('ORD-2024-0005',5,'2024-02-01','DELIVERED', 3798.00),
('ORD-2024-0006',6,'2024-02-05','DELIVERED',  999.00),
('ORD-2024-0007',7,'2024-02-10','CANCELLED',24999.00),
('ORD-2024-0008',8,'2024-02-14','DELIVERED', 2628.00),
('ORD-2024-0009',9,'2024-02-20','DELIVERED',  649.00),
('ORD-2024-0010',10,'2024-03-01','DELIVERED',4548.00),
('ORD-2024-0011',1,'2024-03-05','DELIVERED',  599.00),
('ORD-2024-0012',2,'2024-03-10','DELIVERED', 1397.00),
('ORD-2024-0013',3,'2024-03-15','DELIVERED', 6999.00),
('ORD-2024-0014',4,'2024-03-20','PROCESSING',2499.00),
('ORD-2024-0015',5,'2024-03-25','PENDING',   3999.00),
('ORD-2024-0016',6,'2024-04-01','DELIVERED',   79.00),
('ORD-2024-0017',7,'2024-04-05','DELIVERED',  648.00),
('ORD-2024-0018',8,'2024-04-10','DELIVERED',   29.00),
('ORD-2024-0019',9,'2024-04-15','DELIVERED', 5498.00),
('ORD-2024-0020',10,'2024-04-20','DELIVERED',2999.00)
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES
(1,1,1,24999.00),(1,2,2,299.00),
(2,3,1,799.00),(2,4,1,549.00),
(3,5,1,6999.00),(3,2,1,299.00),
(4,4,1,549.00),
(5,6,1,2499.00),(5,8,1,999.00),
(6,8,1,999.00),
(8,1,1,24999.00),(8,4,2,549.00),
(9,9,1,649.00),
(10,5,1,6999.00),(10,8,1,999.00),
(11,10,1,599.00),
(12,8,1,999.00),
(13,5,1,6999.00),
(14,6,1,2499.00),
(15,7,1,3999.00),
(19,1,1,24999.00),(19,2,1,299.00),
(20,10,1,2999.00)
ON CONFLICT DO NOTHING;
