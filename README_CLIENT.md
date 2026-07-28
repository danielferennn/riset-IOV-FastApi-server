# IOV Backend API: Panduan Client

Dokumen ringkas untuk developer aplikasi HP dan Raspberry Pi yang mengirim atau mengambil data dari backend IOV.

## 1. Konfigurasi

Gunakan base URL berikut pada aplikasi client:

```text
BASE_URL=https://dcows.berdikari.pens.ac.id/riset-iov
```

Contoh URL lengkap:

```text
https://dcows.berdikari.pens.ac.id/riset-iov/health
https://dcows.berdikari.pens.ac.id/riset-iov/ingest/gps
https://dcows.berdikari.pens.ac.id/riset-iov/ingest/telemetry
https://dcows.berdikari.pens.ac.id/riset-iov/broadcast/latest
```

Jangan menambahkan trailing slash pada `BASE_URL`.

Saat dokumentasi ini dibuat, sertifikat HTTPS server masih self-signed. `curl -k` pada dokumen ini hanya untuk test manual. Aplikasi HP/Raspi tidak boleh mematikan validasi TLS atau memakai `verify=False`; gunakan domain untuk aplikasi setelah administrator memasang sertifikat HTTPS yang valid.

Untuk test dari terminal:

```bash
export BASE_URL="https://dcows.berdikari.pens.ac.id/riset-iov"
```

## 2. Alur Client

```text
1. Set BASE_URL.
2. POST /nodes/register menggunakan email node.
3. Simpan node_id dan 5 PID dari response.
4. HP POST GPS, Raspi POST telemetry.
5. Poll GET /broadcast/latest jika perlu data node lain.
```

Simpan minimal data berikut pada local storage aplikasi:

```json
{
  "base_url": "https://dcows.berdikari.pens.ac.id/riset-iov",
  "email": "raspi@example.com",
  "node_id": "raspi-01",
  "pids": ["pid_...", "pid_...", "pid_...", "pid_...", "pid_..."],
  "pid_index": 0
}
```

## 3. Node Prototype

| Email | `node_id` | Tipe | Data utama |
| --- | --- | --- | --- |
| `raspi@example.com` | `raspi-01` | `raspi` | Telemetry |
| `raspi2@example.com` | `raspi-02` | `raspi` | Telemetry |
| `raspi3@example.com` | `raspi-03` | `raspi` | Telemetry |
| `phone1@example.com` | `phone-01` | `phone` | GPS |
| `phone2@example.com` | `phone-02` | `phone` | GPS |

## 4. Daftar Endpoint

| Method | Endpoint | Kegunaan |
| --- | --- | --- |
| `GET` | `/health` | Cek backend hidup |
| `POST` | `/nodes/register` | Mendapatkan `node_id` dan 5 PID |
| `GET` | `/pids` | Semua pool PID, debugging |
| `GET` | `/nodes/{node_id}/pids` | PID satu node |
| `POST` | `/ingest/gps` | Kirim GPS dari HP |
| `POST` | `/ingest/telemetry` | Kirim telemetry dari Raspi |
| `GET` | `/nodes` | Snapshot terbaru semua node |
| `GET` | `/broadcast/latest` | Data terbaru semua node untuk polling |
| `GET` | `/nodes/{node_id}/latest` | Snapshot satu node |
| `GET` | `/events?limit=100` | Event terbaru, debugging |
| `GET` | `/map` | Dashboard peta |
| `WS` | `/ws/maps` | Opsional, belum diperlukan untuk prototype |

Endpoint JSON selalu berbentuk:

```text
{BASE_URL}/nama-endpoint
```

Semua `POST` JSON wajib memakai header:

```http
Content-Type: application/json
```

## 5. Endpoint Utama

### `GET /health`

```bash
curl -k "${BASE_URL}/health"
```

Response:

```json
{"status":"ok"}
```

### `POST /nodes/register`

Panggil saat aplikasi belum memiliki konfigurasi node.

```bash
curl -k -X POST "${BASE_URL}/nodes/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"raspi@example.com"}'
```

Request:

```json
{"email":"raspi@example.com"}
```

Response:

```json
{
  "email": "raspi@example.com",
  "node_id": "raspi-01",
  "device_type": "raspi",
  "pids": [
    "pid_3f9a0c8e12d44bb7a98f21cd",
    "pid_81c2fb771a0945c4b62e03aa",
    "pid_f4d812bafe98490ab2731e28",
    "pid_20b17e5f10fd4cd4a9cb743e",
    "pid_a9374b8267d140a1802a935c"
  ]
}
```

Response `404` jika email tidak terdaftar:

```json
{"detail":"email node tidak terdaftar"}
```

### `POST /ingest/gps`

Endpoint utama aplikasi HP. Kirim hanya setelah device memiliki GPS fix.

```bash
curl -k -X POST "${BASE_URL}/ingest/gps" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id":"phone-01",
    "pid":"pid_64b79ea172304899be1170aa",
    "lat":-6.2,
    "lon":106.816666,
    "accuracy_m":8.5
  }'
```

| Field | Wajib | Aturan |
| --- | --- | --- |
| `node_id` | Ya | Contoh `phone-01` |
| `pid` | Ya | PID milik `node_id` tersebut |
| `lat` | Ya | Angka `-90` sampai `90` |
| `lon` | Ya | Angka `-180` sampai `180` |
| `accuracy_m` | Tidak | Meter, minimal `0` |
| `speed_mps` | Tidak | Meter/detik, minimal `0` |
| `heading_deg` | Tidak | `0` sampai kurang dari `360` |
| `altitude_m` | Tidak | Meter |
| `timestamp` | Tidak | ISO 8601; default waktu server |

`speed_mps` adalah kecepatan hasil GPS HP. Field ini opsional dan boleh tidak dikirim.

### `POST /ingest/telemetry`

Endpoint utama Raspi. Field baterai resmi adalah `battery`, dalam persen `0` sampai `100`.

```bash
curl -k -X POST "${BASE_URL}/ingest/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id":"raspi-01",
    "pid":"pid_3f9a0c8e12d44bb7a98f21cd",
    "battery":78.5,
    "fuel_level_pct":63,
    "speed_kph":42,
    "odometer_km":12034.5,
    "temperature_c":87
  }'
```

| Field | Wajib | Aturan |
| --- | --- | --- |
| `node_id` | Ya | Contoh `raspi-01` |
| `pid` | Ya | PID milik `node_id` tersebut |
| `battery` | Tidak | Persen `0` sampai `100` |
| `fuel_level_pct` | Tidak | Persen `0` sampai `100` |
| `speed_kph` | Tidak | Km/jam, minimal `0` |
| `odometer_km` | Tidak | Kilometer, minimal `0` |
| `temperature_c` | Tidak | Celsius |
| `extra` | Tidak | Object untuk sensor/OBD tambahan |
| `timestamp` | Tidak | ISO 8601; default waktu server |

Contoh data tambahan:

```json
{
  "extra": {
    "engine_load_pct": 32.5,
    "intake_temp_c": 41
  }
}
```

### Response Ingest

Kedua endpoint ingest mengembalikan event seperti ini:

```json
{
  "event_type": "telemetry",
  "node_id": "raspi-01",
  "pid": "pid_3f9a0c8e12d44bb7a98f21cd",
  "timestamp": "2026-07-27T08:00:01Z",
  "payload": {}
}
```

## 6. Mengambil Data Node Lain

### `GET /broadcast/latest`

Ini endpoint utama untuk node mengambil kondisi terbaru node lain.

```bash
curl -k "${BASE_URL}/broadcast/latest"
```

Response adalah array snapshot seluruh node:

```json
[
  {
    "node_id": "phone-01",
    "pids": ["pid_..."],
    "latest_gps": {
      "node_id": "phone-01",
      "pid": "pid_64b79ea172304899be1170aa",
      "lat": -6.2,
      "lon": 106.816666,
      "timestamp": "2026-07-27T08:00:00Z"
    },
    "latest_telemetry": null
  },
  {
    "node_id": "raspi-01",
    "pids": ["pid_..."],
    "latest_gps": null,
    "latest_telemetry": {
      "node_id": "raspi-01",
      "pid": "pid_3f9a0c8e12d44bb7a98f21cd",
      "battery": 78.5,
      "speed_kph": 42,
      "timestamp": "2026-07-27T08:00:01Z"
    }
  }
]
```

Untuk menampilkan PID yang benar-benar dipakai saat data terakhir dikirim:

```text
PID aktif = latest_gps.pid atau latest_telemetry.pid
```

Jangan memakai `pids[0]` sebagai PID aktif; `pids` adalah seluruh pool 5 PID. Untuk implementasi umum:

```text
active_pid = node.latest_gps?.pid || node.latest_telemetry?.pid
```

`GET /nodes` memiliki response yang sama dengan `/broadcast/latest` pada prototype ini.

### Endpoint GET Lain

```bash
curl -k "${BASE_URL}/nodes/raspi-01/latest"
curl -k "${BASE_URL}/nodes/phone-01/pids"
curl -k "${BASE_URL}/pids"
curl -k "${BASE_URL}/events?limit=20"
```

- `/nodes/{node_id}/latest`: data terbaru satu node.
- `/nodes/{node_id}/pids`: pool PID satu node.
- `/pids`: seluruh pool PID, hanya untuk debugging.
- `/events?limit=20`: event terbaru, `limit` dari `1` sampai `500`; hanya untuk debugging.

## 7. PID, Interval, Dan Error

Setiap node memiliki 5 PID. Untuk prototype, client dapat melakukan round-robin per interval PID, misalnya setiap 60 detik:

```text
pid = pids[pid_index]
pid_index = (pid_index + 1) modulo jumlah_PID
```

Interval yang disarankan:

| Aktivitas | Interval |
| --- | --- |
| HP mengirim GPS | 1 sampai 5 detik |
| Raspi mengirim telemetry | 1 sampai 5 detik |
| Client polling broadcast | 1 sampai 5 detik |
| Rotasi PID | 30 sampai 60 detik |

| Status | Arti | Tindakan |
| --- | --- | --- |
| `200` | Berhasil | Proses response |
| `403` | PID bukan milik node | Pakai PID dari hasil register node yang sama |
| `404` | Email/node tidak ada | Cek email atau `node_id` |
| `422` | Body JSON tidak valid | Cek field wajib, tipe, dan range nilai |
| Timeout | Server tidak dapat dijangkau | Retry pada interval berikutnya |

Untuk deployment D-COWS, client tidak perlu dan tidak boleh menambahkan port `8001`; port tersebut hanya digunakan internal antara Nginx dan FastAPI.

## 8. Map Dan Swagger

```text
{BASE_URL}/docs   # Swagger UI
{BASE_URL}/redoc  # ReDoc
{BASE_URL}/map    # Dashboard map
```

Map menggunakan REST polling `/broadcast/latest`. WebSocket `/ws/maps` tersedia, tetapi belum diperlukan untuk prototype.

## 9. Checklist Integrasi

- [ ] `BASE_URL` memakai domain D-COWS.
- [ ] `GET /health` berhasil.
- [ ] Client register dengan email yang benar.
- [ ] `node_id`, PID pool, dan indeks rotasi disimpan lokal.
- [ ] Semua POST memakai `Content-Type: application/json`.
- [ ] HP mengirim `lat` dan `lon` valid.
- [ ] Raspi mengirim `battery`, fuel, speed, odometer, dan temperatur jika tersedia.
- [ ] Client dapat membaca `/broadcast/latest` dan mengambil PID aktif dari `latest_gps.pid` atau `latest_telemetry.pid`.
- [ ] Client menangani `403`, `404`, `422`, dan timeout.
- [ ] Sertifikat HTTPS valid sudah dipasang sebelum aplikasi mobile dipakai di lapangan.
