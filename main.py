"""Kalkulator Subnet & VLSM IPv4.

Modul ini mengimplementasikan logika komputasi subnetting dan alokasi VLSM (Variable
Length Subnet Masking) untuk IPv4 menggunakan operasi bitwise 32-bit integer,
dilengkapi dengan API web berbasis FastAPI.

Dirancang dengan validasi ketat dan dokumentasi komprehensif untuk memudahkan
pembelajaran siswa dan guru Teknik Komputer dan Jaringan (TKJ).
"""

import os
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse


# ==============================================================================
# 1. FUNGSI UTILITAS BINER & OPERASI 32-BIT
# ==============================================================================

def ip_to_int(ip: str) -> int:
    """Mengonversi string alamat IPv4 dotted-decimal menjadi 32-bit unsigned integer.

    Konsep Jaringan (TKJ):
    IPv4 terdiri dari 32 bit yang dibagi menjadi 4 blok (oktet) berukuran 8 bit.
    Setiap oktet digeser ke posisi bobot binernya:
    - Oktet 1 digeser ke kiri 24 bit
    - Oktet 2 digeser ke kiri 16 bit
    - Oktet 3 digeser ke kiri 8 bit
    - Oktet 4 berada di posisi bit terendah (0 bit)

    Args:
        ip (str): Alamat IPv4 valid, contoh "192.168.1.1".

    Returns:
        int: Representasi 32-bit integer unsigned (0 s.d. 4.294.967.295).
    """
    octets = [int(part) for part in ip.split(".")]
    return (
        ((octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3])
        & 0xFFFFFFFF
    )


def int_to_ip(ip_int: int) -> str:
    """Mengonversi 32-bit unsigned integer kembali ke format string IPv4 dotted-decimal.

    Args:
        ip_int (int): Integer 32-bit (0 s.d. 0xFFFFFFFF).

    Returns:
        str: Alamat IPv4 dotted-decimal, contoh "192.168.1.1".
    """
    o1 = (ip_int >> 24) & 0xFF
    o2 = (ip_int >> 16) & 0xFF
    o3 = (ip_int >> 8) & 0xFF
    o4 = ip_int & 0xFF
    return f"{o1}.{o2}.{o3}.{o4}"


def prefix_to_mask_int(prefix: int) -> int:
    """Menghitung nilai 32-bit subnet mask dari prefix CIDR.

    Konsep Jaringan (TKJ):
    Prefix /P berarti P bit pertama bernilai biner 1 dan (32 - P) bit sisanya bernilai 0.
    Contoh: /24 berarti 24 bit angka 1 (11111111.11111111.11111111.00000000) = 255.255.255.0.

    Args:
        prefix (int): Panjang prefix (0 s.d. 32).

    Returns:
        int: Subnet mask dalam 32-bit unsigned integer.
    """
    if prefix == 0:
        return 0
    return ((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF)


# ==============================================================================
# 2. VALIDASI KETAT SESUAI SPESIFIKASI (BAGIAN 2 SPEC.MD)
# ==============================================================================

def validate_ip(ip: str) -> None:
    """Memvalidasi format alamat IPv4 dengan aturan ketat.

    Aturan Validasi:
    1. Tipe data wajib string dan tidak boleh kosong.
    2. Dilarang mengandung karakter spasi (tidak boleh di-trim secara implisit).
    3. Tepat terdiri dari 4 oktet desimal yang dipisahkan titik.
    4. Setiap oktet hanya boleh berisi digit angka desimal (0-9).
    5. Setiap oktet harus bernilai antara 0 sampai 255.
    6. Dilarang memiliki leading zero (angka '0' sah, tetapi '01' atau '001' ditolak).

    Args:
        ip (str): String IP yang akan diperiksa.

    Raises:
        ValueError: Jika format IP melanggar salah satu aturan validasi.
    """
    if not isinstance(ip, str):
        raise ValueError("Alamat IP harus berupa string")

    if ip == "":
        raise ValueError("Alamat IP tidak boleh kosong")

    if " " in ip:
        raise ValueError("Alamat IP tidak boleh mengandung karakter spasi")

    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError(f"Alamat IP harus terdiri dari tepat 4 oktet, ditemukan {len(parts)}")

    for i, part in enumerate(parts, start=1):
        if part == "":
            raise ValueError(f"Oktet ke-{i} tidak boleh kosong")

        if not part.isdigit():
            raise ValueError(f"Oktet ke-{i} ('{part}') bukan angka yang valid")

        # Cek leading zero (contoh: "01", "001")
        if len(part) > 1 and part.startswith("0"):
            raise ValueError(f"Oktet ke-{i} ('{part}') tidak boleh memiliki leading zero")

        val = int(part)
        if val < 0 or val > 255:
            raise ValueError(f"Oktet ke-{i} bernilai {val}, melebihi batas yang diperbolehkan (0-255)")


def validate_prefix(prefix: int) -> None:
    """Memvalidasi prefix CIDR agar berada di rentang 0 sampai 32.

    Catatan Khusus Python:
    Di Python, bool adalah subclass dari int (`isinstance(True, int) == True`).
    Fungsi ini secara eksplisit menolak tipe boolean agar tidak menyamar sebagai int.

    Args:
        prefix (int): Nilai prefix CIDR.

    Raises:
        ValueError: Jika prefix berupa boolean, bukan int, atau di luar rentang 0-32.
    """
    if isinstance(prefix, bool):
        raise ValueError("Prefix tidak boleh berupa nilai boolean")

    if not isinstance(prefix, int):
        raise ValueError("Prefix harus berupa bilangan bulat (integer)")

    if prefix < 0 or prefix > 32:
        raise ValueError(f"Prefix /{prefix} tidak valid. Harus berada dalam rentang 0 sampai 32")


def validate_vlsm_params(network_cidr: str, kebutuhan_host: list[int]) -> tuple[str, int, list[int]]:
    """Memvalidasi parameter alokasi VLSM secara ketat.

    Aturan Validasi:
    1. network_cidr harus string berformat `<ip>/<prefix>` tanpa spasi.
    2. Bagian IP dan prefix harus lulus validasi IPv4 dan CIDR.
    3. IP pada network_cidr WAJIB merupakan Network Address yang sah (ip & mask == ip).
       Jika user memasukkan host address (misal 192.168.1.5/24), input harus ditolak.
    4. kebutuhan_host harus berupa list tidak kosong.
    5. Setiap elemen kebutuhan_host harus integer >= 1 (bukan bool, bukan float, bukan <= 0).

    Args:
        network_cidr (str): Format subnet CIDR, contoh "192.168.1.0/24".
        kebutuhan_host (list[int]): Daftar kebutuhan host tiap segmen.

    Returns:
        tuple[str, int, list[int]]: (base_ip, base_prefix, valid_kebutuhan_list)

    Raises:
        ValueError: Jika salah satu parameter tidak valid.
    """
    if not isinstance(network_cidr, str):
        raise ValueError("network_cidr harus berupa string")

    if network_cidr == "":
        raise ValueError("network_cidr tidak boleh kosong")

    if " " in network_cidr:
        raise ValueError("network_cidr tidak boleh mengandung karakter spasi")

    if "/" not in network_cidr:
        raise ValueError("Format network_cidr harus berupa <ip>/<prefix>")

    parts = network_cidr.split("/")
    if len(parts) != 2:
        raise ValueError("Format network_cidr harus tepat terdiri dari satu karakter '/'")

    ip_str, prefix_str = parts[0], parts[1]

    # Validasi bagian IP
    validate_ip(ip_str)

    # Validasi bagian Prefix
    if prefix_str == "":
        raise ValueError("Prefix CIDR tidak boleh kosong")
    if not prefix_str.isdigit():
        raise ValueError("Prefix CIDR harus berupa bilangan bulat positif")
    if len(prefix_str) > 1 and prefix_str.startswith("0"):
        raise ValueError("Prefix CIDR tidak boleh memiliki leading zero")

    prefix_val = int(prefix_str)
    validate_prefix(prefix_val)

    # Cek keabsahan Network Address (ip & mask == ip)
    ip_int = ip_to_int(ip_str)
    mask_int = prefix_to_mask_int(prefix_val)
    expected_net_int = (ip_int & mask_int) & 0xFFFFFFFF

    if ip_int != expected_net_int:
        sah_ip = int_to_ip(expected_net_int)
        raise ValueError(
            f"Alamat '{ip_str}' bukan network address yang sah untuk prefix /{prefix_val}. "
            f"Network address yang sah adalah '{sah_ip}'"
        )

    # Validasi kebutuhan_host
    if isinstance(kebutuhan_host, bool) or not isinstance(kebutuhan_host, list):
        raise ValueError("kebutuhan_host harus berupa list")

    if len(kebutuhan_host) == 0:
        raise ValueError("Daftar kebutuhan_host tidak boleh kosong")

    for idx, item in enumerate(kebutuhan_host):
        if isinstance(item, bool):
            raise ValueError(f"Elemen kebutuhan_host pada indeks {idx} tidak boleh bernilai boolean")
        if not isinstance(item, int):
            raise ValueError(f"Elemen kebutuhan_host pada indeks {idx} ('{item}') harus berupa bilangan bulat")
        if item < 1:
            raise ValueError(f"Kebutuhan host pada indeks {idx} bernilai {item}, harus minimal 1 host")

    return ip_str, prefix_val, kebutuhan_host


# ==============================================================================
# 3. FUNGSI LOGIKA MURNI (CORE NETWORKING ENGINE)
# ==============================================================================

def hitung_subnet(ip: str, prefix: int) -> dict[str, Any]:
    """Menghitung parameter subnetting IPv4 lengkap berdasarkan IP dan prefix CIDR.

    Mendukung seluruh rentang prefix dari /0 sampai /32 dengan penanganan khusus:
    - Prefix /0 s.d. /30 : Subnetting standar dengan 1 network IP dan 1 broadcast IP.
    - Prefix /31        : Standar RFC 3021 (Point-to-Point links, 2 usable host, tanpa broadcast).
    - Prefix /32        : Host Route tunggal (1 host, tanpa broadcast).

    Rumus Matematika Biner (TKJ):
    - Subnet Mask = 0xFFFFFFFF << (32 - prefix)
    - Wildcard Mask = ~Subnet Mask
    - Network Address = IP & Subnet Mask
    - Broadcast Address = Network Address | Wildcard Mask
    - Host Usable (/0 s.d. /30) = 2^(32 - prefix) - 2

    Args:
        ip (str): Alamat IPv4 (contoh "192.168.1.10").
        prefix (int): Prefix subnetting CIDR (0 s.d. 32).

    Returns:
        dict: Berisi kunci:
            - mask (str): Subnet mask dotted-decimal (misal "255.255.255.0")
            - network (str): Alamat network (misal "192.168.1.0")
            - broadcast (str | None): Alamat broadcast (misal "192.168.1.255" atau None)
            - first_host (str): Alamat host pertama yang dapat digunakan
            - last_host (str): Alamat host terakhir yang dapat digunakan
            - usable_hosts (int): Jumlah host yang dapat digunakan
    """
    validate_ip(ip)
    validate_prefix(prefix)

    ip_int = ip_to_int(ip)
    mask_int = prefix_to_mask_int(prefix)
    wildcard_int = (~mask_int) & 0xFFFFFFFF
    net_int = (ip_int & mask_int) & 0xFFFFFFFF
    bcast_int = (net_int | wildcard_int) & 0xFFFFFFFF

    mask_str = int_to_ip(mask_int)
    net_str = int_to_ip(net_int)
    bcast_str = int_to_ip(bcast_int)

    # Kasus Khusus 1: Prefix /32 (Single Host Route)
    if prefix == 32:
        return {
            "mask": mask_str,
            "network": net_str,
            "broadcast": None,
            "first_host": ip,
            "last_host": ip,
            "usable_hosts": 1,
        }

    # Kasus Khusus 2: Prefix /31 (RFC 3021 - Point-to-Point link)
    if prefix == 31:
        return {
            "mask": mask_str,
            "network": net_str,
            "broadcast": None,
            "first_host": net_str,
            "last_host": int_to_ip(net_int + 1),
            "usable_hosts": 2,
        }

    # Kasus Khusus 3: Prefix /0 (Default Route - Seluruh Ruang IPv4)
    if prefix == 0:
        return {
            "mask": "0.0.0.0",
            "network": "0.0.0.0",
            "broadcast": "255.255.255.255",
            "first_host": "0.0.0.1",
            "last_host": "255.255.255.254",
            "usable_hosts": 4294967294,
        }

    # Kasus Standar: Prefix /1 s.d. /30
    usable_hosts = (1 << (32 - prefix)) - 2
    first_host_str = int_to_ip(net_int + 1)
    last_host_str = int_to_ip(bcast_int - 1)

    return {
        "mask": mask_str,
        "network": net_str,
        "broadcast": bcast_str,
        "first_host": first_host_str,
        "last_host": last_host_str,
        "usable_hosts": usable_hosts,
    }


def alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict[str, Any]]:
    """Mengalokasikan subnet secara hierarkis menggunakan algoritma VLSM.

    Alur Algoritma VLSM (TKJ):
    1. Urutkan daftar kebutuhan host dari yang terbesar ke terkecil (Descending).
       Hal ini penting untuk menghindari fragmentasi ruang alamat IP.
    2. Untuk setiap kebutuhan H, cari ukuran blok pangkat 2 terkecil yang >= (H + 2).
       (+2 dialokasikan untuk 1 Network IP dan 1 Broadcast IP).
    3. Batas minimal subnet adalah /30 (blok 4 IP, menampung 2 host usable).
       Jika kebutuhan 1 host, tetap diberikan blok /30.
    4. Alokasikan subnet berturut-turut mulai dari network awal.
    5. Jika total kebutuhan melebihi kapasitas network induk, raise ValueError (Overflow).

    Args:
        network_cidr (str): Network address induk dan prefix, contoh "192.168.1.0/24".
        kebutuhan_host (list[int]): Daftar kebutuhan host, contoh [100, 50, 20, 2].

    Returns:
        list[dict]: Daftar blok alokasi subnet beserta seluruh properti subnetting.

    Raises:
        ValueError: Jika input tidak valid atau kapasitas network induk tidak mencukupi.
    """
    base_ip_str, base_prefix, valid_kebutuhan = validate_vlsm_params(network_cidr, kebutuhan_host)

    # 1. Urutkan dari kebutuhan terbesar ke terkecil
    sorted_kebutuhan = sorted(valid_kebutuhan, reverse=True)

    base_net_int = ip_to_int(base_ip_str)
    base_capacity = 1 << (32 - base_prefix) if base_prefix < 32 else 1
    base_end_int = base_net_int + base_capacity

    current_net_int = base_net_int
    hasil_alokasi: list[dict[str, Any]] = []

    for h in sorted_kebutuhan:
        # Tentukan ukuran blok (pangkat 2 terkecil >= h + 2, batas minimal 4 [/30])
        needed_ips = h + 2
        block_size = 4
        while block_size < needed_ips:
            block_size <<= 1

        # Hitung prefix baru: 32 - log2(block_size)
        sub_prefix = 32 - (block_size.bit_length() - 1)

        # Cek kapasitas sisa (Deteksi Overflow)
        if current_net_int + block_size > base_end_int:
            raise ValueError("Kapasitas network tidak mencukupi untuk alokasi VLSM yang diminta")

        # Hitung rincian subnet cabang
        current_ip_str = int_to_ip(current_net_int)
        sub_detail = hitung_subnet(current_ip_str, sub_prefix)

        alokasi_item = {
            "kebutuhan": h,
            "network_cidr": f"{sub_detail['network']}/{sub_prefix}",
            "mask": sub_detail["mask"],
            "network": sub_detail["network"],
            "broadcast": sub_detail["broadcast"],
            "first_host": sub_detail["first_host"],
            "last_host": sub_detail["last_host"],
            "usable_hosts": sub_detail["usable_hosts"],
        }
        hasil_alokasi.append(alokasi_item)

        # Majukan penunjuk network ke blok berikutnya
        current_net_int += block_size

    return hasil_alokasi


# ==============================================================================
# 4. FASTAPI WEB APPLICATION & ENDPOINTS
# ==============================================================================

app = FastAPI(
    title="Kalkulator Subnet & VLSM IPv4",
    description="Engine kalkulasi subnetting IPv4 dan alokasi VLSM berbasis FastAPI dengan validasi ketat.",
    version="1.0.0",
)


@app.get("/")
def get_root():
    """Menyajikan halaman antarmuka visual kalkulator web (index.html)."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, "index.html")

    if not os.path.exists(html_file):
        raise HTTPException(status_code=404, detail="File 'index.html' tidak ditemukan")

    return FileResponse(html_file, media_type="text/html")


@app.get("/api/subnet")
def api_get_subnet(ip: str | None = None, prefix: str | None = None):
    """Endpoint API untuk menghitung parameter subnetting IPv4.

    Query Parameters:
        ip (str): Alamat IPv4 (contoh: "192.168.1.1").
        prefix (str): Prefix CIDR berupa string (contoh: "24").
    """
    if ip is None:
        raise HTTPException(status_code=400, detail="Parameter query 'ip' wajib diisi")

    if prefix is None:
        raise HTTPException(status_code=400, detail="Parameter query 'prefix' wajib diisi")

    # Validasi format prefix string untuk menangkap spasi, bilangan desimal/float, dan minus
    if not isinstance(prefix, str) or prefix == "":
        raise HTTPException(status_code=400, detail="Parameter 'prefix' tidak boleh kosong")

    if " " in prefix:
        raise HTTPException(status_code=400, detail="Prefix tidak boleh mengandung spasi")

    if prefix.startswith("-"):
        raise HTTPException(status_code=400, detail="Prefix tidak boleh negatif")

    if not prefix.isdigit():
        raise HTTPException(status_code=400, detail="Prefix harus berupa bilangan bulat antara 0 sampai 32")

    if len(prefix) > 1 and prefix.startswith("0"):
        raise HTTPException(status_code=400, detail="Prefix tidak boleh memiliki leading zero")

    try:
        prefix_int = int(prefix)
    except ValueError:
        raise HTTPException(status_code=400, detail="Prefix tidak valid")

    try:
        result = hitung_subnet(ip, prefix_int)
        return result
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.post("/api/vlsm")
async def api_post_vlsm(request: Request):
    """Endpoint API untuk menghitung alokasi VLSM (Variable Length Subnet Masking).

    Request Body (JSON):
        network (str): CIDR network address induk (contoh: "192.168.1.0/24").
        kebutuhan_host (list[int]): Daftar kebutuhan host (contoh: [100, 50, 20, 2]).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Format payload harus berupa JSON yang valid")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload JSON harus berupa objek (dictionary)")

    if "network" not in payload:
        raise HTTPException(status_code=400, detail="Field 'network' wajib ada dalam payload")

    if "kebutuhan_host" not in payload:
        raise HTTPException(status_code=400, detail="Field 'kebutuhan_host' wajib ada dalam payload")

    network = payload["network"]
    kebutuhan_host = payload["kebutuhan_host"]

    try:
        result = alokasi_vlsm(network, kebutuhan_host)
        return result
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

