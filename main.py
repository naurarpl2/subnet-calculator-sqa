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
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse


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
        str: String IPv4, contoh "192.168.1.1".
    """
    return (
        f"{(ip_int >> 24) & 0xFF}."
        f"{(ip_int >> 16) & 0xFF}."
        f"{(ip_int >> 8) & 0xFF}."
        f"{ip_int & 0xFF}"
    )


def prefix_to_mask_int(prefix: int) -> int:
    """Menghitung 32-bit integer subnet mask dari prefix CIDR.

    Konsep Jaringan (TKJ):
    Prefix /N berarti N bit pertama bernilai 1 (network bits) dan sisanya bernilai 0
    (host bits). Misalnya /24 berarti 24 bit bernilai 1.

    Args:
        prefix (int): Nilai prefix CIDR (0 s.d. 32).

    Returns:
        int: Subnet mask dalam bentuk 32-bit unsigned integer.
    """
    if prefix == 0:
        return 0
    return ((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF)


# ==============================================================================
# 2. VALIDASI KETAT INPUT IP & PREFIX
# ==============================================================================

def validate_ip(ip: str) -> None:
    """Memvalidasi format string IPv4 secara ketat sesuai spesifikasi (SPEC.md 2.1).

    Aturan:
    1. Tipe data harus string.
    2. Tidak boleh ada spasi (di awal, akhir, atau tengah - tidak boleh di-strip).
    3. Tepat 4 oktet desimal yang dipisahkan oleh '.'.
    4. Setiap oktet hanya berisi digit desimal (0-9).
    5. Setiap oktet bernilai antara 0 sampai 255.
    6. Leading zero dilarang (misal '01', '001' tidak sah; '0' sah).
    7. String kosong ditolak.

    Args:
        ip (str): String alamat IPv4.

    Raises:
        ValueError: Jika format alamat IP melanggar salah satu aturan di atas.
    """
    if not isinstance(ip, str):
        raise ValueError("Alamat IP harus berupa string")

    if ip == "":
        raise ValueError("Alamat IP tidak boleh kosong")

    if " " in ip:
        raise ValueError("Alamat IP tidak boleh mengandung karakter spasi")

    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError(
            f"Alamat IP harus terdiri dari tepat 4 oktet, diterima {len(parts)} oktet"
        )

    for idx, part in enumerate(parts, start=1):
        if part == "":
            raise ValueError(f"Oktet ke-{idx} tidak boleh kosong")

        if not part.isdigit():
            raise ValueError(
                f"Oktet ke-{idx} ('{part}') mengandung karakter non-numerik"
            )

        if len(part) > 1 and part.startswith("0"):
            raise ValueError(
                f"Oktet ke-{idx} ('{part}') memiliki leading zero yang dilarang"
            )

        val = int(part)
        if val < 0 or val > 255:
            raise ValueError(
                f"Oktet ke-{idx} bernilai {val}, melebihi rentang yang diizinkan (0-255)"
            )


def validate_prefix(prefix: Any) -> int:
    """Memvalidasi nilai prefix subnet mask secara ketat (SPEC.md 2.2).

    Aturan:
    1. Nilai harus berupa integer (bukan boolean, bukan float).
    2. Berada dalam rentang 0 sampai 32 (inklusif).

    Args:
        prefix (Any): Nilai prefix yang akan divalidasi.

    Returns:
        int: Nilai prefix yang telah diverifikasi sebagai integer.

    Raises:
        ValueError: Jika tipe atau rentang prefix tidak valid.
    """
    if isinstance(prefix, bool):
        raise ValueError("Prefix tidak boleh berupa nilai boolean")

    if not isinstance(prefix, int):
        raise ValueError("Prefix harus berupa bilangan bulat (integer)")

    if prefix < 0 or prefix > 32:
        raise ValueError(
            f"Prefix bernilai {prefix}, berada di luar rentang valid (0 s.d. 32)"
        )

    return prefix


# ==============================================================================
# 3. FUNGSI LOGIKA MURNI: hitung_subnet
# ==============================================================================

def hitung_subnet(ip: str, prefix: int) -> dict:
    """Menghitung parameter subnetting IPv4 menggunakan operasi bitwise 32-bit.

    Rumus & Konsep Jaringan (TKJ):
    - Subnet Mask = N bit 1 diikuti (32 - N) bit 0.
    - Network Address = IP bitwise-AND Subnet Mask (`ip & mask`).
    - Broadcast Address = Network Address bitwise-OR Wildcard Mask (`network | (~mask)`).
    - Host Pertama = Network Address + 1 (kecuali /31 dan /32).
    - Host Terakhir = Broadcast Address - 1 (kecuali /31 dan /32).
    - Usable Hosts:
      * /0 s.d. /30 : 2^(32 - prefix) - 2
      * /31         : 2 host (RFC 3021 untuk link point-to-point tanpa broadcast terpisah)
      * /32         : 1 host (Host route tunggal)

    Args:
        ip (str): Alamat IPv4 dotted-decimal.
        prefix (int): Nilai prefix CIDR (0 s.d. 32).

    Returns:
        dict: Dictionary berisi `mask`, `network`, `broadcast`, `first_host`,
              `last_host`, dan `usable_hosts`.

    Raises:
        ValueError: Jika input IP atau prefix tidak valid.
    """
    validate_ip(ip)
    val_prefix = validate_prefix(prefix)

    ip_int = ip_to_int(ip)
    mask_int = prefix_to_mask_int(val_prefix)

    # Operasi Bitwise Inti:
    # 1. Network Address: IP AND Mask
    network_int = (ip_int & mask_int) & 0xFFFFFFFF
    # 2. Wildcard Mask: Negasi bitwise dari Subnet Mask
    wildcard_int = (~mask_int) & 0xFFFFFFFF
    # 3. Broadcast Address: Network OR Wildcard
    broadcast_int = (network_int | wildcard_int) & 0xFFFFFFFF

    mask_str = int_to_ip(mask_int)
    network_str = int_to_ip(network_int)

    # Kasus Khusus Prefix /31 (RFC 3021 Point-to-Point Links)
    if val_prefix == 31:
        return {
            "mask": mask_str,
            "network": network_str,
            "broadcast": None,
            "first_host": network_str,
            "last_host": int_to_ip((network_int + 1) & 0xFFFFFFFF),
            "usable_hosts": 2,
        }

    # Kasus Khusus Prefix /32 (Single Host Route)
    if val_prefix == 32:
        return {
            "mask": mask_str,
            "network": network_str,
            "broadcast": None,
            "first_host": network_str,
            "last_host": network_str,
            "usable_hosts": 1,
        }

    # Kasus Khusus Prefix /0 (Default Route 0.0.0.0/0)
    if val_prefix == 0:
        return {
            "mask": "0.0.0.0",
            "network": "0.0.0.0",
            "broadcast": "255.255.255.255",
            "first_host": "0.0.0.1",
            "last_host": "255.255.255.254",
            "usable_hosts": 4294967294,
        }

    # Kasus Standar Prefix /1 sampai /30
    broadcast_str = int_to_ip(broadcast_int)
    first_host_str = int_to_ip((network_int + 1) & 0xFFFFFFFF)
    last_host_str = int_to_ip((broadcast_int - 1) & 0xFFFFFFFF)
    usable_hosts = (1 << (32 - val_prefix)) - 2

    return {
        "mask": mask_str,
        "network": network_str,
        "broadcast": broadcast_str,
        "first_host": first_host_str,
        "last_host": last_host_str,
        "usable_hosts": usable_hosts,
    }


# ==============================================================================
# 4. FUNGSI LOGIKA MURNI: alokasi_vlsm
# ==============================================================================

def validate_vlsm_params(network_cidr: str, kebutuhan_host: list[int]) -> tuple[str, int]:
    """Memvalidasi parameter alokasi VLSM secara ketat (SPEC.md 2.3)."""
    if not isinstance(network_cidr, str):
        raise ValueError("Network CIDR harus berupa string")

    if "/" not in network_cidr:
        raise ValueError("Format network CIDR tidak valid, gunakan format '<ip>/<prefix>'")

    parts = network_cidr.split("/")
    if len(parts) != 2:
        raise ValueError("Format network CIDR harus tepat '<ip>/<prefix>'")

    ip_part, prefix_part = parts[0], parts[1]
    validate_ip(ip_part)

    if prefix_part == "" or " " in prefix_part or "." in prefix_part:
        raise ValueError("Prefix CIDR harus berupa bilangan bulat positif")

    try:
        prefix = int(prefix_part)
    except ValueError:
        raise ValueError(f"Prefix CIDR '{prefix_part}' bukan angka integer valid")

    validate_prefix(prefix)

    ip_int = ip_to_int(ip_part)
    mask_int = prefix_to_mask_int(prefix)
    if (ip_int & mask_int) != ip_int:
        raise ValueError(
            f"Alamat IP '{ip_part}' bukan valid network address untuk prefix /{prefix}. "
            f"Gunakan alamat network yang sah."
        )

    if not isinstance(kebutuhan_host, list):
        raise ValueError("Kebutuhan host harus berupa list")

    if len(kebutuhan_host) == 0:
        raise ValueError("Daftar kebutuhan host tidak boleh kosong")

    for idx, req in enumerate(kebutuhan_host, start=1):
        if isinstance(req, bool) or not isinstance(req, int):
            raise ValueError(f"Kebutuhan host ke-{idx} harus berupa integer")
        if req <= 0:
            raise ValueError(
                f"Kebutuhan host ke-{idx} bernilai {req}, harus berupa integer >= 1"
            )

    return ip_part, prefix


def alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]:
    """Mengalokasikan blok-blok subnet variabel (VLSM) secara hierarkis.

    Belum diimplementasikan (Tahap RED TDD).
    """
    raise NotImplementedError("Fungsi alokasi_vlsm belum diimplementasikan")


# ==============================================================================
# 5. APLIKASI FASTAPI & ENDPOINT ROUTE
# ==============================================================================

app = FastAPI(
    title="Kalkulator Subnet & VLSM IPv4",
    description="API Edukasi Jaringan Komputer untuk Perhitungan Subnetting dan VLSM",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Mengubah error validasi default FastAPI (HTTP 422) menjadi HTTP 400 dengan field 'detail'."""
    first_error = exc.errors()[0]
    msg = first_error.get("msg", "Format input tidak valid")
    return JSONResponse(
        status_code=400,
        content={"detail": msg},
    )


@app.get("/", response_class=FileResponse)
def read_root():
    """Menyajikan halaman antarmuka web index.html."""
    index_file = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(index_file):
        index_file = "index.html"
    return FileResponse(index_file, media_type="text/html")


@app.get("/api/subnet")
def api_subnet(request: Request):
    """Endpoint untuk melakukan perhitungan subnetting IPv4."""
    ip = request.query_params.get("ip")
    prefix_raw = request.query_params.get("prefix")

    if ip is None or prefix_raw is None:
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'ip' dan 'prefix' wajib disertakan",
        )

    try:
        validate_ip(ip)

        if prefix_raw == "" or " " in prefix_raw:
            raise ValueError("Prefix tidak boleh kosong atau mengandung karakter spasi")

        if "." in prefix_raw:
            raise ValueError("Prefix harus berupa bilangan bulat, bukan bilangan desimal")

        try:
            prefix = int(prefix_raw)
        except ValueError:
            raise ValueError(f"Prefix '{prefix_raw}' bukan representasi integer yang valid")

        validate_prefix(prefix)

        return hitung_subnet(ip, prefix)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.post("/api/vlsm")
async def api_vlsm(request: Request):
    """Endpoint untuk melakukan alokasi subnet VLSM bertingkat."""
    raise HTTPException(
        status_code=501,
        detail="Endpoint POST /api/vlsm belum diimplementasikan",
    )
