"""Test suite komprehensif untuk Kalkulator Subnet & VLSM IPv4.

Mencakup pengujian unit fungsi murni (hitung_subnet, alokasi_vlsm) dan
pengujian integrasi API HTTP (GET /, GET /api/subnet, POST /api/vlsm)
sesuai spesifikasi Bagian 4 & 5 SPEC.md (Tabel Test Case TC-01 s.d. TC-21).
"""

import pytest
from fastapi.testclient import TestClient
from main import app, hitung_subnet, alokasi_vlsm


# ==============================================================================
# FIXTURE TEST CLIENT FASTAPI
# ==============================================================================

@pytest.fixture(scope="module")
def client():
    """Menyediakan instans TestClient untuk pengujian integrasi endpoint HTTP."""
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# BAGIAN 1: PENGUJIAN FUNGSI MURNI hitung_subnet (TC-01 s.d. TC-15)
# ==============================================================================

class TestHitungSubnetUnit:
    """Pengujian langsung fungsi murni hitung_subnet()."""

    def test_tc01_subnet_standar_25(self):
        """TC-01: Subnet Standar /25."""
        res = hitung_subnet("192.168.1.0", 25)
        assert res["network"] == "192.168.1.0"
        assert res["mask"] == "255.255.255.128"
        assert res["broadcast"] == "192.168.1.127"
        assert res["first_host"] == "192.168.1.1"
        assert res["last_host"] == "192.168.1.126"
        assert res["usable_hosts"] == 126

    def test_tc02_subnet_standar_26(self):
        """TC-02: Subnet Standar /26."""
        res = hitung_subnet("192.168.1.64", 26)
        assert res["network"] == "192.168.1.64"
        assert res["mask"] == "255.255.255.192"
        assert res["broadcast"] == "192.168.1.127"
        assert res["first_host"] == "192.168.1.65"
        assert res["last_host"] == "192.168.1.126"
        assert res["usable_hosts"] == 62

    def test_tc03_subnet_standar_20(self):
        """TC-03: Subnet Standar /20."""
        res = hitung_subnet("172.16.16.0", 20)
        assert res["network"] == "172.16.16.0"
        assert res["mask"] == "255.255.240.0"
        assert res["broadcast"] == "172.16.31.255"
        assert res["first_host"] == "172.16.16.1"
        assert res["last_host"] == "172.16.31.254"
        assert res["usable_hosts"] == 4094

    def test_tc04_subnet_standar_30(self):
        """TC-04: Subnet Standar /30."""
        res = hitung_subnet("10.0.0.4", 30)
        assert res["network"] == "10.0.0.4"
        assert res["mask"] == "255.255.255.252"
        assert res["broadcast"] == "10.0.0.7"
        assert res["first_host"] == "10.0.0.5"
        assert res["last_host"] == "10.0.0.6"
        assert res["usable_hosts"] == 2

    def test_tc05_edge_case_31_rfc3021(self):
        """TC-05: Edge Case /31 (RFC 3021 - Point-to-Point)."""
        res = hitung_subnet("10.0.0.0", 31)
        assert res["network"] == "10.0.0.0"
        assert res["mask"] == "255.255.255.254"
        assert res["broadcast"] is None
        assert res["first_host"] == "10.0.0.0"
        assert res["last_host"] == "10.0.0.1"
        assert res["usable_hosts"] == 2

    def test_tc06_edge_case_32_single_host(self):
        """TC-06: Edge Case /32 (Single Host Route)."""
        res = hitung_subnet("192.168.1.1", 32)
        assert res["network"] == "192.168.1.1"
        assert res["mask"] == "255.255.255.255"
        assert res["broadcast"] is None
        assert res["first_host"] == "192.168.1.1"
        assert res["last_host"] == "192.168.1.1"
        assert res["usable_hosts"] == 1

    def test_tc07_edge_case_0_default_route(self):
        """TC-07: Edge Case /0 (Default Route Global)."""
        res = hitung_subnet("0.0.0.0", 0)
        assert res["network"] == "0.0.0.0"
        assert res["mask"] == "0.0.0.0"
        assert res["broadcast"] == "255.255.255.255"
        assert res["first_host"] == "0.0.0.1"
        assert res["last_host"] == "255.255.255.254"
        assert res["usable_hosts"] == 4294967294

    def test_tc08_edge_case_broadcast_ip_input(self):
        """TC-08: Edge Case input berupa alamat broadcast 255.255.255.255/24."""
        res = hitung_subnet("255.255.255.255", 24)
        assert res["network"] == "255.255.255.0"
        assert res["mask"] == "255.255.255.0"
        assert res["broadcast"] == "255.255.255.255"
        assert res["first_host"] == "255.255.255.1"
        assert res["last_host"] == "255.255.255.254"
        assert res["usable_hosts"] == 254

    def test_tc09_invalid_octet_overflow_256(self):
        """TC-09: Validasi Negatif - Oktet 256 melebihi 255."""
        with pytest.raises(ValueError, match="melebihi batas"):
            hitung_subnet("256.1.1.1", 24)

    def test_tc10_invalid_octet_leading_zero(self):
        """TC-10: Validasi Negatif - Leading zero pada oktet (01)."""
        with pytest.raises(ValueError, match="leading zero"):
            hitung_subnet("192.168.01.1", 24)

    def test_tc11_invalid_octet_count_less_than_4(self):
        """TC-11: Validasi Negatif - Kurang dari 4 oktet."""
        with pytest.raises(ValueError, match="tepat 4 oktet"):
            hitung_subnet("192.168.1", 24)

        with pytest.raises(ValueError, match="tepat 4 oktet"):
            hitung_subnet("192.168.1.1.1", 24)

    def test_tc12_invalid_non_numeric_ip(self):
        """TC-12: Validasi Negatif - Karakter alfabet non-numerik."""
        with pytest.raises(ValueError):
            hitung_subnet("abc", 24)

        with pytest.raises(ValueError, match="bukan angka yang valid"):
            hitung_subnet("192.168.abc.1", 24)

    def test_tc13_invalid_empty_ip(self):
        """TC-13: Validasi Negatif - IP string kosong."""
        with pytest.raises(ValueError, match="tidak boleh kosong"):
            hitung_subnet("", 24)

    def test_tc14_invalid_ip_with_spaces(self):
        """TC-14: Validasi Negatif - Mengandung spasi (tidak boleh di-trim)."""
        with pytest.raises(ValueError, match="spasi"):
            hitung_subnet(" 192.168.1.1", 24)

        with pytest.raises(ValueError, match="spasi"):
            hitung_subnet("192.168.1.1 ", 24)

        with pytest.raises(ValueError, match="spasi"):
            hitung_subnet("192.168. 1.1", 24)

    def test_tc15_invalid_prefix_out_of_range(self):
        """TC-15: Validasi Negatif - Prefix di luar 0 s.d. 32."""
        with pytest.raises(ValueError, match="rentang 0 sampai 32"):
            hitung_subnet("192.168.1.1", 33)

        with pytest.raises(ValueError, match="rentang 0 sampai 32"):
            hitung_subnet("192.168.1.1", -1)

    def test_invalid_prefix_boolean(self):
        """Uji penolakan boolean sebagai prefix (karena bool adalah subclass int di Python)."""
        with pytest.raises(ValueError, match="boolean"):
            hitung_subnet("192.168.1.1", True)

    def test_invalid_prefix_types_and_empty(self):
        """Uji penolakan prefix dengan tipe non-int (float, string) dan IP non-string."""
        with pytest.raises(ValueError, match="string"):
            hitung_subnet(12345, 24)

        with pytest.raises(ValueError, match="integer"):
            hitung_subnet("192.168.1.1", 24.5)

        with pytest.raises(ValueError, match="integer"):
            hitung_subnet("192.168.1.1", "24")


# ==============================================================================
# BAGIAN 2: PENGUJIAN FUNGSI MURNI alokasi_vlsm (TC-16 s.d. TC-21)
# ==============================================================================

class TestAlokasiVlsmUnit:
    """Pengujian langsung fungsi murni alokasi_vlsm()."""

    def test_tc16_vlsm_normal_allocation(self):
        """TC-16: Skenario VLSM Normal (192.168.1.0/24 dengan [100, 50, 20, 2])."""
        res = alokasi_vlsm("192.168.1.0/24", [100, 50, 20, 2])
        assert len(res) == 4

        # Blok 1: 100 host -> /25 (128 IP)
        assert res[0]["kebutuhan"] == 100
        assert res[0]["network_cidr"] == "192.168.1.0/25"
        assert res[0]["network"] == "192.168.1.0"
        assert res[0]["mask"] == "255.255.255.128"
        assert res[0]["broadcast"] == "192.168.1.127"
        assert res[0]["first_host"] == "192.168.1.1"
        assert res[0]["last_host"] == "192.168.1.126"
        assert res[0]["usable_hosts"] == 126

        # Blok 2: 50 host -> /26 (64 IP)
        assert res[1]["kebutuhan"] == 50
        assert res[1]["network_cidr"] == "192.168.1.128/26"
        assert res[1]["network"] == "192.168.1.128"
        assert res[1]["mask"] == "255.255.255.192"
        assert res[1]["broadcast"] == "192.168.1.191"
        assert res[1]["first_host"] == "192.168.1.129"
        assert res[1]["last_host"] == "192.168.1.190"
        assert res[1]["usable_hosts"] == 62

        # Blok 3: 20 host -> /27 (32 IP)
        assert res[2]["kebutuhan"] == 20
        assert res[2]["network_cidr"] == "192.168.1.192/27"
        assert res[2]["network"] == "192.168.1.192"
        assert res[2]["mask"] == "255.255.255.224"
        assert res[2]["broadcast"] == "192.168.1.223"
        assert res[2]["first_host"] == "192.168.1.193"
        assert res[2]["last_host"] == "192.168.1.222"
        assert res[2]["usable_hosts"] == 30

        # Blok 4: 2 host -> /30 (4 IP)
        assert res[3]["kebutuhan"] == 2
        assert res[3]["network_cidr"] == "192.168.1.224/30"
        assert res[3]["network"] == "192.168.1.224"
        assert res[3]["mask"] == "255.255.255.252"
        assert res[3]["broadcast"] == "192.168.1.227"
        assert res[3]["first_host"] == "192.168.1.225"
        assert res[3]["last_host"] == "192.168.1.226"
        assert res[3]["usable_hosts"] == 2

    def test_tc17_vlsm_random_order(self):
        """TC-17: Skenario VLSM Urutan Acak ([2, 100, 20, 50]).

        Harus otomatis diurutkan descending menjadi [100, 50, 20, 2]
        sehingga hasil alokasi identik dengan TC-16.
        """
        res = alokasi_vlsm("192.168.1.0/24", [2, 100, 20, 50])
        assert [r["kebutuhan"] for r in res] == [100, 50, 20, 2]
        assert [r["network_cidr"] for r in res] == [
            "192.168.1.0/25",
            "192.168.1.128/26",
            "192.168.1.192/27",
            "192.168.1.224/30",
        ]

    def test_tc18_vlsm_boundary_62_vs_63(self):
        """TC-18: Skenario VLSM Batas Kapasitas (62 vs 63).

        - Kebutuhan 62: (62 + 2 = 64) -> dialokasikan blok /26 (64 IP).
        - Kebutuhan 63: (63 + 2 = 65) -> dialokasikan blok /25 (128 IP).
        """
        res_62 = alokasi_vlsm("192.168.1.0/24", [62])
        assert res_62[0]["network_cidr"] == "192.168.1.0/26"
        assert res_62[0]["usable_hosts"] == 62

        res_63 = alokasi_vlsm("192.168.1.0/24", [63])
        assert res_63[0]["network_cidr"] == "192.168.1.0/25"
        assert res_63[0]["usable_hosts"] == 126

    def test_tc19_vlsm_minimum_1_host(self):
        """TC-19: Skenario VLSM Batas Minimal 1 Host.

        Kebutuhan 1 host (1 + 2 = 3) dialokasikan blok minimal /30 (4 IP, 2 usable).
        """
        res = alokasi_vlsm("192.168.1.0/24", [1])
        assert len(res) == 1
        assert res[0]["network_cidr"] == "192.168.1.0/30"
        assert res[0]["usable_hosts"] == 2

    def test_tc20_vlsm_capacity_overflow(self):
        """TC-20: Skenario VLSM Overflow Kapasitas.

        192.168.1.0/24 (256 IP) diberi kebutuhan [200, 100].
        200 butuh /24 (256 IP) + 100 butuh /25 (128 IP) = 384 IP -> Overflow!
        """
        with pytest.raises(ValueError, match="tidak mencukupi"):
            alokasi_vlsm("192.168.1.0/24", [200, 100])

    def test_tc21_vlsm_invalid_inputs(self):
        """TC-21: Skenario VLSM Input Tidak Valid.

        1. Non-network CIDR (192.168.1.5/24).
        2. Kebutuhan host <= 0 atau list kosong.
        """
        # Bukan network address
        with pytest.raises(ValueError, match="bukan network address"):
            alokasi_vlsm("192.168.1.5/24", [50])

        # Kebutuhan bernilai 0
        with pytest.raises(ValueError, match="minimal 1 host"):
            alokasi_vlsm("192.168.1.0/24", [50, 0])

        # Kebutuhan bernilai negatif
        with pytest.raises(ValueError, match="minimal 1 host"):
            alokasi_vlsm("192.168.1.0/24", [-5])

        # List kebutuhan kosong
        with pytest.raises(ValueError, match="tidak boleh kosong"):
            alokasi_vlsm("192.168.1.0/24", [])

        # Elemen bertipe boolean
        with pytest.raises(ValueError, match="boolean"):
            alokasi_vlsm("192.168.1.0/24", [True, 50])

        # Elemen bertipe float
        with pytest.raises(ValueError, match="bilangan bulat"):
            alokasi_vlsm("192.168.1.0/24", [10.5])

        # kebutuhan_host bukan list
        with pytest.raises(ValueError, match="berupa list"):
            alokasi_vlsm("192.168.1.0/24", "bukan list")

        # Format network_cidr tidak valid
        with pytest.raises(ValueError, match="berupa string"):
            alokasi_vlsm(12345, [10])

        with pytest.raises(ValueError, match="tidak boleh kosong"):
            alokasi_vlsm("", [10])

        with pytest.raises(ValueError, match="spasi"):
            alokasi_vlsm(" 192.168.1.0/24", [10])

        with pytest.raises(ValueError, match="berupa <ip>/<prefix>"):
            alokasi_vlsm("192.168.1.0", [10])

        with pytest.raises(ValueError, match="satu karakter '/'"):
            alokasi_vlsm("192.168.1.0/24/24", [10])

        with pytest.raises(ValueError, match="tidak boleh kosong"):
            alokasi_vlsm("192.168.1.0/", [10])

        with pytest.raises(ValueError, match="bilangan bulat positif"):
            alokasi_vlsm("192.168.1.0/abc", [10])

        with pytest.raises(ValueError, match="leading zero"):
            alokasi_vlsm("192.168.1.0/024", [10])


# ==============================================================================
# BAGIAN 3: PENGUJIAN INTEGRASI ENDPOINT HTTP FastAPI DENGAN TestClient
# ==============================================================================

class TestApiEndpoints:
    """Pengujian integrasi endpoint HTTP API."""

    def test_api_get_root(self, client):
        """Memastikan endpoint GET / menyajikan halaman web index.html."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "NetCalc" in resp.text or "Subnet" in resp.text

    # --- Endpoint GET /api/subnet (Kasus Valid) ---

    def test_api_subnet_tc01_success(self, client):
        """Endpoint GET /api/subnet untuk TC-01 (/25)."""
        resp = client.get("/api/subnet", params={"ip": "192.168.1.0", "prefix": "25"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["network"] == "192.168.1.0"
        assert data["mask"] == "255.255.255.128"
        assert data["broadcast"] == "192.168.1.127"
        assert data["first_host"] == "192.168.1.1"
        assert data["last_host"] == "192.168.1.126"
        assert data["usable_hosts"] == 126

    def test_api_subnet_tc05_edge_31(self, client):
        """Endpoint GET /api/subnet untuk TC-05 (RFC 3021 /31)."""
        resp = client.get("/api/subnet", params={"ip": "10.0.0.0", "prefix": "31"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["broadcast"] is None
        assert data["usable_hosts"] == 2

    def test_api_subnet_tc06_edge_32(self, client):
        """Endpoint GET /api/subnet untuk TC-06 (/32)."""
        resp = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": "32"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["broadcast"] is None
        assert data["usable_hosts"] == 1

    def test_api_subnet_tc07_edge_0(self, client):
        """Endpoint GET /api/subnet untuk TC-07 (/0)."""
        resp = client.get("/api/subnet", params={"ip": "0.0.0.0", "prefix": "0"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["network"] == "0.0.0.0"
        assert data["broadcast"] == "255.255.255.255"
        assert data["usable_hosts"] == 4294967294

    def test_api_subnet_tc08_broadcast_input(self, client):
        """Endpoint GET /api/subnet untuk TC-08 (255.255.255.255/24)."""
        resp = client.get("/api/subnet", params={"ip": "255.255.255.255", "prefix": "24"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["network"] == "255.255.255.0"
        assert data["usable_hosts"] == 254

    # --- Endpoint GET /api/subnet (Kasus Negatif -> HTTP 400 + 'detail') ---

    def test_api_subnet_tc09_overflow_octet(self, client):
        """TC-09: HTTP 400 saat oktet > 255."""
        resp = client.get("/api/subnet", params={"ip": "256.1.1.1", "prefix": "24"})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_subnet_tc10_leading_zero(self, client):
        """TC-10: HTTP 400 saat terdapat leading zero."""
        resp = client.get("/api/subnet", params={"ip": "192.168.01.1", "prefix": "24"})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_subnet_tc11_incomplete_octets(self, client):
        """TC-11: HTTP 400 saat kurang atau lebih dari 4 oktet."""
        resp = client.get("/api/subnet", params={"ip": "192.168.1", "prefix": "24"})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_subnet_tc12_non_numeric_ip(self, client):
        """TC-12: HTTP 400 saat IP berupa alfabet."""
        resp = client.get("/api/subnet", params={"ip": "abc", "prefix": "24"})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_subnet_tc13_empty_ip(self, client):
        """TC-13: HTTP 400 saat IP kosong."""
        resp = client.get("/api/subnet", params={"ip": "", "prefix": "24"})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_subnet_tc14_spaces_in_ip(self, client):
        """TC-14: HTTP 400 saat IP mengandung spasi."""
        resp1 = client.get("/api/subnet", params={"ip": " 192.168.1.1", "prefix": "24"})
        assert resp1.status_code == 400
        assert "detail" in resp1.json()

        resp2 = client.get("/api/subnet", params={"ip": "192.168. 1.1", "prefix": "24"})
        assert resp2.status_code == 400
        assert "detail" in resp2.json()

    def test_api_subnet_tc15_prefix_invalid_range(self, client):
        """TC-15: HTTP 400 saat prefix < 0 atau > 32."""
        resp_over = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": "33"})
        assert resp_over.status_code == 400
        assert "detail" in resp_over.json()

        resp_neg = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": "-1"})
        assert resp_neg.status_code == 400
        assert "detail" in resp_neg.json()

    def test_api_subnet_missing_parameters(self, client):
        """HTTP 400 saat query parameter ip atau prefix tidak disertakan."""
        resp1 = client.get("/api/subnet", params={"prefix": "24"})
        assert resp1.status_code == 400
        assert "detail" in resp1.json()

        resp2 = client.get("/api/subnet", params={"ip": "192.168.1.1"})
        assert resp2.status_code == 400
        assert "detail" in resp2.json()

    def test_api_subnet_invalid_prefix_format(self, client):
        """HTTP 400 saat prefix berupa non-angka atau mengandung spasi/leading zero."""
        resp_alpha = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": "xyz"})
        assert resp_alpha.status_code == 400
        assert "detail" in resp_alpha.json()

        resp_space = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": " 24"})
        assert resp_space.status_code == 400
        assert "detail" in resp_space.json()

        resp_lead_zero = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": "024"})
        assert resp_lead_zero.status_code == 400
        assert "detail" in resp_lead_zero.json()

    # --- Endpoint POST /api/vlsm (Kasus Valid) ---

    def test_api_vlsm_tc16_success(self, client):
        """Endpoint POST /api/vlsm untuk TC-16."""
        payload = {
            "network": "192.168.1.0/24",
            "kebutuhan_host": [100, 50, 20, 2]
        }
        resp = client.post("/api/vlsm", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 4
        assert data[0]["network_cidr"] == "192.168.1.0/25"
        assert data[1]["network_cidr"] == "192.168.1.128/26"
        assert data[2]["network_cidr"] == "192.168.1.192/27"
        assert data[3]["network_cidr"] == "192.168.1.224/30"

    def test_api_vlsm_tc17_unordered(self, client):
        """Endpoint POST /api/vlsm untuk TC-17 (urutan acak)."""
        payload = {
            "network": "192.168.1.0/24",
            "kebutuhan_host": [2, 100, 20, 50]
        }
        resp = client.post("/api/vlsm", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert [r["kebutuhan"] for r in data] == [100, 50, 20, 2]

    def test_api_vlsm_tc18_boundary(self, client):
        """Endpoint POST /api/vlsm untuk TC-18 (batas 62 vs 63)."""
        resp62 = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [62]})
        assert resp62.status_code == 200
        assert resp62.json()[0]["network_cidr"] == "192.168.1.0/26"

        resp63 = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [63]})
        assert resp63.status_code == 200
        assert resp63.json()[0]["network_cidr"] == "192.168.1.0/25"

    def test_api_vlsm_tc19_minimum_host(self, client):
        """Endpoint POST /api/vlsm untuk TC-19 (1 host)."""
        resp = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [1]})
        assert resp.status_code == 200
        assert resp.json()[0]["network_cidr"] == "192.168.1.0/30"

    # --- Endpoint POST /api/vlsm (Kasus Negatif -> HTTP 400 + 'detail') ---

    def test_api_vlsm_tc20_overflow(self, client):
        """TC-20: HTTP 400 saat kapasitas network tidak mencukupi."""
        payload = {
            "network": "192.168.1.0/24",
            "kebutuhan_host": [200, 100]
        }
        resp = client.post("/api/vlsm", json=payload)
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_vlsm_tc21_non_network_cidr(self, client):
        """TC-21: HTTP 400 saat input berupa host address bukan network address."""
        payload = {
            "network": "192.168.1.5/24",
            "kebutuhan_host": [50]
        }
        resp = client.post("/api/vlsm", json=payload)
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_api_vlsm_tc21_invalid_kebutuhan(self, client):
        """TC-21: HTTP 400 saat kebutuhan <= 0 atau list kosong."""
        resp_zero = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [50, 0]})
        assert resp_zero.status_code == 400
        assert "detail" in resp_zero.json()

        resp_neg = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [-5]})
        assert resp_neg.status_code == 400
        assert "detail" in resp_neg.json()

        resp_empty = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": []})
        assert resp_empty.status_code == 400
        assert "detail" in resp_empty.json()

    def test_api_vlsm_missing_fields(self, client):
        """HTTP 400 saat field network atau kebutuhan_host tidak ada."""
        resp1 = client.post("/api/vlsm", json={"kebutuhan_host": [10]})
        assert resp1.status_code == 400
        assert "detail" in resp1.json()

        resp2 = client.post("/api/vlsm", json={"network": "192.168.1.0/24"})
        assert resp2.status_code == 400
        assert "detail" in resp2.json()

    def test_api_vlsm_invalid_json(self, client):
        """HTTP 400 saat request body bukan JSON object yang valid."""
        resp = client.post("/api/vlsm", content="bukan json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 400
        assert "detail" in resp.json()

        # Payload bukan dict (misal array)
        resp_list = client.post("/api/vlsm", json=["bukan", "dict"])
        assert resp_list.status_code == 400
        assert "detail" in resp_list.json()

    def test_api_subnet_empty_prefix(self, client):
        """HTTP 400 saat prefix kosong."""
        resp = client.get("/api/subnet", params={"ip": "192.168.1.1", "prefix": ""})
        assert resp.status_code == 400
        assert "detail" in resp.json()
