# IoV FastAPI Backend

Backend prototype Internet of Vehicles (IoV) untuk menerima GPS dari perangkat mobile, telemetry dari Raspberry Pi/kendaraan, status singkat pengguna, dan report kondisi jalan. Data terbaru dapat diakses melalui REST API, WebSocket, dan dashboard peta pada `/map`.

> Project ini masih prototype. Email, node, dan PID pada registry adalah data dummy dan belum dapat dianggap sebagai autentikasi production.

## Fitur Utama

- Ingest GPS dan telemetry dari node yang terdaftar.
- Snapshot data terbaru seluruh node atau satu node.
- Status message yang melekat pada marker node.
- Report kondisi jalan dengan lokasi dan foto opsional.
- Dashboard peta untuk node, message aktif, dan report.
- REST API, dokumentasi Swagger, dan broadcast WebSocket.
- Penyimpanan JSON/JSONL untuk GPS/telemetry serta SQLite untuk message/report.
- Migrasi database menggunakan Alembic.

## Struktur Proyek

```text
app/              source FastAPI, model, storage, dan dashboard map
alembic/          migration database
static/markers/   ikon marker peta
tests/            automated test
data/             data runtime dan SQLite; tidak masuk Git
uploads/          foto report; tidak masuk Git
```

## Persyaratan

- Python 3.10 atau lebih baru
- `pip` dan `venv`

## Menjalankan Secara Lokal

```bash
git clone https://github.com/danielferennn/riset-IOV-FastApi-server.git
cd riset-IOV-FastApi-server

python3 -m venv .iovvenv
source .iovvenv/bin/activate
python -m pip install -r requirements.txt

mkdir -p data uploads/reports
alembic upgrade head

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Buka layanan berikut:

| URL | Fungsi |
| --- | --- |
| `http://127.0.0.1:8000/health` | Health check |
| `http://127.0.0.1:8000/docs` | Swagger API |
| `http://127.0.0.1:8000/map` | Dashboard peta |

Verifikasi cepat:

```bash
curl http://127.0.0.1:8000/health
```

Respons yang diharapkan:

```json
{"status":"ok"}
```

Untuk pengujian dari perangkat lain dalam jaringan lokal, jalankan dengan `--host 0.0.0.0`, lalu akses IP komputer/server. Pastikan port hanya dibuka pada jaringan yang dipercaya.

## Konfigurasi Environment

Semua konfigurasi bersifat opsional untuk penggunaan lokal.

| Variable | Default | Fungsi |
| --- | --- | --- |
| `IOV_ROOT_PATH` | kosong | Prefix reverse proxy, misalnya `/riset-iov` |
| `IOV_DATA_DIR` | `data` | Lokasi JSON/JSONL GPS dan telemetry |
| `IOV_DATABASE_URL` | `sqlite:///data/iov.db` | URL database message dan report |
| `IOV_UPLOAD_DIR` | `uploads/reports` | Lokasi file foto report |
| `IOV_ADMIN_TOKEN` | kosong | Token untuk mengaktifkan penghapusan report |

Contoh menjalankan dengan direktori absolut:

```bash
export IOV_DATA_DIR=/opt/iov/data
export IOV_DATABASE_URL=sqlite:////opt/iov/data/iov.db
export IOV_UPLOAD_DIR=/opt/iov/uploads/reports

mkdir -p "$IOV_DATA_DIR" "$IOV_UPLOAD_DIR"
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Jangan menyimpan token, password database, atau credential lain di source code dan `alembic.ini`. Gunakan environment service atau file environment yang tidak masuk Git.

## API Utama

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| `GET` | `/health` | Memeriksa backend |
| `GET` | `/pids` | Melihat assignment node/PID prototype |
| `POST` | `/nodes/register` | Registrasi node menggunakan email dummy |
| `POST` | `/ingest/gps` | Mengirim GPS dari mobile |
| `POST` | `/ingest/telemetry` | Mengirim telemetry dari Raspberry Pi/kendaraan |
| `GET` | `/broadcast/latest` | Snapshot terbaru seluruh node untuk client/map |
| `GET` | `/nodes/{node_id}/latest` | Snapshot satu node |
| `POST` | `/nodes/{node_id}/status-message` | Membuat status message |
| `GET` | `/nodes/{node_id}/status-messages` | Membaca message aktif dan riwayatnya |
| `POST` | `/reports` | Membuat report melalui `multipart/form-data` |
| `GET` | `/reports` | Membaca daftar report; mendukung filter area |
| `GET` | `/reports/{report_id}` | Membaca detail report |
| `GET` | `/reports/{report_id}/photos/{photo_id}` | Mengambil foto report |
| `DELETE` | `/reports/{report_id}` | Menghapus report dengan `X-Admin-Token` |
| `GET` | `/events` | Membaca event terbaru untuk debugging |
| `WS` | `/ws/maps` | Broadcast event GPS/telemetry real-time |

Skema request dan response lengkap tersedia pada `/docs`.

### Status Message

- Kategori: `traffic`, `road_condition`, `hazard`, `weather`, dan `info`.
- Maksimal dua message aktif per node.
- Setiap message kedaluwarsa dua jam setelah dipublikasikan.
- Message ketiga menggantikan message aktif paling lama; riwayat tetap disimpan.
- `active_messages` pada snapshot berisi seluruh message aktif. `active_message` tetap tersedia untuk kompatibilitas client lama.

### Report

- Kategori: `road_damage`, `traffic`, `accident`, `flood`, `obstacle`, dan `other`.
- `title`, `description`, `lat`, dan `lon` wajib diisi.
- Foto tidak wajib; maksimal tiga foto dengan ukuran 5 MB per file.
- Format foto yang diterima: JPEG, PNG, dan WebP.
- Report tidak expired dan tidak dikirim melalui `/broadcast/latest`; client mengambilnya melalui `/reports`.
- URL foto pada response bersifat relatif terhadap base URL server.

Penghapusan report hanya aktif jika `IOV_ADMIN_TOKEN` dikonfigurasi. Request harus membawa header `X-Admin-Token` dengan nilai yang sama.

## Penyimpanan Data

| Data | Penyimpanan |
| --- | --- |
| GPS/telemetry terbaru | `data/latest_nodes.json` |
| Riwayat event GPS/telemetry | `data/events.jsonl` |
| Status message dan metadata report | SQLite, default `data/iov.db` |
| File foto report | `uploads/reports/` |

Direktori runtime, database, upload, `.env`, virtual environment, dan credential sudah dikecualikan melalui `.gitignore`.

## Pengujian

```bash
source .iovvenv/bin/activate
alembic upgrade head
python -m pytest -q
```

## Deployment Singkat

Untuk reverse proxy pada subpath, set prefix yang sama pada aplikasi dan proxy. Contoh:

```bash
export IOV_ROOT_PATH=/riset-iov
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Nginx kemudian meneruskan `/riset-iov/` ke `http://127.0.0.1:8001/`. Jalankan migrasi dengan environment database yang sama sebelum me-restart service.

## Troubleshooting Dasar

| Masalah | Pemeriksaan dan solusi |
| --- | --- |
| `ModuleNotFoundError` | Aktifkan virtualenv dan jalankan `python -m pip install -r requirements.txt`. |
| `unable to open database file` | Buat parent directory database, periksa permission, lalu pastikan `IOV_DATABASE_URL` menunjuk path yang benar. |
| Tabel/kolom database belum tersedia | Jalankan `alembic current` lalu `alembic upgrade head` dengan `IOV_DATABASE_URL` yang sama seperti server. |
| Port sudah digunakan | Periksa dengan `ss -ltnp` lalu gunakan port lain atau hentikan service yang bentrok. |
| Tidak dapat diakses dari perangkat lain | Gunakan `--host 0.0.0.0`, periksa IP host, firewall, dan pastikan kedua perangkat berada pada jaringan yang sama. |
| Map gagal mengambil data pada subpath | Pastikan `IOV_ROOT_PATH` dan location Nginx sama, lalu uji `/health` dan `/broadcast/latest` secara langsung. |
| Upload foto ditolak | Pastikan format JPEG/PNG/WebP, maksimal tiga file, maksimal 5 MB per file, dan batas body proxy mencukupi. |
| Delete report mendapat `401`/`503` | `401` berarti token salah/tidak dikirim; `503` berarti `IOV_ADMIN_TOKEN` belum dikonfigurasi. |
| Backend menghasilkan `500` | Periksa traceback terminal atau `journalctl -u iov-backend -n 100 --no-pager`; untuk Nginx jalankan `nginx -t` dan periksa `/var/log/nginx/error.log`. |

Project ini belum menyediakan user management, autentikasi node yang kuat, rate limiting, atau moderasi report. Tambahkan kontrol tersebut sebelum digunakan sebagai layanan production publik.
