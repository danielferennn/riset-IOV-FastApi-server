# IOV Backend Prototype

Backend prototype untuk sistem Internet of Vehicles (IOV). Project ini menerima data GPS dari perangkat mobile dan data telemetry dari node kendaraan, lalu menampilkan data terbaru melalui REST API dan dashboard peta.

## Fitur

- API backend menggunakan FastAPI.
- Ingest data GPS dari HP.
- Ingest data telemetry dari Raspberry Pi atau node kendaraan.
- Registrasi node prototype dengan PID dummy.
- Snapshot data terbaru semua node.
- Status message singkat pada node dengan masa aktif 2 jam.
- Submit report kondisi jalan dengan lokasi tetap dan foto opsional.
- Dashboard peta di endpoint `/map`.
- Penyimpanan GPS/telemetry runtime berbasis JSON/JSONL.
- Penyimpanan status message berbasis SQLite dan migration Alembic.

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- Uvicorn
- Pytest

## Struktur Singkat

```text
app/              source backend
alembic/          database migration
static/markers/   asset marker peta
tests/            automated test
requirements.txt  dependency Python
```

## Cara Menjalankan

Install dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Siapkan tabel status message:

```bash
alembic upgrade head
```

Jalankan server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Buka:

```text
http://localhost:8000/docs
http://localhost:8000/map
```

## Endpoint Utama

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `GET` | `/health` | Cek status server |
| `POST` | `/nodes/register` | Registrasi node prototype |
| `POST` | `/ingest/gps` | Kirim data GPS |
| `POST` | `/ingest/telemetry` | Kirim data telemetry |
| `GET` | `/broadcast/latest` | Ambil snapshot terbaru semua node |
| `POST` | `/nodes/{node_id}/status-message` | Buat status message; message tertua diganti jika dua slot penuh |
| `GET` | `/nodes/{node_id}/status-message` | Ambil status message aktif |
| `DELETE` | `/nodes/{node_id}/status-message?pid=...` | Hapus status message milik PID |
| `GET` | `/nodes/{node_id}/status-messages` | Ambil riwayat status message |
| `POST` | `/reports` | Submit report kondisi jalan |
| `GET` | `/reports` | Ambil daftar report |
| `GET` | `/reports/{report_id}` | Ambil detail report |
| `GET` | `/map` | Dashboard peta |

Setiap node dapat memiliki maksimal dua status message aktif. Masing-masing message otomatis kedaluwarsa dua jam setelah dipublikasikan. Jika message ketiga dibuat saat dua message masih aktif, message aktif paling lama digantikan, sedangkan riwayatnya tetap disimpan.

## Test

```bash
python -m pytest
```
