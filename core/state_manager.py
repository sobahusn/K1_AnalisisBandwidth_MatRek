"""Manajemen session state, pemuatan dataset preset, dan validasi data tabular."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TIME_UNITS: dict[str, float] = {
    "detik": 1.0,
    "menit": 60.0,
    "jam": 3600.0,
}

# Faktor konversi dari (satuan_laju * detik) ke Megabyte desimal (1 MB = 8 Mb).
RATE_TO_MB_PER_SEC: Dict[str, float] = {
    "Mbps": 1.0 / 8.0,
    "MB/s": 1.0,
    "MB/menit": 1.0 / 60.0,
    "Kbps": 1.0 / 8000.0,
}

RATE_UNITS = tuple(RATE_TO_MB_PER_SEC.keys())

PRESET_DATASETS: dict[str, dict[str, str]] = {
    "Simulasi Panduan (7 titik)": {
        "filename": "simulasi_panduan.csv",
        "time_unit": "menit",
        "rate_unit": "MB/menit",
        "description": "Data simulasi panduan PPT selama 6 menit untuk verifikasi dasar luas di bawah kurva.",
    },
    "Dataset Publik ISP (13 titik)": {
        "filename": "dataset_publik_isp.csv",
        "time_unit": "jam",
        "rate_unit": "Mbps",
        "description": "Cuplikan pola trafik harian ISP selama 24 jam dengan puncak beban pada malam hari.",
    },
    "Pengukuran Lokal (11 titik)": {
        "filename": "pengukuran_lokal.csv",
        "time_unit": "detik",
        "rate_unit": "Mbps",
        "description": "Sampel laju unduhan lokal berdurasi 50 detik yang merekam fase naik dan stabil.",
    },
}


@dataclass(frozen=True)
class ActiveAppState:
    """Snapshot terstruktur dari konfigurasi analisis yang sedang aktif."""

    df: pd.DataFrame
    dataset_name: str
    time_unit: str
    rate_unit: str
    poly_degree: int
    domain_a: float
    domain_b: float


def load_preset_dataset(preset_key: str) -> tuple[pd.DataFrame, str, str]:
    """Memuat salah satu dataset preset CSV dari folder data/."""
    meta = PRESET_DATASETS[preset_key]
    csv_path = DATA_DIR / meta["filename"]
    df = pd.read_csv(csv_path)
    df = clean_bandwidth_dataframe(df)
    return df, meta["time_unit"], meta["rate_unit"]


def clean_bandwidth_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Menormalisasi nama kolom, memaksa tipe numerik, dan mengurutkan berdasarkan waktu."""
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=["waktu", "bandwidth"])

    df = raw_df.copy()
    if "waktu" not in df.columns or "bandwidth" not in df.columns:
        if df.shape[1] < 2:
            return pd.DataFrame(columns=["waktu", "bandwidth"])
        df = df.iloc[:, :2].copy()
        df.columns = ["waktu", "bandwidth"]
    else:
        df = df[["waktu", "bandwidth"]].copy()

    df["waktu"] = pd.to_numeric(df["waktu"], errors="coerce")
    df["bandwidth"] = pd.to_numeric(df["bandwidth"], errors="coerce")
    df = df.dropna(subset=["waktu", "bandwidth"])
    df = df.sort_values("waktu", kind="mergesort")

    # Gabungkan duplikat waktu dengan rata-rata agar fungsi B(t) tetap bernilai tunggal.
    df = df.groupby("waktu", as_index=False)["bandwidth"].mean()
    df["bandwidth"] = df["bandwidth"].clip(lower=0.0)
    return df.reset_index(drop=True)


def validate_dataset(df: pd.DataFrame) -> tuple[bool, str]:
    """Memeriksa kelayakan dataset untuk regresi polinomial dan integrasi numerik."""
    if df is None or df.empty:
        return (
            False,
            "Dataset kosong. Muat preset CSV atau unggah berkas di halaman Eksplorasi Data.",
        )
    if "waktu" not in df.columns or "bandwidth" not in df.columns:
        return False, "Kolom wajib 'waktu' dan 'bandwidth' tidak ditemukan."
    if len(df) < 3:
        return (
            False,
            f"Minimal dibutuhkan 3 titik waktu unik untuk kurva dan integrasi Simpson (saat ini {len(df)} titik).",
        )
    if df["waktu"].isna().any() or df["bandwidth"].isna().any():
        return (
            False,
            "Dataset masih memuat nilai kosong (NaN). Perbaiki atau hapus baris yang tidak lengkap.",
        )
    if not np.all(np.isfinite(df["waktu"].to_numpy(dtype=float))) or not np.all(
        np.isfinite(df["bandwidth"].to_numpy(dtype=float))
    ):
        return (
            False,
            "Dataset memuat nilai tak hingga (inf). Pastikan seluruh angka valid.",
        )
    if df["waktu"].nunique() < 3:
        return False, "Nilai waktu harus memiliki minimal 3 titik berbeda."
    if (df["bandwidth"] < 0).any():
        return False, "Laju bandwidth tidak boleh bernilai negatif."
    return True, "Dataset siap dianalisis."


def init_session_state() -> None:
    """Menginisialisasi seluruh kunci st.session_state bila belum tersedia."""
    if "active_df" not in st.session_state:
        default_key = "Simulasi Panduan (7 titik)"
        df, time_unit, rate_unit = load_preset_dataset(default_key)
        st.session_state["active_df"] = df
        st.session_state["dataset_name"] = default_key
        st.session_state["time_unit"] = time_unit
        st.session_state["rate_unit"] = rate_unit
        st.session_state["poly_degree"] = min(3, max(1, len(df) - 1))
        st.session_state["domain_a"] = float(df["waktu"].min())
        st.session_state["domain_b"] = float(df["waktu"].max())

    if "last_capture_df" not in st.session_state:
        st.session_state["last_capture_df"] = pd.DataFrame(
            columns=["waktu", "bandwidth"]
        )

    if "capture_direction" not in st.session_state:
        st.session_state["capture_direction"] = "Total (Download + Upload)"


def set_active_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    time_unit: str | None = None,
    rate_unit: str | None = None,
) -> pd.DataFrame:
    """Memperbarui dataset aktif beserta batas domain [a, b] dan derajat polinomial yang aman."""
    cleaned = clean_bandwidth_dataframe(df)
    st.session_state["active_df"] = cleaned
    st.session_state["dataset_name"] = dataset_name

    if time_unit in TIME_UNITS:
        st.session_state["time_unit"] = time_unit
    if rate_unit in RATE_TO_MB_PER_SEC:
        st.session_state["rate_unit"] = rate_unit

    if not cleaned.empty:
        t_min = float(cleaned["waktu"].min())
        t_max = float(cleaned["waktu"].max())
        st.session_state["domain_a"] = t_min
        st.session_state["domain_b"] = t_max
        max_safe_deg = max(1, min(6, len(cleaned) - 1))
        current_deg = int(st.session_state.get("poly_degree", 3))
        st.session_state["poly_degree"] = min(current_deg, max_safe_deg)
    return cleaned


def get_active_state() -> ActiveAppState:
    """Mengembalikan state aktif dengan proteksi batas nilai agar halaman tidak crash."""
    init_session_state()
    df: pd.DataFrame = st.session_state["active_df"]
    if df.empty:
        return ActiveAppState(
            df=df,
            dataset_name=str(st.session_state.get("dataset_name", "Tidak ada")),
            time_unit=str(st.session_state.get("time_unit", "detik")),
            rate_unit=str(st.session_state.get("rate_unit", "Mbps")),
            poly_degree=1,
            domain_a=0.0,
            domain_b=1.0,
        )

    t_min = float(df["waktu"].min())
    t_max = float(df["waktu"].max())
    domain_a = float(st.session_state.get("domain_a", t_min))
    domain_b = float(st.session_state.get("domain_b", t_max))
    if domain_a < t_min or domain_a >= t_max:
        domain_a = t_min
    if domain_b <= domain_a or domain_b > t_max:
        domain_b = t_max

    max_deg = max(1, min(6, len(df) - 1))
    poly_degree = int(np.clip(int(st.session_state.get("poly_degree", 2)), 1, max_deg))

    return ActiveAppState(
        df=df,
        dataset_name=str(st.session_state["dataset_name"]),
        time_unit=str(st.session_state["time_unit"]),
        rate_unit=str(st.session_state["rate_unit"]),
        poly_degree=poly_degree,
        domain_a=domain_a,
        domain_b=domain_b,
    )
