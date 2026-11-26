"""Halaman Beranda: konteks masalah, tujuan penelitian, 6 langkah kerja, dan status dataset."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.state_manager import get_active_state, validate_dataset

state = get_active_state()
is_valid, status_msg = validate_dataset(state.df)

st.title("Analisis Total Transfer Data Jaringan Menggunakan Integral Tentu")
st.caption(
    "Mini Research Matematika Rekayasa | Kelompok 1 | Studi Kasus Luas di Bawah Kurva B(t)"
)

st.markdown("""
    Laju transfer data jaringan berubah sepanjang waktu mengikuti beban trafik, kapasitas tautan, dan kondisi kanal.
    Jika laju transfer dinyatakan sebagai fungsi kontinu $B(t)$, total volume data yang berpindah selama selang waktu
    $[a, b]$ sama dengan luas daerah di bawah kurva:
    """)
st.latex(r"V_{\text{total}} = \int_{a}^{b} B(t)\,dt")

st.divider()

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.subheader("Alur 6 Langkah Penelitian")
    steps_df = pd.DataFrame(
        [
            {
                "Langkah": "1",
                "Aktivitas Penelitian": "Menentukan periode pengamatan [a, b] serta satuan waktu dan laju transfer.",
                "Halaman Aplikasi": "1. Eksplorasi Data",
            },
            {
                "Langkah": "2",
                "Aktivitas Penelitian": "Menyusun atau memuat data laju transfer (simulasi, dataset publik, atau ukur langsung).",
                "Halaman Aplikasi": "1. Eksplorasi Data & 3. Live Capture",
            },
            {
                "Langkah": "3",
                "Aktivitas Penelitian": "Membuat grafik sebaran data dan membentuk fungsi kontinu B(t).",
                "Halaman Aplikasi": "2. Model & Integral",
            },
            {
                "Langkah": "4",
                "Aktivitas Penelitian": "Menghitung total transfer data secara analitis menggunakan integral tentu.",
                "Halaman Aplikasi": "2. Model & Integral",
            },
            {
                "Langkah": "5",
                "Aktivitas Penelitian": "Membandingkan integral analitis dengan Aturan Trapesium dan Simpson.",
                "Halaman Aplikasi": "4. Simulasi & Validasi",
            },
            {
                "Langkah": "6",
                "Aktivitas Penelitian": "Mengevaluasi asumsi, keterbatasan model, dan menyusun laporan.",
                "Halaman Aplikasi": "4. Simulasi & Validasi & 5. Ekspor Laporan",
            },
        ]
    )
    st.dataframe(steps_df, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("Ringkasan Dataset Aktif")
    if is_valid:
        st.success(status_msg)
        st.metric("Sumber Dataset", state.dataset_name)
        m1, m2 = st.columns(2)
        m1.metric(
            "Rentang Waktu",
            f"[{state.domain_a:g}, {state.domain_b:g}] {state.time_unit}",
        )
        m2.metric(
            "Rata-rata Laju", f"{state.df['bandwidth'].mean():.2f} {state.rate_unit}"
        )
        st.dataframe(state.df.head(6), use_container_width=True, hide_index=True)
    else:
        st.error(status_msg)
        st.info(
            "Buka halaman 1. Eksplorasi Data untuk memilih preset atau mengunggah berkas CSV/XLSX."
        )

st.divider()
st.subheader("Konvensi Satuan Perhitungan")
st.markdown("""
    Aplikasi ini menerapkan konvensi jaringan desimal agar konsisten dengan standar perangkat telekomunikasi:
    - $1\text{ Byte} = 8\text{ bit}$
    - $1\text{ MB} = 1000\text{ KB}$, dan $1\text{ GB} = 1000\text{ MB}$
    - Laju dalam `Mbps` yang diintegralkan terhadap `detik` menghasilkan `Megabit (Mb)`, lalu dibagi `8` untuk memperoleh `Megabyte (MB)`.
    """)
