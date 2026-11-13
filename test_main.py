"""Unit & Integration Tests untuk Kalkulator Subnet & VLSM IPv4.

Ditulis lebih dulu sebelum implementasi kode (Test-Driven Development / TDD).
Mengacu pada tabel pengujian Bagian 5 SPEC.md.
"""

import pytest
from fastapi.testclient import TestClient

from main import app, hitung_subnet, alokasi_vlsm

client = TestClient(app)


# ==============================================================================
# DATA TEST CASE SUBNET DARI SPEC.MD (TC-01 s.d. TC-08: Subnet Valid & Edge Cases)
# ==============================================================================

VALID_SUBNET_CASES = [
    # TC-01: Subnet Standar /25
    (
        "192.168.1.0",
        25,
        {
            "network": "192.168.1.0",
            "mask": "255.255.255.128",
            "broadcast": "192.168.1.127",
            "first_host": "192.168.1.1",
            "last_host": "192.168.1.126",
            "usable_hosts": 126,
        },
    ),
    # TC-02: Subnet Standar /26
    (
        "192.168.1.64",
        26,
        {
            "network": "192.168.1.64",
            "mask": "255.255.255.192",
            "broadcast": "192.168.1.127",
            "first_host": "192.168.1.65",
            "last_host": "192.168.1.126",
            "usable_hosts": 62,
        },
    ),
    # TC-03: Subnet Standar /20
    (
        "172.16.16.0",
        20,
        {
            "network": "172.16.16.0",
            "mask": "255.255.240.0",
            "broadcast": "172.16.31.255",
            "first_host": "172.16.16.1",
            "last_host": "172.16.31.254",
            "usable_hosts": 4094,
        },
    ),
    # TC-04: Subnet Standar /30
    (
        "10.0.0.4",
        30,
        {
            "network": "10.0.0.4",
            "mask": "255.255.255.252",
            "broadcast": "10.0.0.7",
            "first_host": "10.0.0.5",
            "last_host": "10.0.0.6",
            "usable_hosts": 2,
        },
    ),
    # TC-05: Edge Case /31 (RFC 3021)
    (
        "10.0.0.0",
        31,
        {
            "network": "10.0.0.0",
            "mask": "255.255.255.254",
            "broadcast": None,
            "first_host": "10.0.0.0",
            "last_host": "10.0.0.1",
            "usable_hosts": 2,
        },
    ),
    # TC-06: Edge Case /32 (Single Host)
    (
        "192.168.1.1",
        32,
        {
            "network": "192.168.1.1",
            "mask": "255.255.255.255",
            "broadcast": None,
            "first_host": "192.168.1.1",
            "last_host": "192.168.1.1",
            "usable_hosts": 1,
        },
    ),
    # TC-07: Edge Case /0 (Default Route)
    (
        "0.0.0.0",
        0,
        {
            "network": "0.0.0.0",
            "mask": "0.0.0.0",
            "broadcast": "255.255.255.255",
            "first_host": "0.0.0.1",
            "last_host": "255.255.255.254",
            "usable_hosts": 4294967294,
        },
    ),
    # TC-08: Edge Case /24 dengan Broadcast Address Input
    (
        "255.255.255.255",
        24,
        {
            "network": "255.255.255.0",
            "mask": "255.255.255.0",
            "broadcast": "255.255.255.255",
            "first_host": "255.255.255.1",
            "last_host": "255.255.255.254",
            "usable_hosts": 254,
        },
    ),
]


# ==============================================================================
# DATA TEST CASE SUBNET DARI SPEC.MD (TC-09 s.d. TC-15: Input Tidak Valid)
# ==============================================================================

INVALID_SUBNET_CASES = [
    # TC-09: Oktet > 255
    ("256.1.1.1", 24),
    # TC-10: Leading zero
    ("192.168.01.1", 24),
    ("010.0.0.1", 24),
    ("192.168.1.001", 24),
    # TC-11: Kurang dari 4 oktet
    ("192.168.1", 24),
    ("10.0", 16),
    ("172", 8),
    # TC-12: Karakter non-numerik
    ("abc", 24),
    ("192.168.a.1", 24),
    ("192.168.1.1xyz", 24),
    # TC-13: String kosong
    ("", 24),
    # TC-14: Karakter spasi (tidak boleh di-trim)
    (" 192.168.1.1", 24),
    ("192.168.1.1 ", 24),
    ("192.168. 1.1", 24),
    (" 192.168. 1.1 ", 24),
    # TC-15: Prefix di luar batas 0-32
    ("192.168.1.1", 33),
    ("192.168.1.1", -1),
    ("192.168.1.1", 100),
    # Kasus tambahan format tidak valid
    ("192.168.1.1.1", 24),  # Lebih dari 4 oktet
    ("-1.0.0.1", 24),        # Oktet negatif
    ("...", 24),             # Hanya titik
]


# ==============================================================================
# DATA TEST CASE VLSM DARI SPEC.MD (TC-16 s.d. TC-21)
# ==============================================================================

TC16_EXPECTED = [
    {
        "kebutuhan": 100,
        "network_cidr": "192.168.1.0/25",
        "mask": "255.255.255.128",
        "network": "192.168.1.0",
        "broadcast": "192.168.1.127",
        "first_host": "192.168.1.1",
        "last_host": "192.168.1.126",
        "usable_hosts": 126,
    },
    {
        "kebutuhan": 50,
        "network_cidr": "192.168.1.128/26",
        "mask": "255.255.255.192",
        "network": "192.168.1.128",
        "broadcast": "192.168.1.191",
        "first_host": "192.168.1.129",
        "last_host": "192.168.1.190",
        "usable_hosts": 62,
    },
    {
        "kebutuhan": 20,
        "network_cidr": "192.168.1.192/27",
        "mask": "255.255.255.224",
        "network": "192.168.1.192",
        "broadcast": "192.168.1.223",
        "first_host": "192.168.1.193",
        "last_host": "192.168.1.222",
        "usable_hosts": 30,
    },
    {
        "kebutuhan": 2,
        "network_cidr": "192.168.1.224/30",
        "mask": "255.255.255.252",
        "network": "192.168.1.224",
        "broadcast": "192.168.1.227",
        "first_host": "192.168.1.225",
        "last_host": "192.168.1.226",
        "usable_hosts": 2,
    },
]

VALID_VLSM_CASES = [
    # TC-16: VLSM Normal
    ("192.168.1.0/24", [100, 50, 20, 2], TC16_EXPECTED),
    # TC-17: VLSM Urutan Acak
    ("192.168.1.0/24", [2, 100, 20, 50], TC16_EXPECTED),
    # TC-18: VLSM Batas Kapasitas [62] vs [63]
    (
        "192.168.1.0/24",
        [62],
        [
            {
                "kebutuhan": 62,
                "network_cidr": "192.168.1.0/26",
                "mask": "255.255.255.192",
                "network": "192.168.1.0",
                "broadcast": "192.168.1.63",
                "first_host": "192.168.1.1",
                "last_host": "192.168.1.62",
                "usable_hosts": 62,
            }
        ],
    ),
    (
        "192.168.1.0/24",
        [63],
        [
            {
                "kebutuhan": 63,
                "network_cidr": "192.168.1.0/25",
                "mask": "255.255.255.128",
                "network": "192.168.1.0",
                "broadcast": "192.168.1.127",
                "first_host": "192.168.1.1",
                "last_host": "192.168.1.126",
                "usable_hosts": 126,
            }
        ],
    ),
    # TC-19: VLSM Batas Bawah [1] -> blok minimal /30
    (
        "192.168.1.0/24",
        [1],
        [
            {
                "kebutuhan": 1,
                "network_cidr": "192.168.1.0/30",
                "mask": "255.255.255.252",
                "network": "192.168.1.0",
                "broadcast": "192.168.1.3",
                "first_host": "192.168.1.1",
                "last_host": "192.168.1.2",
                "usable_hosts": 2,
            }
        ],
    ),
]

INVALID_VLSM_CASES = [
    # TC-20: VLSM Overflow kapasitas network induk
    ("192.168.1.0/24", [200, 100]),
    ("192.168.1.0/24", [130, 130]),
    # TC-21: Alamat Host bukan Network Address
    ("192.168.1.5/24", [50]),
    ("192.168.1.129/25", [50]),
    # TC-21: Kebutuhan <= 0 atau format tidak valid
    ("192.168.1.0/24", [50, 0]),
    ("192.168.1.0/24", [-5]),
    ("192.168.1.0/24", []),
    ("192.168.1.0/24", [10, -1]),
    ("192.168.1.0/24", [10, 0, 5]),
]


# ==============================================================================
# 1. PENGUJIAN FUNGSI MURNI hitung_subnet
# ==============================================================================

@pytest.mark.parametrize("ip, prefix, expected", VALID_SUBNET_CASES)
def test_hitung_subnet_valid(ip: str, prefix: int, expected: dict):
    """Memverifikasi kalkulasi subnet valid (TC-01 sampai TC-08)."""
    result = hitung_subnet(ip, prefix)
    assert result == expected


@pytest.mark.parametrize("ip, prefix", INVALID_SUBNET_CASES)
def test_hitung_subnet_invalid(ip: str, prefix: int):
    """Memverifikasi penolakan input tidak valid dengan ValueError (TC-09 sampai TC-15)."""
    with pytest.raises(ValueError):
        hitung_subnet(ip, prefix)


# ==============================================================================
# 2. PENGUJIAN ENDPOINT API: GET /
# ==============================================================================

def test_api_get_root():
    """Memverifikasi endpoint GET / menyajikan antarmuka index.html dengan HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


# ==============================================================================
# 3. PENGUJIAN ENDPOINT API: GET /api/subnet (SUKSES)
# ==============================================================================

@pytest.mark.parametrize("ip, prefix, expected", VALID_SUBNET_CASES)
def test_api_subnet_success(ip: str, prefix: int, expected: dict):
    """Memverifikasi endpoint GET /api/subnet mengembalikan HTTP 200 dan data sesuai untuk input valid."""
    response = client.get(f"/api/subnet?ip={ip}&prefix={prefix}")
    assert response.status_code == 200
    assert response.json() == expected


# ==============================================================================
# 4. PENGUJIAN ENDPOINT API: GET /api/subnet (GAGAL / 400 BAD REQUEST)
# ==============================================================================

@pytest.mark.parametrize("ip, prefix", INVALID_SUBNET_CASES)
def test_api_subnet_bad_request(ip: str, prefix: int):
    """Memverifikasi endpoint GET /api/subnet mengembalikan HTTP 400 dengan 'detail' untuk input tidak valid."""
    response = client.get(f"/api/subnet?ip={ip}&prefix={prefix}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


@pytest.mark.parametrize(
    "params",
    [
        {},                      # Tanpa parameter sama sekali
        {"ip": "192.168.1.1"},   # Parameter prefix hilang
        {"prefix": "24"},        # Parameter ip hilang
        {"ip": "192.168.1.1", "prefix": "abc"},  # Prefix bukan angka
        {"ip": "192.168.1.1", "prefix": "24.5"}, # Prefix bilangan desimal/float
    ],
)
def test_api_subnet_missing_or_malformed_params(params: dict):
    """Memverifikasi endpoint GET /api/subnet mengembalikan HTTP 400 jika query param tidak lengkap atau salah format."""
    response = client.get("/api/subnet", params=params)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


# ==============================================================================
# 5. PENGUJIAN FUNGSI MURNI alokasi_vlsm
# ==============================================================================

@pytest.mark.parametrize("network, kebutuhan, expected", VALID_VLSM_CASES)
def test_alokasi_vlsm_valid(network: str, kebutuhan: list[int], expected: list[dict]):
    """Memverifikasi alokasi VLSM valid (TC-16 sampai TC-19)."""
    result = alokasi_vlsm(network, kebutuhan)
    assert result == expected


@pytest.mark.parametrize("network, kebutuhan", INVALID_VLSM_CASES)
def test_alokasi_vlsm_invalid(network: str, kebutuhan: list[int]):
    """Memverifikasi penolakan alokasi VLSM tidak valid / overflow dengan ValueError (TC-20, TC-21)."""
    with pytest.raises(ValueError):
        alokasi_vlsm(network, kebutuhan)


# ==============================================================================
# 6. PENGUJIAN ENDPOINT API: POST /api/vlsm (SUKSES)
# ==============================================================================

@pytest.mark.parametrize("network, kebutuhan, expected", VALID_VLSM_CASES)
def test_api_vlsm_success(network: str, kebutuhan: list[int], expected: list[dict]):
    """Memverifikasi endpoint POST /api/vlsm mengembalikan HTTP 200 dan data alokasi yang benar."""
    response = client.post(
        "/api/vlsm",
        json={"network": network, "kebutuhan_host": kebutuhan},
    )
    assert response.status_code == 200
    assert response.json() == expected


# ==============================================================================
# 7. PENGUJIAN ENDPOINT API: POST /api/vlsm (GAGAL / 400 BAD REQUEST)
# ==============================================================================

@pytest.mark.parametrize("network, kebutuhan", INVALID_VLSM_CASES)
def test_api_vlsm_bad_request(network: str, kebutuhan: list[int]):
    """Memverifikasi endpoint POST /api/vlsm mengembalikan HTTP 400 dengan 'detail' untuk input tidak valid."""
    response = client.post(
        "/api/vlsm",
        json={"network": network, "kebutuhan_host": kebutuhan},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


@pytest.mark.parametrize(
    "payload",
    [
        {},                                         # Body kosong
        {"network": "192.168.1.0/24"},              # Atribut kebutuhan_host hilang
        {"kebutuhan_host": [50, 20]},               # Atribut network hilang
        {"network": "192.168.1.0/24", "kebutuhan_host": "bukan-list"},  # Bukan list
        {"network": "192.168.1.0/24", "kebutuhan_host": [10, "abc"]},   # Elemen bukan int
        {"network": "192.168.1.0/24", "kebutuhan_host": [10, 5.5]},     # Elemen float
    ],
)
def test_api_vlsm_malformed_payload(payload: dict):
    """Memverifikasi endpoint POST /api/vlsm mengembalikan HTTP 400 jika payload rusak atau tidak lengkap."""
    response = client.post("/api/vlsm", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
