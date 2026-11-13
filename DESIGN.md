# Dokumentasi Desain UI/UX: NetCalc IPv4 (Google Stitch Edition)

Dokumen ini menjelaskan arsitektur antarmuka pengguna (UI), pengalaman pengguna (UX), sistem warna, tipografi, komponen, serta 3 state visual pada aplikasi **Kalkulator Subnet & VLSM IPv4** yang mengadopsi prinsip desain **Google Stitch / Material Design**.

---

## 1. Filosofi & Prinsip Desain

1. **Edukatif & Berorientasi Siswa/Guru TKJ**:
   Dirancang khusus untuk pembelajaran Teknik Komputer dan Jaringan (TKJ), menyajikan data teknis dengan kejelasan tinggi serta visualisasi biner yang intuitif.
2. **Umpan Balik Instan (Instant Feedback)**:
   Perubahan input memberikan feedback visual yang jelas dengan animasi halus (`fade-enter`), validasi input deskriptif, dan penanganan kesalahan real-time.
3. **Keteraturan Informasi (Visual Hierarchy)**:
   Metrik-metrik krusial (Network ID, Broadcast, Range Host, Usable Hosts) ditonjolkan melalui kartu metrik tersendiri dengan kode warna yang konsisten.

---

## 2. Sistem Desain & Visual

### 2.1 Palet Warna (Google Stitch Color System)

| Nama Token | Kode Warna (Hex) | Peran Penggunaan |
| :--- | :--- | :--- |
| `google-blue` | `#1a73e8` | Warna utama (Primary), tombol aksi (CTA), network bits, active tab indicator |
| `google-blueHover` | `#1557b0` | State hover untuk tombol utama |
| `google-blueLight` | `#e8f0fe` | Latar belakang aksen, badge CIDR, highlight aktif |
| `google-green` | `#1e8e3e` | State sukses, indikator usable host, kapasitas memadai |
| `google-greenLight`| `#e6f4ea` | Latar meteran sisa alamat bebas |
| `google-red` | `#d93025` | Indikator error, validasi tidak valid, kotak peringatan global |
| `google-redLight` | `#fce8e6` | Latar belakang kartu error dan ikon peringatan |
| `google-yellow` | `#f9ab00` | Aksen peringatan minor |
| `google-grayBg` | `#f8f9fa` | Latar belakang halaman utama (canvas background) |
| `google-graySurface`| `#ffffff`| Latar belakang kartu komponen dan tabel |
| `google-grayBorder` | `#dadce0`| Garis batas kontur kartu, input, dan separator |
| `google-grayText` | `#3c4043` | Warna teks utama body |
| `google-graySecondary`| `#5f6368`| Warna label, teks deskripsi sekunder, petunjuk input |

### 2.2 Tipografi

* **Display / Judul Utama**: `Google Sans`, `Roboto`, sans-serif (bobot 500, 700).
* **Teks Konten (Body)**: `Roboto`, system-ui, sans-serif (bobot 400, 500).
* **Representasi Teknis / Jaringan**: `JetBrains Mono`, `Menlo`, monospace (bobot 400, 500, 600) untuk seluruh alamat IP, subnet mask, representasi biner, dan prefix CIDR.

---

## 3. Komponen Antarmuka Utama

### 3.1 Header & Quick-Switcher Presets
* **Brand Logo**: Ikon processor/jaringan dengan badge `Edu Edition`.
* **State Preview Pills**: Tombol cepat untuk demonstrasi pengujian:
  * `Empty`: Mengosongkan form dan menampilkan state *Awaiting Parameters*.
  * `Success`: Memuat skenario valid dan menampilkan hasil kalkulasi lengkap.
  * `Error`: Memuat skenario invalid untuk menguji penanganan error HTTP 400 dari API backend.

### 3.2 Navigasi Tab
* **Tab 1: Subnet Calculator**: Menghitung batas jaringan, broadcast, rentang host, dan rincian biner untuk subnetting standar.
* **Tab 2: VLSM Subnetting**: Alokasi hierarkis bertingkat berdasarkan daftar kebutuhan host.
* **Indikator Aktif**: Garis bawah biru 3px (`border-bottom: 3px solid #1a73e8`) dengan transisi halus.

### 3.3 Kartu Metrik Hasil Subnet (2x3 / 3x2 Grid)
1. **Subnet Mask**: Menampilkan format desimal (e.g. `255.255.255.0`) dan wildcard mask.
2. **Network Address**: Identitas basis subnet (warna biru `#1a73e8`).
3. **Broadcast Address**: Alamat broadcast ke seluruh host. Menampilkan teks khusus:
   * `"Tidak ada (Point-to-Point /31)"` pada prefix `/31`.
   * `"Tidak ada (Host Route /32)"` pada prefix `/32`.
4. **First Usable Host**: IP host pertama yang valid (warna hijau `#1e8e3e`).
5. **Last Usable Host**: IP host terakhir yang valid (warna hijau `#1e8e3e`).
6. **Usable Host Capacity**: Total host usable dan formula eksponensial ($2^{32-P} - 2$).

### 3.4 Classroom Binary Breakdown
Bagian khusus edukasi yang memecah alamat IP dan Subnet Mask ke format 32-bit biner terpisah titik:
```text
IP Binary   : 11000000.10101000.00001010.00101101
Mask Binary : 11111111.11111111.11111111.00000000
Alokasi Bit : 24 network bits | 8 host bits (2⁸ - 2 = 254 hosts)
```

### 3.5 VLSM Schedule & Utilization Meter Bar
* **Daftar Kebutuhan Dinamis**: Baris kebutuhan dapat ditambah (`Add Subnet Row`) dan dihapus (`Trash icon`) secara interaktif.
* **Tabel Jadwal Alokasi**: Kolom Subnet Name, Req/Usable, Prefix/Mask, Network ID, Usable Range, dan Broadcast ID.
* **Address Space Utilization Bar**: Baris visual dua warna yang menunjukkan persentase ruang alamat yang teralokasi vs sisa IP bebas untuk ekspansi.
* **Export Action**: Tombol unduh laporan ke format file `.csv` dan tombol *Copy Table*.

---

## 4. Tiga State Tampilan UI

Aplikasi menerapkan 3 state tampilan visual pada masing-masing tab:

```text
┌────────────────────────────────────────────────────────┐
│                      TIGA STATE UI                     │
├─────────────────┬──────────────────┬───────────────────┤
│   EMPTY STATE   │  SUCCESS STATE   │    ERROR STATE    │
│  (#...empty-card)│ (#...success-card)│  (#...error-card)  │
│                 │                  │                   │
│ Menampilkan     │ Menampilkan      │ Menampilkan kartu │
│ placeholder     │ kartu metrik &   │ peringatan merah  │
│ instruksi       │ tabel hasil      │ dengan pesan dari │
│ interaktif      │ lengkap          │ field API `detail`│
└─────────────────┴──────────────────┴───────────────────┘
```

1. **Empty State (`#subnet-empty-card`, `#vlsm-empty-card`)**:
   * Aktif saat form dalam kondisi kosong.
   * Menampilkan ilustrasi ikon minimalis, deskripsi petunjuk pengisian, dan tombol ajakan bertindak (*call-to-action*) untuk memuat data contoh guru.
2. **Success State (`#subnet-success-card`, `#vlsm-success-card`)**:
   * Aktif saat request API (`/api/subnet` atau `/api/vlsm`) mengembalikan kode `HTTP 200 OK`.
   * Menampilkan kartu ringkasan hasil kalkulasi, badge status hijau berdenyut (*pulsing indicator*), dan opsi salin/ekspor.
3. **Error State (`#subnet-error-card`, `#vlsm-error-card`)**:
   * Aktif saat request API mengembalikan kode `HTTP 400 Bad Request`.
   * Mengambil pesan deskriptif dari atribut `detail` respons backend.
   * Menyorot kotak peringatan global berlatar belakang merah muda lembut (`bg-red-50/10`) dengan border merah `#d93025`.
   * Menampilkan pesan kesalahan tepat di bawah field input yang bermasalah serta mewarnai border input menjadi merah.
