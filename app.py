"""Entry point utama aplikasi Streamlit dengan router st.navigation()."""

from __future__ import annotations

import streamlit as st

from core.state_manager import get_active_state, init_session_state, validate_dataset

st.set_page_config(
    page_title="Analisis Bandwidth MatRek - Kelompok 1",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }
        [data-testid="stMetricValue"] {
            color: #0F172A;
            font-weight: 600;
        }
        [data-testid="stMetricLabel"] {
            color: #475569;
        }
        .status-box {
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 0.75rem 0.9rem;
            background-color: #F8FAFC;
            font-size: 0.88rem;
            color: #0F172A;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

init_session_state()

pages = {
    "Pengantar": [
        st.Page("pages/0_Beranda.py", title="Beranda", default=True),
    ],
    "Tahap Penelitian": [
        st.Page("pages/1_Eksplorasi_Data.py", title="1. Eksplorasi Data"),
        st.Page("pages/2_Model_Integral.py", title="2. Model & Integral"),
        st.Page("pages/3_Live_Capture.py", title="3. Live Capture"),
        st.Page("pages/4_Simulasi_Skenario.py", title="4. Simulasi & Validasi"),
    ],
    "Luaran": [
        st.Page("pages/5_Ekspor_Laporan.py", title="5. Ekspor Laporan"),
    ],
}

pg = st.navigation(pages)

state = get_active_state()
is_valid, status_msg = validate_dataset(state.df)

with st.sidebar:
    st.caption("Status Dataset Aktif")
    st.markdown(
        f"""
        <div class="status-box">
            <strong>Sumber:</strong> {state.dataset_name}<br/>
            <strong>Jumlah Titik:</strong> {len(state.df)} baris<br/>
            <strong>Domain [a, b]:</strong> [{state.domain_a:g}, {state.domain_b:g}] {state.time_unit}<br/>
            <strong>Satuan Laju:</strong> {state.rate_unit}<br/>
            <strong>Derajat Model:</strong> d = {state.poly_degree}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not is_valid:
        st.warning(status_msg)

pg.run()
