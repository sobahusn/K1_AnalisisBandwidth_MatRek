"""Perekaman laju bandwidth antarmuka jaringan lokal secara real-time via psutil."""

from __future__ import annotations

import time

import pandas as pd
import plotly.graph_objects as go
import psutil
import streamlit as st

from core.plotting import COLOR_PRIMARY, _apply_base_layout
from core.state_manager import set_active_dataset

st.title("3. Live Capture Jaringan Lokal")
st.caption("Pengukuran laju transfer aktual perangkat melalui psutil.")

st.markdown("""
    Fitur ini membaca penghitung byte antarmuka jaringan lokal (`psutil.net_io_counters`) pada interval tetap.
    Jalankan aktivitas jaringan ringan seperti mengunduh berkas atau memutar video saat perekaman berlangsung
    agar kurva menampilkan variasi beban yang jelas.
    """)

c1, c2, c3 = st.columns(3)
duration_sec = c1.number_input(
    "Durasi Rekam (detik)", min_value=5, max_value=120, value=15, step=5
)
interval_sec = c2.selectbox(
    "Interval Sampling (detik)", options=[0.5, 1.0, 2.0], index=1
)
direction = c3.selectbox(
    "Arah Trafik",
    options=["Total (Download + Upload)", "Download (Recv)", "Upload (Sent)"],
    index=0,
)


def _read_bytes(mode: str) -> int:
    counters = psutil.net_io_counters()
    if counters is None:
        raise RuntimeError("Antarmuka jaringan tidak terdeteksi oleh psutil.")
    if mode == "Download (Recv)":
        return int(counters.bytes_recv)
    if mode == "Upload (Sent)":
        return int(counters.bytes_sent)
    return int(counters.bytes_recv + counters.bytes_sent)


def _build_live_fig(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Scatter(
                x=df["waktu"],
                y=df["bandwidth"],
                mode="lines+markers",
                line={"color": COLOR_PRIMARY, "width": 2.2},
                marker={"size": 6},
                name="Laju Terukur",
            )
        ]
    )
    return _apply_base_layout(
        fig,
        title="Laju Bandwidth Jaringan Lokal Real-Time",
        x_title="Waktu t (detik)",
        y_title="Laju Bandwidth (Mbps)",
    )


if st.button("Mulai Perekaman", type="primary"):
    try:
        total_steps = max(3, int(duration_sec / interval_sec))
        progress_bar = st.progress(0, text="Memulai perekaman jaringan...")
        chart_placeholder = st.empty()
        metric_placeholder = st.empty()

        records: list[dict[str, float]] = []
        start_time = time.perf_counter()
        prev_time = start_time
        prev_bytes = _read_bytes(direction)

        for step in range(1, total_steps + 1):
            time.sleep(float(interval_sec))
            now_time = time.perf_counter()
            now_bytes = _read_bytes(direction)

            dt = max(now_time - prev_time, 1e-6)
            delta_bytes = max(now_bytes - prev_bytes, 0)
            mbps = (delta_bytes * 8.0) / (dt * 1_000_000.0)
            elapsed = round(now_time - start_time, 2)

            records.append({"waktu": elapsed, "bandwidth": round(mbps, 4)})
            prev_time = now_time
            prev_bytes = now_bytes

            live_df = pd.DataFrame(records)
            chart_placeholder.plotly_chart(
                _build_live_fig(live_df), width="stretch"
            )
            metric_placeholder.caption(
                f"Sampel {step}/{total_steps} | Waktu: {elapsed:.1f} detik | Laju terakhir: {mbps:.3f} Mbps"
            )
            progress_bar.progress(
                step / total_steps, text=f"Merekam sampel {step} dari {total_steps}..."
            )

        progress_bar.empty()
        captured_df = pd.DataFrame(records)
        st.session_state["last_capture_df"] = captured_df
        st.session_state["capture_direction"] = direction
        st.success(f"Perekaman selesai ({len(captured_df)} titik sampel).")
    except (OSError, RuntimeError) as exc:
        st.error(f"Perekaman gagal dijalankan pada lingkungan ini. Detail: {exc}")

st.divider()

last_df: pd.DataFrame = st.session_state.get("last_capture_df", pd.DataFrame())
if not last_df.empty:
    st.subheader("Hasil Perekaman Terakhir")
    col_tbl, col_act = st.columns([2, 1], gap="large")
    with col_tbl:
        st.dataframe(last_df, width="stretch", hide_index=True)
    with col_act:
        st.metric("Jumlah Sampel", f"{len(last_df)}")
        st.metric("Rata-rata Laju", f"{last_df['bandwidth'].mean():.3f} Mbps")
        st.metric("Puncak Laju", f"{last_df['bandwidth'].max():.3f} Mbps")
        if st.button("Gunakan sebagai Dataset Aktif", type="primary"):
            capture_label = (
                f"Live Capture ({st.session_state.get('capture_direction', 'Total')})"
            )
            set_active_dataset(
                last_df, dataset_name=capture_label, time_unit="detik", rate_unit="Mbps"
            )
            st.success(
                "Data rekaman kini menjadi dataset aktif. Lanjutkan ke halaman 2. Model & Integral."
            )
else:
    st.info(
        "Belum ada data rekaman pada sesi ini. Tekan tombol 'Mulai Perekaman' di atas untuk mengambil sampel."
    )
