# [Feature] Kalkulator Subnet & VLSM IPv4

## 📌 Deskripsi

Mengembangkan aplikasi berbasis web modern dan interaktif **"Kalkulator Subnet & VLSM IPv4"** (NetCalc IPv4 Edu Edition) yang dirancang untuk membantu siswa dan guru Teknik Komputer dan Jaringan (TKJ) dalam memahami serta menghitung subnetting IPv4 standar (FLSM) dan alokasi hierarkis Variable Length Subnet Masking (VLSM).

Aplikasi ini menggunakan backend Python 3.12 dengan framework FastAPI berkinerja tinggi, logika biner murni 32-bit unsigned integer, validasi input sangat ketat, serta antarmuka web responsif satu halaman (`index.html`) berbasis Google Stitch design system.

---

## 📋 Daftar Tugas (Task List)

- [ ] **Spesifikasi & Desain**:
  - [x] Menyusun spesifikasi teknis lengkap (`SPEC.md`) mencakup aturan validasi, formula biner, skema API, dan tabel 21 test cases.
  - [x] Mendokumentasikan desain antarmuka dan sistem visual (`DESIGN.md`).
- [ ] **Backend & Core Engine (`main.py`)**:
  - [ ] Implementasi fungsi biner 32-bit: `ip_to_int`, `int_to_ip`, `prefix_to_mask_int`.
  - [ ] Implementasi validasi ketat sesuai Bagian 2 `SPEC.md` (`validate_ip`, `validate_prefix`, `validate_vlsm_params`).
  - [ ] Implementasi fungsi logika murni `hitung_subnet(ip: str, prefix: int) -> dict`.
  - [ ] Implementasi fungsi logika murni `alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]`.
  - [ ] Implementasi endpoint FastAPI:
    - `GET /`: menyajikan `index.html`.
    - `GET /api/subnet`: kalkulasi subnet via query parameter `ip` dan `prefix`.
    - `POST /api/vlsm`: kalkulasi VLSM via JSON body `network` dan `kebutuhan_host`.
- [ ] **Frontend Interaktif (`index.html`)**:
  - [ ] Menghubungkan form Subnet ke endpoint `GET /api/subnet` via `fetch()`.
  * Menangani kasus khusus broadcast `null` pada prefix `/31` ("Tidak ada (Point-to-Point /31)") dan `/32` ("Tidak ada (Host Route /32)").
  - [ ] Menghubungkan form VLSM ke endpoint `POST /api/vlsm` via `fetch()`.
  - [ ] Menambahkan manajemen baris kebutuhan host dinamis (tambah, hapus, update).
  - [ ] Mengimplementasikan 3 state tampilan (Empty, Success, Error) dengan umpan balik pesan `detail` HTTP 400.
  - [ ] Menghadirkan Classroom Binary Breakdown dan meteran utilisasi ruang alamat IP.
- [ ] **Pengujian & Kualitas Perangkat Lunak (`test_main.py`)**:
  - [ ] Unit testing komprehensif menggunakan `pytest` untuk fungsi murni `hitung_subnet` dan `alokasi_vlsm`.
  - [ ] Integration testing menggunakan `fastapi.testclient.TestClient` untuk seluruh endpoint API.
  - [ ] Memastikan seluruh 21 skenario test case (TC-01 s.d. TC-21) lulus 100% dengan cakupan kode tinggi (>95%).

---

## 🎯 Kriteria Penerimaan (Acceptance Criteria)

Kriteria penerimaan merujuk langsung pada **Tabel 21 Test Case** pada Bagian 5 `SPEC.md`:

| ID Test | Kategori | Input Pengujian | Kriteria Hasil yang Diharapkan |
| :--- | :--- | :--- | :--- |
| **TC-01** | Subnet Standar | IP: `192.168.1.0`, Prefix: `25` | `network: 192.168.1.0`, `mask: 255.255.255.128`, `broadcast: 192.168.1.127`, `first_host: 192.168.1.1`, `last_host: 192.168.1.126`, `usable_hosts: 126` |
| **TC-02** | Subnet Standar | IP: `192.168.1.64`, Prefix: `26` | `network: 192.168.1.64`, `mask: 255.255.255.192`, `broadcast: 192.168.1.127`, `first_host: 192.168.1.65`, `last_host: 192.168.1.126`, `usable_hosts: 62` |
| **TC-03** | Subnet Standar | IP: `172.16.16.0`, Prefix: `20` | `network: 172.16.16.0`, `mask: 255.255.240.0`, `broadcast: 172.16.31.255`, `first_host: 172.16.16.1`, `last_host: 172.16.31.254`, `usable_hosts: 4094` |
| **TC-04** | Subnet Standar | IP: `10.0.0.4`, Prefix: `30` | `network: 10.0.0.4`, `mask: 255.255.255.252`, `broadcast: 10.0.0.7`, `first_host: 10.0.0.5`, `last_host: 10.0.0.6`, `usable_hosts: 2` |
| **TC-05** | Edge Case | IP: `10.0.0.0`, Prefix: `31` (RFC 3021) | `network: 10.0.0.0`, `mask: 255.255.255.254`, `broadcast: None`, `first_host: 10.0.0.0`, `last_host: 10.0.0.1`, `usable_hosts: 2` |
| **TC-06** | Edge Case | IP: `192.168.1.1`, Prefix: `32` (Single Host) | `network: 192.168.1.1`, `mask: 255.255.255.255`, `broadcast: None`, `first_host: 192.168.1.1`, `last_host: 192.168.1.1`, `usable_hosts: 1` |
| **TC-07** | Edge Case | IP: `0.0.0.0`, Prefix: `0` (Default Route) | `network: 0.0.0.0`, `mask: 0.0.0.0`, `broadcast: 255.255.255.255`, `first_host: 0.0.0.1`, `last_host: 255.255.255.254`, `usable_hosts: 4294967294` |
| **TC-08** | Edge Case | IP: `255.255.255.255`, Prefix: `24` | `network: 255.255.255.0`, `mask: 255.255.255.0`, `broadcast: 255.255.255.255`, `first_host: 255.255.255.1`, `last_host: 255.255.255.254`, `usable_hosts: 254` |
| **TC-09** | Validasi Negatif | IP: `256.1.1.1`, Prefix: `24` | Melempar `ValueError` / HTTP `400 Bad Request` dengan payload `{"detail": "..."}` karena oktet melebihi 255. |
| **TC-10** | Validasi Negatif | IP: `192.168.01.1`, Prefix: `24` | Melempar `ValueError` / HTTP `400 Bad Request` karena leading zero `01`. |
| **TC-11** | Validasi Negatif | IP: `192.168.1`, Prefix: `24` | Melempar `ValueError` / HTTP `400 Bad Request` karena kurang dari 4 oktet. |
| **TC-12** | Validasi Negatif | IP: `abc`, Prefix: `24` | Melempar `ValueError` / HTTP `400 Bad Request` karena non-numerik. |
| **TC-13** | Validasi Negatif | IP: `""`, Prefix: `24` | Melempar `ValueError` / HTTP `400 Bad Request` karena IP kosong. |
| **TC-14** | Validasi Negatif | IP: `" 192.168.1.1"` atau `"192.168. 1.1"` | Melempar `ValueError` / HTTP `400 Bad Request` karena mengandung spasi (tidak boleh di-trim). |
| **TC-15** | Validasi Negatif | Prefix: `33` dan `-1` | Melempar `ValueError` / HTTP `400 Bad Request` karena prefix di luar batas 0–32. |
| **TC-16** | VLSM Normal | Network: `192.168.1.0/24`, Kebutuhan: `[100, 50, 20, 2]` | Alokasi 4 blok berurutan: `192.168.1.0/25` (126 host), `192.168.1.128/26` (62 host), `192.168.1.192/27` (30 host), `192.168.1.224/30` (2 host). |
| **TC-17** | VLSM Acak | Network: `192.168.1.0/24`, Kebutuhan: `[2, 100, 20, 50]` | Otomatis diurutkan descending menjadi `[100, 50, 20, 2]`, hasil alokasi identik dengan TC-16. |
| **TC-18** | VLSM Batas | Kebutuhan `[62]` vs `[63]` | Kebutuhan `62` dialokasikan ke `/26` (64 IP). Kebutuhan `63` dialokasikan ke `/25` (128 IP). |
| **TC-19** | VLSM Minimal | Kebutuhan `[1]` | Kebutuhan 1 host tetap dialokasikan ke blok minimal `/30` (4 IP, 2 usable host: `192.168.1.0/30`). |
| **TC-20** | VLSM Overflow | Network: `192.168.1.0/24`, Kebutuhan: `[200, 100]` | Melempar `ValueError` / HTTP `400 Bad Request` karena total kebutuhan melebihi 256 IP. |
| **TC-21** | VLSM Invalid | 1. Network: `192.168.1.5/24`<br>2. Kebutuhan: `[50, 0]`, `[-5]`, `[]` | Melempar `ValueError` / HTTP `400 Bad Request`:<br>1. Alamat host ditolak (wajib valid network address).<br>2. Kebutuhan host $\le 0$ atau list kosong ditolak. |

---

## 🔄 Alur Kerja Pengembangan (Workflow)

Pengembangan fitur ini mengikuti prinsip **Test-Driven Development (TDD)** dan siklus GitHub Flow standar:

```text
[Issue] ──> [Branch] ──> [Test Dulu (TDD)] ──> [Implementasi] ──> [Commit] ──> [Pull Request] ──> [CI] ──> [Merge]
```

1. **Issue**: Membuat tiket issue pelacakan fitur ini di GitHub Repository.
2. **Branch**: Membuat branch fitur baru dari branch `main` dengan format `feature/issue-<nomor>-subnet-calculator`.
3. **Test Dulu (TDD)**: Menyusun skenario pengujian di `test_main.py` berdasarkan 21 kriteria penerimaan sebelum implementasi kode.
4. **Implementasi**: Menulis logika biner di `main.py` dan menghubungkan antarmuka di `index.html`.
5. **Commit**: Melakukan commit bertahap dengan konvensi *Conventional Commits* (misal: `docs: ...`, `feat: ...`, `test: ...`).
6. **Pull Request**: Membuka PR ke branch `main` dengan mereferensikan issue terkait (`Closes #<nomor>`).
7. **CI**: Menjalankan automated test suite di pipeline CI untuk menjamin 100% pass rate dan code coverage tinggi.
8. **Merge**: Menggabungkan PR ke branch `main` setelah review dan verifikasi sukses.
