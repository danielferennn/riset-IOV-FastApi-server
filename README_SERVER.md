# IOV Backend Prototype

Backend prototype untuk menerima data GPS dari HP dan data telemetry OBD dari Raspberry Pi, lalu membagikan snapshot terbaru semua node melalui REST API.

Prototype ini memiliki 5 node hardcode:

| Node | Device | Data utama |
| --- | --- | --- |
| `raspi-01` | Raspberry Pi | Telemetry OBD |
| `raspi-02` | Raspberry Pi | Telemetry OBD |
| `raspi-03` | Raspberry Pi | Telemetry OBD |
| `phone-01` | HP | GPS |
| `phone-02` | HP | GPS |

> Dokumen ini sengaja dibagi menjadi dua jalur. Bagian A untuk pembuat/administrator backend. Bagian B untuk teman yang mengembangkan aplikasi HP dan Raspi.

Dokumentasi khusus integrasi client tersedia di [README_CLIENT.md](README_CLIENT.md). File tersebut dapat langsung dibagikan kepada developer aplikasi.

## Daftar Isi

- [A. Untuk Pembuat Backend](#a-untuk-pembuat-backend)
- [B. Untuk Developer Aplikasi Node](#b-untuk-developer-aplikasi-node)
- [C. Referensi Endpoint](#c-referensi-endpoint)
- [D. Dashboard Map](#d-dashboard-map)
- [E. Storage Dan Reset Data](#e-storage-dan-reset-data)
- [F. Batasan Keamanan Prototype](#f-batasan-keamanan-prototype)

## A. Untuk Pembuat Backend

### 1. Struktur Proyek

```text
app/
  main.py          # definisi FastAPI dan endpoint
  models.py        # model request dan response
  pid_registry.py  # email, node, dan PID hardcode
  store.py         # penyimpanan JSONL dan snapshot terbaru
  map_view.py      # halaman map
static/markers/    # PNG marker opsional
tests/             # automated test
data/              # data runtime, dibuat otomatis
requirements.txt
README.md
```

### 2. Instalasi Pertama

Jalankan dari folder proyek:

```bash
cd /path/ke/beiov
python3 -m venv .iovvenv
source .iovvenv/bin/activate
pip install -r requirements.txt
```

Jika virtual environment sudah dibuat, cukup jalankan:

```bash
cd /path/ke/beiov
source .iovvenv/bin/activate
```

### 3. Menjalankan Backend

Untuk development di laptop:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Untuk diakses dari laptop/HP/Raspi lain dalam jaringan yang sama:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`0.0.0.0` berarti server mendengarkan koneksi dari semua interface jaringan. Client tidak memakai `0.0.0.0` sebagai URL; client memakai IP perangkat yang menjalankan backend.

Contoh jika backend berjalan di Raspi dengan IP `192.168.1.147`:

```text
BASE_URL=http://192.168.1.147:8000
```

Kemudian map dapat dibuka dari perangkat lain dengan:

```text
http://192.168.1.147:8000/map
```

### 4. Dokumentasi Otomatis

Setelah server berjalan, tersedia:

```text
http://IP_BACKEND:8000/docs       # Swagger UI
http://IP_BACKEND:8000/redoc      # ReDoc
http://IP_BACKEND:8000/map        # Dashboard map
```

Untuk mencoba endpoint melalui Swagger: buka `/docs`, pilih endpoint, klik `Try it out`, isi request body jika diperlukan, lalu klik `Execute`.

### 5. Menjalankan Automated Test

Dengan virtual environment aktif:

```bash
python -m pytest
```

Atau tanpa activate:

```bash
.iovvenv/bin/python -m pytest
```

File `pytest.ini` sudah mengatur import project sehingga error `ModuleNotFoundError: No module named 'app'` tidak muncul saat pytest dijalankan dari root proyek.

### 6. Menentukan Base URL Untuk Client

Base URL tidak disimpan sebagai URL tetap di backend karena nilainya bergantung pada tempat server dijalankan. URL tersebut dikonfigurasi di aplikasi client.

| Kondisi | Base URL client |
| --- | --- |
| Client dan backend di laptop yang sama | `http://localhost:8000` |
| Backend di Raspi, satu jaringan | `http://IP_RASPI:8000` |
| Backend di server internet dengan port terbuka | `http://IP_SERVER:8000` |
| Backend di domain dengan HTTPS/reverse proxy | `https://domain-anda.com` |
| Backend D-COWS di path reverse proxy | `https://dcows.berdikari.pens.ac.id/riset-iov` |

Contoh konfigurasi client:

```python
BASE_URL = "http://192.168.1.147:8000"
```

Pastikan firewall, jaringan, dan port `8000` mengizinkan koneksi dari client.

### 7. Deploy Di Path Domain D-COWS

Bagian ini adalah prosedur deployment aktual untuk server D-COWS. Backend dipasang tanpa subdomain pada path berikut:

```text
https://dcows.berdikari.pens.ac.id/riset-iov
```

Endpoint publik:

```text
https://dcows.berdikari.pens.ac.id/riset-iov/health
https://dcows.berdikari.pens.ac.id/riset-iov/docs
https://dcows.berdikari.pens.ac.id/riset-iov/map
https://dcows.berdikari.pens.ac.id/riset-iov/ingest/gps
https://dcows.berdikari.pens.ac.id/riset-iov/ingest/telemetry
https://dcows.berdikari.pens.ac.id/riset-iov/broadcast/latest
```

#### 7.1 Kirim Source Code Dari Laptop

Server diakses dengan SSH key pada port `1041`. Jalankan dari laptop. Perintah berikut tidak menyalin virtual environment dan tidak menimpa data runtime server.

```bash
tar \
  --exclude='./.iovvenv' \
  --exclude='./.venv' \
  --exclude='./.deps' \
  --exclude='./.pytest_cache' \
  --exclude='./__pycache__' \
  --exclude='./data' \
  -C /home/danielferen/beiov \
  -czf - . | \
ssh -i /home/danielferen/ssh-key-dcows \
  -p 1041 \
  root@dcows.berdikari.pens.ac.id \
  'mkdir -p /root/beiov && tar -xzf - -C /root/beiov'
```

Jika `rsync` sudah tersedia di server, perintah transfer dapat diganti dengan `rsync` melalui SSH key. Metode `tar` di atas tidak memerlukan package `rsync` pada server.

#### 7.2 Instalasi Dan Test Internal Di Server

Masuk ke server:

```bash
ssh -i /home/danielferen/ssh-key-dcows \
  -p 1041 \
  root@dcows.berdikari.pens.ac.id
```

Siapkan virtual environment, dependency, dan direktori data:

```bash
cd /root/beiov
python3 -m venv .iovvenv
source .iovvenv/bin/activate
pip install -r requirements.txt
python -m pytest
mkdir -p /var/lib/iov-backend
```

Untuk uji sementara, jalankan backend hanya pada loopback server menggunakan port internal `8001`:

```bash
IOV_ROOT_PATH=/riset-iov \
IOV_DATA_DIR=/var/lib/iov-backend \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Di terminal SSH kedua, cek:

```bash
curl http://127.0.0.1:8001/health
```

Hasilnya harus `{"status":"ok"}`. Hentikan server uji dengan `Ctrl+C` sebelum mengaktifkan systemd.

#### 7.3 Jalankan Dengan Systemd

Buat `/etc/systemd/system/iov-backend.service`:

```text
nano /etc/systemd/system/iov-backend.service
```

```ini
[Unit]
Description=IOV FastAPI Backend
After=network.target

[Service]
User=root
WorkingDirectory=/root/beiov
Environment="IOV_ROOT_PATH=/riset-iov"
Environment="IOV_DATA_DIR=/var/lib/iov-backend"
ExecStart=/root/beiov/.iovvenv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Aktifkan service:

```bash
systemctl daemon-reload
systemctl enable --now iov-backend
systemctl status iov-backend --no-pager
curl http://127.0.0.1:8001/health
```

Gunakan log berikut saat mendiagnosis service:

```bash
journalctl -u iov-backend -n 50 --no-pager
```

#### 7.4 Tambahkan Reverse Proxy Nginx

Konfigurasi domain berada di `/etc/nginx/sites-enabled/dcows`. Tambahkan blok berikut di dalam `server` HTTPS, sebelum `location /` yang melayani file website utama:

```nginx
location = /riset-iov {
    return 308 /riset-iov/;
}

location ^~ /riset-iov/ {
    proxy_pass http://127.0.0.1:8001/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /riset-iov;
}
```

Trailing slash pada `proxy_pass http://127.0.0.1:8001/;` penting karena Nginx harus menghapus prefix `/riset-iov/` sebelum request diteruskan ke FastAPI.

Validasi dan reload tanpa menghentikan website utama:

```bash
nginx -t
systemctl reload nginx
```

#### 7.5 Verifikasi Domain Dan Konfigurasi Node

Uji endpoint publik:

```bash
curl -k https://dcows.berdikari.pens.ac.id/riset-iov/health
curl -k -I https://dcows.berdikari.pens.ac.id/riset-iov/docs
```

Map dan Swagger tersedia di:

```text
https://dcows.berdikari.pens.ac.id/riset-iov/docs
https://dcows.berdikari.pens.ac.id/riset-iov/map
```

Client HP dan Raspi memakai:

```text
BASE_URL=https://dcows.berdikari.pens.ac.id/riset-iov
```

Saat ini Nginx memakai sertifikat self-signed. `curl -k` hanya untuk test administrator. Aplikasi HP/Raspi biasanya akan menolak sertifikat tersebut, sehingga sertifikat TLS valid harus dipasang sebelum client production menggunakan domain ini.

#### 7.6 Update Source Berikutnya

Jalankan kembali perintah transfer pada langkah 7.1 dari laptop, kemudian di server:

```bash
cd /root/beiov
source .iovvenv/bin/activate
pip install -r requirements.txt
python -m pytest
systemctl restart iov-backend
systemctl status iov-backend --no-pager
```

`pip install -r requirements.txt` hanya perlu dilakukan jika dependency berubah, tetapi aman dijalankan pada setiap update.

### 8. Menjalankan Di Raspberry Pi

Salin source code dari laptop ke Raspi menggunakan `rsync` dari terminal laptop:

```bash
rsync -av \
  --exclude '.iovvenv' \
  --exclude '.venv' \
  --exclude '.deps' \
  --exclude '.pytest_cache' \
  --exclude '__pycache__' \
  --exclude 'data' \
  /home/danielferen/beiov/ \
  raspi@192.168.1.147:/home/raspi/beiov/
```

Perintah tersebut dijalankan di laptop, bukan di dalam sesi SSH Raspi. Setelah selesai, masuk ke Raspi dan install dependency di sana:

```bash
ssh raspi@192.168.1.147
cd /home/raspi/beiov
python3 -m venv .iovvenv
source .iovvenv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Uji dari laptop:

```bash
curl http://192.168.1.147:8000/health
```

Response yang benar:

```json
{"status":"ok"}
```

### 9. Konfigurasi Lokasi Data

Default data berada di `data/`. Untuk menentukan lokasi lain:

```bash
IOV_DATA_DIR=/var/lib/iov-backend \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Pada prototype, folder data cukup dibackup jika ingin menyimpan histori. Folder `data/` tidak perlu disalin dari laptop ketika memindahkan source code ke Raspi.

## B. Untuk Developer Aplikasi Node

Bagian ini adalah kontrak yang perlu diikuti oleh developer aplikasi HP dan Raspberry Pi.

### 1. Yang Perlu Disiapkan

Setiap aplikasi node perlu memiliki:

| Komponen | Keterangan |
| --- | --- |
| `BASE_URL` | Alamat backend, misalnya `http://192.168.1.147:8000` |
| Email node | Email prototype yang sudah terdaftar di tabel assignment |
| HTTP client | `requests`/`httpx`, Retrofit/OkHttp, `http`, atau `fetch` |
| Penyimpanan lokal | Untuk menyimpan `node_id` dan 5 PID |
| Scheduler/timer | Untuk mengirim data berkala |
| Retry dan timeout | Untuk menangani backend tidak tersedia |

Email yang tersedia:

| Email | `node_id` | `device_type` |
| --- | --- | --- |
| `raspi@example.com` | `raspi-01` | `raspi` |
| `raspi2@example.com` | `raspi-02` | `raspi` |
| `raspi3@example.com` | `raspi-03` | `raspi` |
| `phone1@example.com` | `phone-01` | `phone` |
| `phone2@example.com` | `phone-02` | `phone` |

### 2. Alur Startup Aplikasi

```text
1. Client membaca BASE_URL dan email dari konfigurasi.
2. Client memanggil POST /nodes/register.
3. Client menyimpan node_id dan daftar pids dari response.
4. Client memilih PID saat mengirim data.
5. Client mulai mengirim GPS atau telemetry sesuai jenis device.
6. Jika perlu melihat node lain, client polling GET /broadcast/latest.
```

Register dilakukan ulang hanya jika data `node_id`/`pids` belum tersimpan atau storage lokal dihapus.

### 3. Register Node

```http
POST {BASE_URL}/nodes/register
Content-Type: application/json
```

Request:

```json
{
  "email": "phone1@example.com"
}
```

Response:

```json
{
  "email": "phone1@example.com",
  "node_id": "phone-01",
  "device_type": "phone",
  "pids": [
    "pid_64b79ea172304899be1170aa",
    "pid_1fb8f25e8c4d4f91bbd30e72",
    "pid_773a12f01f224ca78db11939",
    "pid_f8b412c67e194ebba0e9c4dd",
    "pid_aa0391787f5c42f59478be02"
  ]
}
```

Simpan response tersebut secara lokal. PID bersifat khusus untuk `node_id` terkait dan tidak boleh ditukar antar node.

### 4. Strategi Memakai PID

Setiap node memiliki 5 PID hardcode. Untuk simulasi pergantian identitas, client dapat memakai round-robin:

```text
request 1 -> pids[0]
request 2 -> pids[1]
request 3 -> pids[2]
request 4 -> pids[3]
request 5 -> pids[4]
request 6 -> kembali ke pids[0]
```

Server prototype belum membuat PID baru dan belum mengaitkan PID dengan sesi login. Jangan menganggap mekanisme ini sudah aman untuk produksi.

### 5. Aplikasi HP: Kirim GPS

HP hanya mengirim GPS. HP tidak perlu dan tidak boleh mengirim telemetry untuk desain prototype ini.

```http
POST {BASE_URL}/ingest/gps
Content-Type: application/json
```

Payload minimal:

```json
{
  "node_id": "phone-01",
  "pid": "pid_64b79ea172304899be1170aa",
  "lat": -6.2,
  "lon": 106.816666
}
```

Payload lengkap:

```json
{
  "node_id": "phone-01",
  "pid": "pid_64b79ea172304899be1170aa",
  "lat": -6.2,
  "lon": 106.816666,
  "accuracy_m": 8.5,
  "speed_mps": 2.1,
  "heading_deg": 90,
  "altitude_m": 15.2,
  "timestamp": "2026-07-27T08:00:00Z"
}
```

Aturan field GPS:

| Field | Wajib | Aturan |
| --- | --- | --- |
| `node_id` | Ya | Harus node HP yang terdaftar |
| `pid` | Ya | Harus salah satu dari 5 PID node tersebut |
| `lat` | Ya | Angka antara `-90` dan `90` |
| `lon` | Ya | Angka antara `-180` dan `180` |
| `accuracy_m` | Tidak | Akurasi dalam meter, minimal `0` |
| `speed_mps` | Tidak | Kecepatan dalam meter/detik, minimal `0` |
| `heading_deg` | Tidak | `0` sampai kurang dari `360` |
| `altitude_m` | Tidak | Ketinggian dalam meter |
| `timestamp` | Tidak | ISO 8601; jika kosong server mengisi waktu saat request |

Kirim data setiap 1 sampai 5 detik untuk testing. Jangan mengirim latitude/longitude kosong sebelum GPS memperoleh location fix.

### 6. Aplikasi Raspi: Kirim Telemetry

Raspi membaca nilai dari OBD atau sumber sensor, kemudian mengirim:

```http
POST {BASE_URL}/ingest/telemetry
Content-Type: application/json
```

Payload utama:

```json
{
  "node_id": "raspi-01",
  "pid": "pid_3f9a0c8e12d44bb7a98f21cd",
  "battery": 78.5,
  "fuel_level_pct": 63,
  "speed_kph": 42,
  "odometer_km": 12034.5,
  "temperature_c": 87
}
```

Field telemetry:

| Field | Wajib | Aturan |
| --- | --- | --- |
| `node_id` | Ya | Harus node Raspi yang terdaftar |
| `pid` | Ya | Harus salah satu dari 5 PID node tersebut |
| `battery` | Tidak | Persentase baterai, `0` sampai `100` |
| `fuel_level_pct` | Tidak | Persentase `0` sampai `100` |
| `speed_kph` | Tidak | Km/jam, minimal `0` |
| `odometer_km` | Tidak | Kilometer, minimal `0` |
| `temperature_c` | Tidak | Celsius |
| `extra` | Tidak | Object untuk data tambahan |
| `timestamp` | Tidak | ISO 8601; jika kosong server mengisi waktu saat request |

Contoh data tambahan:

```json
{
  "node_id": "raspi-01",
  "pid": "pid_3f9a0c8e12d44bb7a98f21cd",
  "battery": 78.5,
  "fuel_level_pct": 63,
  "speed_kph": 42,
  "odometer_km": 12034.5,
  "temperature_c": 87,
  "extra": {
    "engine_load_pct": 32.5,
    "intake_temp_c": 41,
    "obd_protocol": "ISO 15765-4 CAN"
  }
}
```

Telemetry dikirim setiap 1 sampai 5 detik untuk prototype. Jika nilai sensor belum tersedia, field opsional boleh bernilai `null` atau tidak dikirim.

### 7. Mengambil Data Semua Node

Semua node dapat mengambil data terbaru melalui REST polling:

```http
GET {BASE_URL}/broadcast/latest
```

Response berupa array 5 snapshot node. Setiap snapshot memiliki `latest_gps` dan `latest_telemetry`. Untuk node HP, `latest_telemetry` memang selalu `null`; untuk node Raspi, data GPS dapat `null` jika Raspi belum mengirim GPS.

Contoh bentuk response:

```json
[
  {
    "node_id": "phone-01",
    "pids": ["pid_..."],
    "latest_gps": {
      "node_id": "phone-01",
      "pid": "pid_...",
      "lat": -6.2,
      "lon": 106.816666,
      "accuracy_m": null,
      "speed_mps": null,
      "heading_deg": null,
      "altitude_m": null,
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
      "pid": "pid_...",
      "battery": 78.5,
      "fuel_level_pct": 63,
      "speed_kph": 42,
      "odometer_km": 12034.5,
      "temperature_c": 87,
      "extra": {},
      "timestamp": "2026-07-27T08:00:01Z"
    }
  }
]
```

Polling setiap 1 sampai 5 detik cukup untuk prototype. Client yang gagal terhubung sebaiknya menyimpan data terakhir yang valid dan mencoba kembali pada interval berikutnya.

### 8. Penyimpanan Konfigurasi Client

Minimal simpan object seperti berikut di storage lokal aplikasi:

```json
{
  "base_url": "http://192.168.1.147:8000",
  "email": "raspi@example.com",
  "node_id": "raspi-01",
  "pids": ["pid_...", "pid_...", "pid_...", "pid_...", "pid_..."],
  "pid_index": 0
}
```

Implementasinya dapat memakai file config, SQLite lokal, SharedPreferences, secure storage, atau mekanisme penyimpanan sesuai platform.

### 9. Library Client Yang Dapat Dipakai

| Platform | Pilihan HTTP client |
| --- | --- |
| Raspi Python | `requests` atau `httpx` |
| Android Kotlin | Retrofit atau OkHttp |
| Flutter | `http` atau `dio` |
| React Native | `fetch` atau `axios` |

Kontrak API tetap sama pada semua platform: method, URL, header JSON, nama field, dan response mengikuti bagian C.

## C. Referensi Endpoint

Semua endpoint, kecuali `/map`, dapat dicoba dari Swagger di `{BASE_URL}/docs`.

### `GET /health`

Memeriksa apakah backend hidup.

Response `200`:

```json
{"status":"ok"}
```

### `POST /nodes/register`

Mencocokkan email hardcode dengan `node_id`, tipe device, dan 5 PID.

Request:

```json
{"email":"raspi@example.com"}
```

Response `200`: object `email`, `node_id`, `device_type`, dan `pids`.

Response `404` jika email belum ada di registry:

```json
{"detail":"email node tidak terdaftar"}
```

### `GET /pids`

Mengembalikan seluruh assignment node dan PID. Endpoint ini untuk debugging/administrasi prototype, bukan untuk dipakai sebagai mekanisme keamanan client.

### `GET /nodes/{node_id}/pids`

Mengembalikan 5 PID untuk satu node. Response `404` jika node tidak ditemukan.

### `POST /ingest/gps`

Menyimpan GPS terbaru node dan menambahkan event ke `events.jsonl`. Validasi PID dilakukan sebelum penyimpanan.

Response `200` berbentuk:

```json
{
  "event_type": "gps",
  "node_id": "phone-01",
  "pid": "pid_...",
  "timestamp": "2026-07-27T08:00:00Z",
  "payload": {}
}
```

### `POST /ingest/telemetry`

Menyimpan telemetry terbaru Raspi dan menambahkan event ke `events.jsonl`. Field tambahan diperbolehkan karena model telemetry menggunakan `extra="allow"`.

### `GET /nodes`

Mengembalikan snapshot terbaru seluruh node. Pada prototype hasilnya sama dengan `/broadcast/latest`.

### `GET /broadcast/latest`

Endpoint utama untuk distribusi data ke semua node dan dashboard map melalui REST polling.

### `GET /nodes/{node_id}/latest`

Mengembalikan snapshot terbaru satu node. Response `404` jika `node_id` tidak ditemukan.

### `GET /events?limit=100`

Mengembalikan event terbaru dari buffer memory. `limit` bernilai `1` sampai `500` dan default-nya `100`. Endpoint ini berguna untuk debugging; histori lengkap berada di `data/events.jsonl`.

### `GET /map`

Membuka dashboard map prototype. Halaman ini polling `/broadcast/latest` setiap 2 detik dan hanya menampilkan marker untuk node yang memiliki `latest_gps`.

### `WS /ws/maps`

Endpoint WebSocket tersedia untuk eksperimen event realtime, tetapi alur utama prototype tetap menggunakan REST. Developer client tidak perlu memakai endpoint ini sekarang.

### Status Error Yang Perlu Ditangani

| Status | Penyebab | Tindakan |
| --- | --- | --- |
| `200` | Request sukses | Proses response |
| `403` | PID bukan milik node_id | Gunakan PID dari register node yang sama |
| `404` | Email atau node tidak ditemukan | Periksa mapping dan URL |
| `422` | JSON/field/range tidak valid | Periksa nama dan tipe field |
| Timeout/connection error | Backend tidak dapat dijangkau | Periksa IP, port, jaringan, dan server |

## D. Dashboard Map

Buka:

```text
http://IP_BACKEND:8000/map
```

Fitur map prototype:

- marker hanya muncul setelah node mengirim GPS;
- setiap node hanya ditampilkan satu kali di sidebar;
- label menggunakan PID aktif, bukan `node_id`;
- hover pada marker atau item sidebar menampilkan data node;
- Raspi memakai marker kendaraan;
- HP memakai marker pedestrian;
- data telemetry hanya ditampilkan untuk Raspi;
- data node diperbarui dengan polling REST.

Jika ingin menggunakan PNG marker sendiri, letakkan file berikut:

```text
static/markers/pedestrian.png
static/markers/vehicle.png
```

PNG sebaiknya memiliki background transparan. Jika file tidak tersedia, aplikasi memakai marker fallback bawaan. Kredit ikon Flaticon yang dipakai sebagai referensi ada di dalam halaman map.

Tile peta memakai Leaflet dan OpenStreetMap melalui CDN, sehingga browser membutuhkan akses internet untuk menampilkan peta dasar.

## E. Storage Dan Reset Data

### Format Storage

Backend memakai file teks JSON:

```text
data/events.jsonl       # histori event append-only
data/latest_nodes.json  # snapshot terbaru tiap node
```

`events.jsonl` bertambah setiap ada GPS atau telemetry baru. `latest_nodes.json` dipakai agar data terbaru dapat dibaca dengan cepat saat server berjalan atau setelah restart.

### Membersihkan Data Runtime

Hentikan server terlebih dahulu, lalu dari root proyek jalankan:

```bash
rm -rf data
```

Kemudian jalankan server kembali. Folder `data/` akan dibuat lagi saat data baru masuk. Perintah ini menghapus histori event dan snapshot terbaru, sehingga gunakan hanya saat memang ingin reset data prototype.

Alternatif yang lebih terkontrol adalah memindahkan folder data untuk backup:

```bash
mv data data-backup-$(date +%Y%m%d-%H%M%S)
```

Pada deployment dengan `IOV_DATA_DIR`, bersihkan direktori yang ditentukan oleh variable tersebut, bukan folder `data/` di source code.

## F. Batasan Keamanan Prototype

Implementasi saat ini dibuat untuk presentasi dan testing jaringan lokal:

- email, node, dan PID masih hardcode;
- belum ada password, API key, bearer token, atau autentikasi device;
- semua node yang mengetahui `BASE_URL` dapat mencoba endpoint broadcast;
- PID hanya divalidasi terhadap `node_id`, bukan bukti kepemilikan sesi;
- data disimpan dalam file lokal, belum memakai database multi-user;
- server development belum memakai HTTPS secara langsung;
- WebSocket tersedia tetapi bukan jalur utama.

Untuk deployment produksi, perlu ditambahkan autentikasi node, HTTPS, rate limiting, validasi timestamp/replay, database yang sesuai, backup, logging, dan reverse proxy.

## Ringkasan Alur Sistem

```text
Backend start
    |
    v
Client register dengan email
    |
    v
Backend mengembalikan node_id + 5 PID hardcode
    |
    +--> HP mengirim GPS --------+
    |                            |
    +--> Raspi mengirim telemetry+
                                 v
                        Storage JSONL + snapshot terbaru
                                 |
                                 v
             Semua node / map mengambil GET /broadcast/latest
```
