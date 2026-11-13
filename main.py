"""Kalkulator Subnet & VLSM IPv4.

Kerangka awal modul sebelum implementasi (TDD - Test Driven Development).
"""

from fastapi import FastAPI

app = FastAPI(title="Kalkulator Subnet IPv4")


def hitung_subnet(ip: str, prefix: int) -> dict:
    """Menghitung parameter subnetting IPv4.

    Args:
        ip (str): Alamat IPv4 dotted-decimal.
        prefix (int): Prefix subnet mask (0 - 32).

    Returns:
        dict: Hasil perhitungan subnet.

    Raises:
        NotImplementedError: Belum diimplementasikan.
    """
    raise NotImplementedError("Fungsi hitung_subnet belum diimplementasikan")
