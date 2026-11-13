# [Feature] Kalkulator Alokasi Subnet VLSM (Variable Length Subnet Masking)

## 📌 Deskripsi

Mengembangkan modul perhitungan dan alokasi **Variable Length Subnet Masking (VLSM)** IPv4 secara hierarkis pada aplikasi NetCalc IPv4. Fitur ini memungkinkan pengguna (khususnya guru dan siswa SMK TKJ) untuk merencanakan pembagian blok subnet IP secara optimal berdasarkan daftar kebutuhan host aktual, meminimalkan pemborosan alamat IP (*IP address wasting*).

Fitur ini mencakup logika pengurutan kebutuhan descending, penentuan ukuran blok pangkat 2 terdekat ($2^k \ge H + 2$) dengan batas minimal prefix `/30`, deteksi batas kapasitas (*subnet overflow*), validasi network address sah, API endpoint `POST /api/vlsm`, serta antarmuka visual dinamis pada tab VLSM di `index.html`.

---

## 📋 Daftar Tugas (Task List)

- [ ] **Alur Kerja TDD & Pengujian (`test_main.py`)**:
  - [ ] Menyusun test case VLSM dengan `pytest.mark.parametrize` mencakup TC-16 sampai TC-21.
  - [ ] Memastikan pengujian unit fungsi murni `alokasi_vlsm` dan integration test `POST /api/vlsm`.
  - [ ] Memverifikasi status RED (gagal) pada kerangka stub awal sebelum implementasi.
- [ ] **Backend Core Engine (`main.py`)**:
  - [ ] Implementasi validasi ketat `validate_vlsm_params` (keabsahan network address murni, list kebutuhan tidak kosong, elemen integer $\ge 1$).
  - [ ] Implementasi fungsi `alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]`.
  - [ ] Implementasi endpoint `POST /api/vlsm` dengan HTTP status 200 untuk alokasi sukses dan HTTP status 400 untuk input tidak valid / overflow.
- [ ] **Frontend Interaktif (`index.html`)**:
  - [ ] Menghubungkan formulir VLSM ke endpoint `POST /api/vlsm` via `fetch()`.
  - [ ] Manajemen baris kebutuhan host dinamis (tambah, edit, hapus).
  - [ ] Visualisasi 3 state (Empty, Success, Error) dengan umpan balik pesan kesalahan dari atribut `detail`.
  - [ ] Meteran utilisasi alamat IP dan ekspor tabel alokasi CSV.
- [ ] **Integrasi CI & Review**:
  - [ ] Menjalankan pipeline CI di GitHub Actions hingga hijau 100%.
  - [ ] Membuka Pull Request dan melakukan merge ke branch `main`.

---

## 🎯 Kriteria Penerimaan (Acceptance Criteria)

Merujuk pada **Tabel Test Case VLSM (TC-16 sampai TC-21)** pada Bagian 5 `SPEC.md`:

| ID Test | Kategori | Input Pengujian | Kriteria Hasil yang Diharapkan |
| :--- | :--- | :--- | :--- |
| **TC-16** | VLSM Normal | Network: `192.168.1.0/24`<br>Kebutuhan: `[100, 50, 20, 2]` | 4 blok subnet berurutan:<br>1. `192.168.1.0/25` (126 host)<br>2. `192.168.1.128/26` (62 host)<br>3. `192.168.1.192/27` (30 host)<br>4. `192.168.1.224/30` (2 host) |
| **TC-17** | VLSM Urutan Acak | Network: `192.168.1.0/24`<br>Kebutuhan: `[2, 100, 20, 50]` | Kebutuhan otomatis diurutkan descending menjadi `[100, 50, 20, 2]`. Hasil alokasi identik dengan TC-16. |
| **TC-18** | VLSM Batas | 1. Kebutuhan `[62]`<br>2. Kebutuhan `[63]` | 1. Kebutuhan `62` ($+2=64$) dialokasikan ke blok `/26` (kapasitas 64 IP).<br>2. Kebutuhan `63` ($+2=65$) dialokasikan ke blok `/25` (kapasitas 128 IP). |
| **TC-19** | VLSM Minimal | Network: `192.168.1.0/24`<br>Kebutuhan: `[1]` | Kebutuhan 1 host tetap dialokasikan ke blok minimal `/30` (kapasitas 4 IP, 2 usable host: `192.168.1.0/30`). |
| **TC-20** | VLSM Overflow | Network: `192.168.1.0/24`<br>Kebutuhan: `[200, 100]` | Total kebutuhan ($256 + 128 = 384$ IP) melebihi kapasitas network /24 (256 IP). Melempar `ValueError` / HTTP `400 Bad Request`. |
| **TC-21** | VLSM Input Tidak Valid | 1. Network: `192.168.1.5/24`<br>2. Kebutuhan: `[50, 0]`, `[-5]`, `[]` | Melempar `ValueError` / HTTP `400 Bad Request`:<br>1. Ditolak jika IP bukan valid network address.<br>2. Ditolak jika kebutuhan host $\le 0$, float, atau list kosong. |

---

## 🔄 Alur Kerja Pengembangan (Workflow)

```text
[Issue #] ──> [Branch feature/issue-#-vlsm] ──> [Test Dulu (RED)] ──> [Implementasi (GREEN)] ──> [Commit] ──> [Pull Request] ──> [CI Pipeline] ──> [Merge]
```
