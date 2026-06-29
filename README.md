# DataFlow Platform

Metadata-driven ETL platformu. Farklı veri kaynaklarından hedef sistemlere kullanıcı dostu arayüz üzerinden veri aktarımı, dönüşüm, doğrulama ve izleme.

## Hızlı Başlangıç

### 1. Ortam Değişkenlerini Ayarla

```bash
cp .env.example .env
# .env dosyasını düzenle:
# - SECRET_KEY ve SECRET_ENCRYPTION_KEY değerlerini değiştir
# - Admin şifresini güncelle
```

### Fernet Key Oluştur

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Çıktıyı .env içinde SECRET_ENCRYPTION_KEY olarak kaydet
```

### 2. Docker Compose ile Başlat

```bash
docker compose up --build -d
```

### 3. Uygulamaya Eriş

| Servis | URL | Açıklama |
|--------|-----|----------|
| Frontend | http://localhost | React UI |
| API Docs | http://localhost:8000/api/docs | Swagger UI |
| Flower | http://localhost:5555 | Celery monitoring |

**Varsayılan giriş:** `admin@dataflow.local` / `Admin123!`

## Geliştirme Ortamı (Local)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Veritabanı migration
alembic upgrade head

# Sunucuyu başlat
uvicorn app.main:app --reload --port 8000
```

### Celery Worker (ayrı terminal)

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --queues=etl
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## Proje Yapısı

```
dataflow/
├── backend/           # FastAPI + Celery + Execution Engine
├── frontend/          # React + TypeScript + Ant Design
├── nginx/             # Nginx reverse proxy config
├── docker-compose.yml
├── .env.example
└── ARCHITECTURE.md    # Detaylı mimari dökümanı
```

## Faz Roadmap

- **Faz 1 (MVP):** Auth, Connections, Pipeline Wizard, Full Load, Job Logs ✅
- **Faz 2:** Incremental Load, Checkpoint, Validation, Scheduling, Retry
- **Faz 3:** RBAC, Audit Log, Schema Drift, SFTP/API Source
- **Faz 4:** Spark Engine, Hive/Iceberg, Airflow Integration
- **Faz 5:** Kafka Streaming

## Desteklenen Connector'lar (MVP)

| Kaynak | Hedef |
|--------|-------|
| PostgreSQL | PostgreSQL |
| MySQL | MySQL |
| MSSQL | MSSQL |
| CSV | CSV |
| Excel | — |

## API Referansı

Swagger UI: http://localhost:8000/api/docs

Ana endpoint'ler:
- `POST /api/v1/auth/login` — Giriş
- `GET/POST /api/v1/connections` — Bağlantı yönetimi
- `POST /api/v1/connections/{id}/test` — Bağlantı test
- `GET/POST /api/v1/pipelines` — Pipeline yönetimi
- `POST /api/v1/jobs/run` — Job başlat
- `GET /api/v1/jobs/{id}/logs` — Job logları
- `GET /api/v1/dashboard/stats` — Dashboard istatistikleri
