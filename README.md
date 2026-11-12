# Kalkulator Subnet IPv4 Berbasis Web (SQA Edition)

Aplikasi web modern, responsif, dan akurat untuk menghitung subnetting IPv4 dengan validasi ketat serta rangkaian pengujian otomatis **Software Quality Assurance (SQA)** yang menerapkan metode *Equivalence Partitioning (EP)* dan *Boundary Value Analysis (BVA)*.

---

## 🌟 Fitur Utama

1. **Input Fleksibel**:
   - Mendukung input terpisah (Alamat IP + Prefix/CIDR).
   - Mendukung format gabungan CIDR (misal: `192.168.1.55/24`).
   - Prefix selector interaktif: Input angka, dropdown daftar subnet mask lengkap (/0 hingga /32), dan range slider.
   - Preset cepat untuk skenario umum (Home LAN, Small Office, Kelas A/B, Point-to-Point /30, RFC 3021 /31, Host Route /32).

2. **Output Lengkap & Terperinci**:
   - **Network Address** (Alamat Jaringan)
   - **Broadcast Address** (Alamat Broadcast)
   - **Rentang Host Usable** (First Host - Last Host)
   - **Jumlah Host Usable** ($2^{32 - \text{prefix}} - 2$) & Total Alamat IP
   - **Subnet Mask** (Format Dotted Decimal)
   - **Wildcard Mask**
   - **Notasi CIDR**
   - **Kelas IP** (Class A, B, C, D, E)
   - **Scope / Kategori IP** (Private RFC 1918, Public, Loopback RFC 1122, APIPA, dsb.)
   - **Representasi Biner 32-Bit** untuk IP, Subnet Mask, Wildcard, Network, dan Broadcast
   - **Visualisasi Bit Alokasi** (Network Bits vs Host Bits)

3. **Penanganan Kasus Khusus (Edge Cases)**:
   - `/32`: Host route tunggal (1 host, Loopback/VPN).
   - `/31`: Point-to-Point links menurut standard **RFC 3021** (2 usable hosts tanpa broadcast address terbuang).
   - `/0`: Default route rute internet penuh ($4.294.967.294$ host usable).

4. **Fitur Ekstra**:
   - **Pembagian Subnet (FLSM)**: Membagi blok network induk menjadi subnet-subnet anak dengan prefix yang diinginkan.
   - **Riwayat Kalkulasi**: Tersimpan otomatis di `localStorage` peramban.
   - **1-Click Copy**: Tombol salin per kartu metrik dan tombol *Salin Ringkasan* berformat teks rapi.
   - **Dark Mode / Light Mode**: Desain modern dengan dukungan tema gelap dan terang.
   - **SQA In-Browser Runner**: Eksekusi 50 test case langsung di halaman web dengan pelaporan visual real-time (waktu eksekusi, status Pass/Fail).

---

## 📐 Rumus Kalkulasi Subnetting

Diberikan sebuah IP dan Prefix $P$ ($0 \le P \le 32$):

1. **Subnet Mask**:
   $$\text{Mask} = (0\text{xFFFFFFFF} \ll (32 - P)) \ \& \ 0\text{xFFFFFFFF}$$

2. **Wildcard Mask**:
   $$\text{Wildcard} = \sim\text{Mask}$$

3. **Network Address**:
   $$\text{Network} = \text{IP} \ \& \ \text{Mask}$$

4. **Broadcast Address**:
   $$\text{Broadcast} = \text{Network} \ | \ \text{Wildcard}$$

5. **Jumlah Host Usable**:
   $$\text{Usable Hosts} = 
   \begin{cases} 
   1 & \text{jika } P = 32 \\ 
   2 & \text{jika } P = 31 \text{ (RFC 3021)} \\ 
   2^{32 - P} - 2 & \text{jika } 0 \le P \le 30 
   \end{cases}$$

6. **Rentang Host Usable**:
   - Host Pertama: $\text{Network} + 1$ (kecuali $/31$ dan $/32$)
   - Host Terakhir: $\text{Broadcast} - 1$ (kecuali $/31$ dan $/32$)

---

## 🚀 Cara Menjalankan

### Cara 1: Buka Langsung di Peramban (Tanpa Server)
Cukup klik ganda atau buka file `index.html` menggunakan peramban web apa pun (Google Chrome, Microsoft Edge, Firefox, dll).

### Cara 2: Menjalankan Server Lokal (Node.js)
```bash
npm start
```
Buka browser pada alamat: [http://localhost:3000](http://localhost:3000)

### Cara 3: Menjalankan Automated SQA Test Suite
```bash
npm test
```
atau
```bash
node test/subnet.test.js
```

---

## 🧪 Rincian SQA Test Suite

Pengujian otomatis mencakup 50 skenario pengujian:

| Kategori | Metode | Deskripsi Kasus Uji |
| :--- | :--- | :--- |
| **Kategori 1** | Equivalence Partitioning | Subnet Class C standar `/24` (Network, Broadcast, Range, Usable, Mask, Class, Type) |
| **Kategori 2** | Equivalence Partitioning | Subnet Class B `/16` dan Class A `/8` |
| **Kategori 3** | Boundary Value Analysis | Batas atas prefix: `/30` (P2P), `/31` (RFC 3021), `/32` (Host Route) |
| **Kategori 4** | Boundary Value Analysis | Batas bawah prefix: `/0` (Default Route $0.0.0.0/0$) |
| **Kategori 5** | Functional Testing | Parsing notasi gabungan CIDR (misal: `192.168.10.70/26`) |
| **Kategori 6** | Negative & Robustness | Validasi input oktet >255, oktet negatif, IP kosong, spasi, huruf, prefix >32, prefix negatif |
| **Kategori 7** | Functional Testing | Pembagian subnet (FLSM) `/24` menjadi 4 blok `/26` |

---

## 📁 Struktur Direktori

```
subnet-calculator-sqa/
├── index.html            # Antarmuka web utama
├── style.css             # Desain CSS modern & responsif (Dark/Light mode)
├── package.json          # Metadata & script npm test/start
├── README.md             # Dokumentasi proyek & rumus
├── js/
│   ├── calculator.js     # Engine kalkulasi subnetting & validasi (UMD Module)
│   └── app.js            # Controller UI, event listener, history, FLSM, & SQA runner
└── test/
    └── subnet.test.js    # Node.js automated test runner (50 test cases)
```

