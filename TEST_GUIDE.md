# DataFlow Platform — Lokal Test Kılavuzu

## Gereksinimler

- Docker Desktop kurulu ve çalışıyor olmalı
- Windows'ta PowerShell veya CMD

---

## ADIM 1 — Fernet Key Üret (zorunlu)

`.env` dosyasındaki `SECRET_ENCRYPTION_KEY` gerçek bir Fernet anahtarı olmalı.
PowerShell'de:

```powershell
docker run --rm python:3.11-slim python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Çıktıyı kopyala, `.env` dosyasında `SECRET_ENCRYPTION_KEY=` satırını güncelle.

---

## ADIM 2 — Docker Compose ile Başlat

`dataflow/` klasöründeyken:

```cmd
docker compose up --build -d
```

İlk seferinde 5–10 dakika sürer (image build + Python paketleri).

Servislerin durumunu izlemek için:
```cmd
docker compose logs -f
```

Tüm servisler hazır mı?
```cmd
docker compose ps
```

Beklenen çıktı (hepsi `healthy` veya `running` olmalı):
```
NAME              STATUS          PORTS
postgres          healthy         0.0.0.0:5432->5432/tcp
demo_source_db    healthy         0.0.0.0:5433->5432/tcp
demo_target_db    healthy         0.0.0.0:5434->5432/tcp
redis             healthy         0.0.0.0:6379->6379/tcp
backend           healthy         0.0.0.0:8000->8000/tcp
celery_worker     running         
celery_beat       running         
flower            running         0.0.0.0:5555->5555/tcp
frontend          running         0.0.0.0:80->80/tcp
```

---

## ADIM 3 — Tarayıcıda Aç

| URL | Açıklama |
|-----|----------|
| http://localhost | Platform arayüzü |
| http://localhost:8000/api/docs | Swagger API docs |
| http://localhost:5555 | Celery Flower (job monitoring) |

**Giriş bilgileri:**
- Email: `admin@dataflow.local`
- Şifre: `Admin123!`

---

## ADIM 4 — Kaynak Bağlantısı Ekle

Platform'a giriş yaptıktan sonra **Connections → Yeni Bağlantı**:

| Alan | Değer |
|------|-------|
| Ad | `demo_kaynak` |
| Tip | `POSTGRESQL` |
| Host | `demo_source_db` ← dikkat: container adı, localhost değil! |
| Port | `5432` |
| Database | `sales_demo` |
| Username | `sales_user` |
| Password | `sales_pass` |

"Test Et" butonuna tıkla → yeşil ✓ görmelisin.

---

## ADIM 5 — Hedef Bağlantısı Ekle

**Connections → Yeni Bağlantı**:

| Alan | Değer |
|------|-------|
| Ad | `demo_hedef` |
| Tip | `POSTGRESQL` |
| Host | `demo_target_db` |
| Port | `5432` |
| Database | `dwh_demo` |
| Username | `dwh_user` |
| Password | `dwh_pass` |

---

## ADIM 6 — Pipeline Oluştur

**Pipelines → Yeni Pipeline** wizard'ına gir:

1. **Temel Bilgiler:** Ad = `orders_test_pipeline`
2. **Kaynak Bağlantı:** `demo_kaynak`
3. **Kaynak Tablo:** `orders` → Önizleme'de 20 satır görmelisin
4. **Hedef Bağlantı:** `demo_hedef`
5. **Hedef Tablo:** `fact_orders`
6. **Kolon Eşleştirme:** "Otomatik Eşleştir" butonuna tıkla
7. **Dönüşümler:** Şimdilik atla (İleri)
8. **Validation:** Şimdilik atla (İleri)
9. **Load Strategy:** `FULL_LOAD`, Batch: `1000`
10. **Schedule:** Kapalı bırak
11. **Özet:** "Yayınla" butonuna tıkla

---

## ADIM 7 — Pipeline'ı Çalıştır

**Pipelines** listesinde `orders_test_pipeline` → **Çalıştır** butonu.

**Job Runs** sayfasında şunları görmelisin:
- Durum: `RUNNING` → `SUCCESS`
- Kaynak satır: 20
- Başarılı: 20

**Loglar** butonuna tıklayarak adım adım ETL akışını izleyebilirsin.

---

## Doğrulama — Hedef DB'yi Kontrol Et

```powershell
docker exec -it dataflow-demo_target_db-1 psql -U dwh_user -d dwh_demo -c "SELECT COUNT(*) FROM fact_orders;"
```

20 satır görmelisin.

---

## Sorun Giderme

**Backend başlamıyor:**
```cmd
docker compose logs backend
```
En sık sebep: `SECRET_ENCRYPTION_KEY` geçersiz. ADIM 1'i tekrar yap.

**Bağlantı testi başarısız:**
Host alanında `localhost` yerine container adını (`demo_source_db`) girdiğinden emin ol.

**Port 80 kullanımda:**
```cmd
docker compose down
# Başka bir uygulamayı kapat, sonra:
docker compose up -d
```

**Sıfırdan başlamak için:**
```cmd
docker compose down -v   # tüm volume'ları siler
docker compose up --build -d
```
