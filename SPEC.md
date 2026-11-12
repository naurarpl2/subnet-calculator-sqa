# Spesifikasi Teknis: Kalkulator Subnet & VLSM IPv4

Dokumen ini mendefinisikan spesifikasi arsitektur, aturan validasi, logika perhitungan subnetting & VLSM, spesifikasi antarmuka API, serta skenario pengujian unit (test cases) untuk aplikasi **Kalkulator Subnet & VLSM IPv4**.

---

## 1. Arsitektur & Teknologi

* **Bahasa Pemrograman**: Python 3.12
* **Framework Backend**: FastAPI
* **Server ASGI**: Uvicorn
* **Frontend**: Halaman tunggal `index.html` (menyajikan UI interaktif responsif)
* **Logika & Endpoint**: Seluruh fungsi core networking dan route API berada di `main.py`
* **Unit Testing**: Pytest (`test_main.py`), HTTP client testing menggunakan `httpx` (`TestClient`)
* **Pengujian Cakupan**: `pytest-cov`

---

## 2. Aturan Validasi Ketat & Penanganan Error

Setiap input yang tidak memenuhi kriteria harus memicu:
* **Level Fungsi**: `ValueError` dengan pesan deskriptif.
* **Level API**: HTTP Status `400 Bad Request` dengan format respons JSON:
  ```json
  {
    "detail": "<Pesan error deskriptif>"
  }
  ```

### 2.1 Aturan Validasi IPv4 (`ip`)
1. **Jumlah Oktet**: Harus tepat 4 oktet desimal yang dipisahkan oleh karakter titik (`.`).
2. **Karakter Spasi**: **Tidak boleh ada spasi** di awal, akhir, maupun di tengah string IP. **Dilarang melakukan `.strip()`** secara diam-diam; jika terdapat spasi, input wajib ditolak.
3. **Format Angka**: Setiap oktet hanya boleh berupa digit angka desimal (0-9). Karakter non-numerik (alfabet, simbol) wajib ditolak.
4. **Rentang Nilai**: Setiap oktet harus bernilai integer antara `0` sampai `255` (inklusif).
5. **Leading Zero**: Angka `0` diperbolehkan, namun angka dengan awalan nol (misal: `01`, `001`, `055`) **wajib ditolak**.
6. **String Kosong**: String kosong `""` wajib ditolak.

### 2.2 Aturan Validasi Prefix Subnet (`prefix`)
1. Harus berupa bilangan bulat (integer) dalam rentang `0` sampai `32` (inklusif).
2. Nilai negatif (`< 0`) atau nilai di atas 32 (`> 32`) wajib ditolak.

### 2.3 Aturan Validasi VLSM (`network_cidr` & `kebutuhan_host`)
1. **Format `network_cidr`**: String berformat `<ip>/<prefix>`.
2. **Keabsahan Network Address**: IP pada `network_cidr` **wajib merupakan network address yang sah** ($(\text{ip} \ \& \ \text{mask}) == \text{ip}$). Jika diberikan alamat host (misal `192.168.1.5/24`), input wajib ditolak dengan pesan bahwa alamat tersebut bukan network address.
3. **Kebutuhan Host (`kebutuhan_host`)**:
   - Harus bertipe list.
   - List **tidak boleh kosong** (`[]` ditolak).
   - Setiap elemen harus integer $\ge 1$ (nilai $\le 0$ atau float ditolak).

---

## 3. Spesifikasi Logika Inti

### 3.1 Fungsi `hitung_subnet(ip: str, prefix: int) -> dict`

Menghitung rincian parameter subnetting berdasarkan alamat IP dan prefix CIDR.

#### Skema Nilai Kembalian:
Fungsi mengembalikan dictionary dengan kunci berikut:
* `mask` (*str*): Subnet mask dalam format dotted-decimal (contoh: `"255.255.255.0"`).
* `network` (*str*): Network address (contoh: `"192.168.1.0"`).
* `broadcast` (*str* | *None*): Broadcast address. Bernilai `None` untuk prefix `/31` dan `/32`.
* `first_host` (*str*): Alamat host pertama yang dapat digunakan.
* `last_host` (*str*): Alamat host terakhir yang dapat digunakan.
* `usable_hosts` (*int*): Jumlah alamat host yang dapat digunakan.

#### Ketentuan Kalkulasi Berdasarkan Prefix:
1. **Prefix /0 sampai /30**:
   * $\text{total\_hosts} = 2^{32 - \text{prefix}}$
   * $\text{usable\_hosts} = 2^{32 - \text{prefix}} - 2$
   * `first_host` = $\text{network} + 1$
   * `last_host` = $\text{broadcast} - 1$
   * Khusus prefix `/0`: `network = "0.0.0.0"`, `broadcast = "255.255.255.255"`, `first_host = "0.0.0.1"`, `last_host = "255.255.255.254"`, `usable_hosts = 4294967294`.
2. **Prefix /31 (RFC 3021 - Point-to-Point Links)**:
   * $\text{usable\_hosts} = 2$
   * `broadcast` = `None`
   * `first_host` = $\text{network}$
   * `last_host` = $\text{network} + 1$
3. **Prefix /32 (Single Host Route)**:
   * $\text{usable\_hosts} = 1$
   * `broadcast` = `None`
   * `first_host` = $\text{ip}$
   * `last_host` = $\text{ip}$

---

### 3.2 Fungsi `alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]`

Mengalokasikan blok-blok subnet variabel (VLSM) dari network induk berdasarkan daftar kebutuhan host.

#### Tahapan Algoritma:
1. **Validasi**: Periksa keabsahan `network_cidr` (harus valid & sah sebagai network address) dan `kebutuhan_host` (tidak kosong, semua elemen $\ge 1$).
2. **Pengurutan**: Urutkan daftar kebutuhan host dari nilai terbesar ke terkecil (*descending*).
3. **Penentuan Ukuran Blok**:
   * Untuk setiap kebutuhan $H$, tentukan kapasitas alamat yang dibutuhkan: $H + 2$ (1 untuk network address, 1 untuk broadcast address).
   * Cari ukuran blok sebagai pangkat 2 terkecil yang memenuhi: $\text{blok\_size} = 2^k \ge H + 2$.
   * **Batas Minimal Blok**: Batas minimal subnet adalah `/30` (ukuran blok minimal 4 alamat, menampung 2 usable hosts). Jika $H = 1$, ukuran blok tetap 4 (prefix `/30`).
   * Hitung prefix baru: $\text{sub\_prefix} = 32 - \log_2(\text{blok\_size})$.
4. **Alokasi Berurutan**:
   * Mulai dari alamat network awal blok utama.
   * Lakukan iterasi pengalokasian sekuensial: $\text{current\_ip} + \text{blok\_size}$.
5. **Deteksi Overflow**:
   * Jika pada proses alokasi akumulasi alamat melebihi kapasitas total network induk yang diberikan, fungsi wajib melempar `ValueError` dengan pesan bahwa kapasitas network tidak mencukupi.
6. **Skema Nilai Kembalian**:
   Mengembalikan `list[dict]` di mana setiap dictionary merepresentasikan satu alokasi subnet dengan struktur:
   * `kebutuhan` (*int*): Nilai host yang diminta.
   * `network_cidr` (*str*): Notasi CIDR subnet baru (contoh: `"192.168.1.0/25"`).
   * Semua properti hasil dari `hitung_subnet` (`mask`, `network`, `broadcast`, `first_host`, `last_host`, `usable_hosts`).

---

## 4. Spesifikasi Endpoint API

### 4.1 `GET /`
* **Deskripsi**: Menyajikan antarmuka visual kalkulator subnet & VLSM (`index.html`).
* **Respons**: HTML file (`200 OK`, `Content-Type: text/html`).

### 4.2 `GET /api/subnet`
* **Deskripsi**: Melakukan perhitungan subnetting.
* **Query Parameters**:
  * `ip` (*string*, wajib): Alamat IPv4 (contoh: `192.168.1.10`).
  * `prefix` (*integer*, wajib): Prefix CIDR (0 - 32).
* **Respons Berhasil (200 OK)**:
  ```json
  {
    "mask": "255.255.255.0",
    "network": "192.168.1.0",
    "broadcast": "192.168.1.255",
    "first_host": "192.168.1.1",
    "last_host": "192.168.1.254",
    "usable_hosts": 254
  }
  ```
* **Respons Gagal (400 Bad Request)**:
  ```json
  {
    "detail": "Oktet ke-1 bernilai 256, melebihi batas 255"
  }
  ```

### 4.3 `POST /api/vlsm`
* **Deskripsi**: Melakukan alokasi subnet bertingkat (VLSM).
* **Headers**: `Content-Type: application/json`
* **Request Body**:
  ```json
  {
    "network": "192.168.1.0/24",
    "kebutuhan_host": [100, 50, 20, 2]
  }
  ```
* **Respons Berhasil (200 OK)**:
  ```json
  [
    {
      "kebutuhan": 100,
      "network_cidr": "192.168.1.0/25",
      "mask": "255.255.255.128",
      "network": "192.168.1.0",
      "broadcast": "192.168.1.127",
      "first_host": "192.168.1.1",
      "last_host": "192.168.1.126",
      "usable_hosts": 126
    },
    {
      "kebutuhan": 50,
      "network_cidr": "192.168.1.128/26",
      "mask": "255.255.255.192",
      "network": "192.168.1.128",
      "broadcast": "192.168.1.191",
      "first_host": "192.168.1.129",
      "last_host": "192.168.1.190",
      "usable_hosts": 62
    },
    {
      "kebutuhan": 20,
      "network_cidr": "192.168.1.192/27",
      "mask": "255.255.255.224",
      "network": "192.168.1.192",
      "broadcast": "192.168.1.223",
      "first_host": "192.168.1.193",
      "last_host": "192.168.1.222",
      "usable_hosts": 30
    },
    {
      "kebutuhan": 2,
      "network_cidr": "192.168.1.224/30",
      "mask": "255.255.255.252",
      "network": "192.168.1.224",
      "broadcast": "192.168.1.227",
      "first_host": "192.168.1.225",
      "last_host": "192.168.1.226",
      "usable_hosts": 2
    }
  ]
  ```
* **Respons Gagal (400 Bad Request)**:
  ```json
  {
    "detail": "Kapasitas network tidak mencukupi untuk alokasi VLSM yang diminta"
  }
  ```

---

## 5. Rencana Pengujian: Tabel 21 Test Case (TC-01 sampai TC-21)

| No. Test | Kategori | Input Pengujian | Ekspektasi Output / Hasil yang Diharapkan |
| :--- | :--- | :--- | :--- |
| **TC-01** | Subnet Standar | IP: `192.168.1.0`, Prefix: `25` | `network`: `192.168.1.0`<br>`mask`: `255.255.255.128`<br>`broadcast`: `192.168.1.127`<br>`first_host`: `192.168.1.1`<br>`last_host`: `192.168.1.126`<br>`usable_hosts`: `126` |
| **TC-02** | Subnet Standar | IP: `192.168.1.64`, Prefix: `26` | `network`: `192.168.1.64`<br>`mask`: `255.255.255.192`<br>`broadcast`: `192.168.1.127`<br>`first_host`: `192.168.1.65`<br>`last_host`: `192.168.1.126`<br>`usable_hosts`: `62` |
| **TC-03** | Subnet Standar | IP: `172.16.16.0`, Prefix: `20` | `network`: `172.16.16.0`<br>`mask`: `255.255.240.0`<br>`broadcast`: `172.16.31.255`<br>`first_host`: `172.16.16.1`<br>`last_host`: `172.16.31.254`<br>`usable_hosts`: `4094` |
| **TC-04** | Subnet Standar | IP: `10.0.0.4`, Prefix: `30` | `network`: `10.0.0.4`<br>`mask`: `255.255.255.252`<br>`broadcast`: `10.0.0.7`<br>`first_host`: `10.0.0.5`<br>`last_host`: `10.0.0.6`<br>`usable_hosts`: `2` |
| **TC-05** | Edge Case | IP: `10.0.0.0`, Prefix: `31` (RFC 3021) | `network`: `10.0.0.0`<br>`mask`: `255.255.255.254`<br>`broadcast`: `None`<br>`first_host`: `10.0.0.0`<br>`last_host`: `10.0.0.1`<br>`usable_hosts`: `2` |
| **TC-06** | Edge Case | IP: `192.168.1.1`, Prefix: `32` (Single Host) | `network`: `192.168.1.1`<br>`mask`: `255.255.255.255`<br>`broadcast`: `None`<br>`first_host`: `192.168.1.1`<br>`last_host`: `192.168.1.1`<br>`usable_hosts`: `1` |
| **TC-07** | Edge Case | IP: `0.0.0.0`, Prefix: `0` (Default Route) | `network`: `0.0.0.0`<br>`mask`: `0.0.0.0`<br>`broadcast`: `255.255.255.255`<br>`first_host`: `0.0.0.1`<br>`last_host`: `255.255.255.254`<br>`usable_hosts`: `4294967294` |
| **TC-08** | Edge Case | IP: `255.255.255.255`, Prefix: `24` (IP Broadcast Input) | `network`: `255.255.255.0`<br>`mask`: `255.255.255.0`<br>`broadcast`: `255.255.255.255`<br>`first_host`: `255.255.255.1`<br>`last_host`: `255.255.255.254`<br>`usable_hosts`: `254` |
| **TC-09** | Validasi Negatif | IP: `256.1.1.1`, Prefix: `24` | Memicu `ValueError` / HTTP `400 Bad Request` (Oktet 256 melebihi batas 255). |
| **TC-10** | Validasi Negatif | IP: `192.168.01.1`, Prefix: `24` | Memicu `ValueError` / HTTP `400 Bad Request` (Ditolak karena terdapat leading zero `01`). |
| **TC-11** | Validasi Negatif | IP: `192.168.1`, Prefix: `24` | Memicu `ValueError` / HTTP `400 Bad Request` (Ditolak karena kurang dari 4 oktet). |
| **TC-12** | Validasi Negatif | IP: `abc`, Prefix: `24` | Memicu `ValueError` / HTTP `400 Bad Request` (Ditolak karena bukan format IP numerik). |
| **TC-13** | Validasi Negatif | IP: `""`, Prefix: `24` | Memicu `ValueError` / HTTP `400 Bad Request` (Ditolak karena IP kosong). |
| **TC-14** | Validasi Negatif | IP: `" 192.168.1.1"` atau `"192.168. 1.1"`, Prefix: `24` | Memicu `ValueError` / HTTP `400 Bad Request` (Ditolak karena mengandung karakter spasi, tidak boleh di-trim). |
| **TC-15** | Validasi Negatif | IP: `192.168.1.1`, Prefix: `33` dan `-1` | Memicu `ValueError` / HTTP `400 Bad Request` (Prefix berada di luar batas `0` sampai `32`). |
| **TC-16** | VLSM Normal | Network: `192.168.1.0/24`<br>Kebutuhan: `[100, 50, 20, 2]` | Menghasilkan 4 blok berurutan:<br>1. Subnet /25 (`192.168.1.0/25`), usable: 126<br>2. Subnet /26 (`192.168.1.128/26`), usable: 62<br>3. Subnet /27 (`192.168.1.192/27`), usable: 30<br>4. Subnet /30 (`192.168.1.224/30`), usable: 2 |
| **TC-17** | VLSM Urutan Acak | Network: `192.168.1.0/24`<br>Kebutuhan: `[2, 100, 20, 50]` | Kebutuhan otomatis diurutkan descending menjadi `[100, 50, 20, 2]`. Hasil alokasi subnet identik dengan TC-16. |
| **TC-18** | VLSM Batas Kapasitas | Network: `192.168.1.0/24`<br>Kebutuhan A: `[62]` vs Kebutuhan B: `[63]` | * Kebutuhan `62` ($+2=64$) dialokasikan blok `/26` (kapasitas 64 IP).<br>* Kebutuhan `63` ($+2=65$) dialokasikan blok `/25` (kapasitas 128 IP). |
| **TC-19** | VLSM Batas Bawah | Network: `192.168.1.0/24`<br>Kebutuhan: `[1]` | Kebutuhan 1 host tetap dialokasikan blok minimal `/30` (kapasitas 4 IP, usable 2 host: `192.168.1.0/30`). |
| **TC-20** | VLSM Overflow | Network: `192.168.1.0/24`<br>Kebutuhan: `[200, 100]` | Total kebutuhan ($256 + 128 = 384$ IP) melebihi kapasitas network /24 (256 IP). Memicu `ValueError` / HTTP `400 Bad Request`. |
| **TC-21** | VLSM Input Tidak Valid | 1. Network: `192.168.1.5/24`<br>2. Kebutuhan: `[50, 0]`, `[-5]`, `[]` | Memicu `ValueError` / HTTP `400 Bad Request`:<br>1. Ditolak karena `192.168.1.5` adalah host address, bukan valid network address.<br>2. Ditolak karena kebutuhan bernilai $\le 0$ atau list kebutuhan kosong. |

