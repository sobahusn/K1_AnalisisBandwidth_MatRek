"""Simulasi Skenario, Validasi Numerik, dan Keterbatasan: Komparasi Analitis vs Trapesium vs Simpson, evaluasi derajat R2/RMSE, uji ekstrapolasi, dan keterbatasan."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.calculus import (
    compare_methods,
    compute_analytical_integral,
    compute_numeric_integrals,
    convert_integral_units,
)
from core.fitting import fit_polynomial
from core.plotting import build_comparison_bar_chart, build_extrapolation_chart
from core.state_manager import get_active_state, validate_dataset

state = get_active_state()
is_valid, status_msg = validate_dataset(state.df)

st.title("4. Simulasi Skenario, Validasi Numerik, dan Keterbatasan")
st.caption(
    "Perbandingan 3 metode integrasi, menguji sensitivitas derajat, dan mengkaji batas model."
)

if not is_valid:
    st.error(status_msg)
    st.info("Muat atau perbaiki dataset di halaman 1. Eksplorasi Data terlebih dahulu.")
    st.stop()

t_obs = state.df["waktu"].to_numpy(dtype=float)
b_obs = state.df["bandwidth"].to_numpy(dtype=float)
a_val, b_val = state.domain_a, state.domain_b
degree = state.poly_degree

fit_res = fit_polynomial(t_obs, b_obs, degree=degree)
analytical_res = compute_analytical_integral(fit_res.coefficients, a=a_val, b=b_val)
numeric_res = compute_numeric_integrals(t_obs, b_obs, a=a_val, b=b_val)
comp = compare_methods(
    analytical_res.value_raw, numeric_res.trapezoid_raw, numeric_res.simpson_raw
)

u_ana = convert_integral_units(comp.analytical_raw, state.time_unit, state.rate_unit)
u_trap = convert_integral_units(comp.trapezoid_raw, state.time_unit, state.rate_unit)
u_simp = convert_integral_units(comp.simpson_raw, state.time_unit, state.rate_unit)

st.subheader(
    f"Perbandingan 3 Metode Integrasi pada [{a_val:g}, {b_val:g}] {state.time_unit}"
)

comp_df = pd.DataFrame(
    [
        {
            "Metode": f"Analitis Polinomial (d={degree})",
            f"Nilai Mentah ({u_ana.raw_unit_label})": round(u_ana.raw_value, 4),
            "Total (MB)": round(u_ana.megabytes, 2),
            "Total (GB)": round(u_ana.gigabytes, 4),
            "Galat Relatif (%)": 0.0,
        },
        {
            "Metode": "Numerik Aturan Trapesium",
            f"Nilai Mentah ({u_trap.raw_unit_label})": round(u_trap.raw_value, 4),
            "Total (MB)": round(u_trap.megabytes, 2),
            "Total (GB)": round(u_trap.gigabytes, 4),
            "Galat Relatif (%)": round(comp.trapezoid_rel_error_pct, 3),
        },
        {
            "Metode": "Numerik Aturan Simpson",
            f"Nilai Mentah ({u_simp.raw_unit_label})": round(u_simp.raw_value, 4),
            "Total (MB)": round(u_simp.megabytes, 2),
            "Total (GB)": round(u_simp.gigabytes, 4),
            "Galat Relatif (%)": round(comp.simpson_rel_error_pct, 3),
        },
    ]
)

col_tbl, col_chart = st.columns([1.2, 1], gap="large")
with col_tbl:
    st.dataframe(comp_df, width="stretch", hide_index=True)
    st.caption(
        f"Integrasi numerik menggunakan {numeric_res.n_points_used} titik data diskrit dalam rentang [{a_val:g}, {b_val:g}]. "
        "Galat relatif dihitung terhadap hasil integral analitis model polinomial."
    )
with col_chart:
    bar_fig = build_comparison_bar_chart(
        u_ana.megabytes, u_trap.megabytes, u_simp.megabytes
    )
    st.plotly_chart(bar_fig, width="stretch")

st.divider()

st.subheader("Evaluasi Derajat Polinomial (R² dan RMSE)")
max_deg = max(1, min(6, len(t_obs) - 1))
deg_rows = []
for d in range(1, max_deg + 1):
    res_d = fit_polynomial(t_obs, b_obs, degree=d)
    ana_d = compute_analytical_integral(res_d.coefficients, a=a_val, b=b_val)
    conv_d = convert_integral_units(ana_d.value_raw, state.time_unit, state.rate_unit)
    deg_rows.append(
        {
            "Derajat (d)": d,
            "R²": round(res_d.r_squared, 5),
            f"RMSE ({state.rate_unit})": round(res_d.rmse, 4),
            "Total Analitis (MB)": round(conv_d.megabytes, 2),
        }
    )
st.dataframe(pd.DataFrame(deg_rows), width="stretch", hide_index=True)

st.divider()

st.subheader("Uji Ekstrapolasi di Luar Domain Pengamatan")
span = float(t_obs.max() - t_obs.min())
default_extra = max(1.0, round(span * 0.25, 2))
extra_horizon = st.slider(
    f"Tambahan waktu ekstrapolasi setelah t = {t_obs.max():g} ({state.time_unit})",
    min_value=round(max(span * 0.05, 0.5), 2),
    max_value=round(max(span * 0.8, 5.0), 2),
    value=default_extra,
)

extrap_fig = build_extrapolation_chart(
    t_obs=t_obs,
    b_obs=b_obs,
    coefficients=fit_res.coefficients,
    extra_horizon=float(extra_horizon),
    time_unit=state.time_unit,
    rate_unit=state.rate_unit,
    degree=degree,
)
st.plotly_chart(extrap_fig, width="stretch")

st.divider()

st.subheader("Asumsi dan Keterbatasan Model (Langkah 6)")
st.markdown("""
    1. **Asumsi kekontinuan:** Model mengasumsikan laju bandwidth $B(t)$ berubah mulus sepanjang selang $[a, b]$, padahal trafik jaringan nyata bersifat diskrit per paket dan dapat mengalami lonjakan mendadak (*burst*).
    2. **Risiko overfitting polinomial derajat tinggi:** Menambah derajat polinomial menaikkan $R^2$ pada titik observasi, tetapi memicu osilasi tajam di antara titik sampel maupun saat ekstrapolasi (fenomena Runge).
    3. **Validitas ekstrapolasi:** Polinomial tidak memiliki batas fisik non-negatif; proyeksi di luar $[a, b]$ dapat menghasilkan nilai bandwidth negatif atau melonjak melampaui kapasitas tautan fisik.
    4. **Keterbatasan interval sampling:** Pada Aturan Trapesium dan Simpson, akurasi bergantung pada kerapatan waktu pengambilan sampel. Interval terlalu jarang dapat melewatkan puncak trafik singkat.
    """)
