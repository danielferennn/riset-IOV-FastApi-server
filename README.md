# IOV Backend Prototype

Backend prototype untuk sistem Internet of Vehicles (IOV). Project ini menerima data GPS dari perangkat mobile dan data telemetry dari node kendaraan, lalu menampilkan data terbaru melalui REST API dan dashboard peta.

## Fitur

- API backend menggunakan FastAPI.
- Ingest data GPS dari HP.
- Ingest data telemetry dari Raspberry Pi atau node kendaraan.
- Registrasi node prototype dengan PID dummy.
- Snapshot data terbaru semua node.
- Dashboard peta di endpoint `/map`.
- Penyimpanan runtime lokal berbasis JSON/JSONL.

## Tech Stack

- Python
- FastAPI
- Pydantic
- Uvicorn
- Pytest

## Struktur Singkat

```text
app/              source backend
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
| `GET` | `/map` | Dashboard peta |

## Test

```bash
python -m pytest
```