"""Modeling curve B(t) and its analytical integral using SymPy (LaTeX), area plots, and MB/GB conversion."""

from __future__ import annotations

import streamlit as st
from sympy.core.sympify import SympifyError

from core.calculus import (
    compute_analytical_integral,
    compute_custom_symbolic_integral,
    convert_integral_units,
)
from core.fitting import fit_polynomial
from core.plotting import build_custom_function_chart, build_integral_chart
from core.state_manager import get_active_state, validate_dataset

state = get_active_state()
model_source = st.radio(
    "Sumber Fungsi B(t)",
    options=["Regresi Polinomial dari Dataset Aktif", "Input Persamaan B(t) Manual"],
    horizontal=True,
)

if model_source == "Input Persamaan B(t) Manual":
    expr_str = st.text_input(
        "Persamaan B(t) dalam variabel t",
        value="-0.5*t**2 + 4*t + 2",
        help="Gunakan sintaks Python/SymPy, misalnya: 2*t + 5, -0.5*t**2 + 4*t + 2, atau 10 + 3*sin(t).",
    )
    mc1, mc2, mc3 = st.columns([1, 1, 1])
    a_val = float(
        mc1.number_input(f"Batas Bawah a ({state.time_unit})", value=0.0, step=0.5)
    )
    b_val = float(
        mc2.number_input(f"Batas Atas b ({state.time_unit})", value=6.0, step=0.5)
    )
    show_mean_line = mc3.checkbox("Tampilkan Garis Rata-Rata B̄", value=True)

    try:
        analytical_res, t_grid, b_grid = compute_custom_symbolic_integral(
            expr_str, a=a_val, b=b_val
        )
        unit_res = convert_integral_units(
            analytical_res.value_raw, state.time_unit, state.rate_unit
        )
        mean_b = analytical_res.value_raw / (b_val - a_val)

        fig = build_custom_function_chart(
            t_grid=t_grid,
            b_grid=b_grid,
            a=a_val,
            b=b_val,
            time_unit=state.time_unit,
            rate_unit=state.rate_unit,
            mean_value=mean_b if show_mean_line else None,
        )
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Data (MB)", f"{unit_res.megabytes:,.2f} MB")
        m2.metric("Total Data (GB)", f"{unit_res.gigabytes:,.4f} GB")
        m3.metric("Rata-Rata Integral (B̄)", f"{mean_b:.3f} {state.rate_unit}")

        st.divider()
        st.subheader("Langkah Perhitungan Integral Analitis (SymPy)")
        st.latex(analytical_res.latex_b_t)
        st.latex(analytical_res.latex_antiderivative)
        st.latex(analytical_res.latex_definite_integral)
        st.latex(analytical_res.latex_evaluation)
    except (SympifyError, SyntaxError, TypeError, ValueError, ZeroDivisionError) as exc:
        st.error(f"Persamaan tidak dapat diproses: {exc}")
    st.stop()

is_valid, status_msg = validate_dataset(state.df)

st.title("2. Pemodelan Kurva B(t) dan Integral Analitis")
st.caption(
    "Pembentukan fungsi kontinu B(t) dan menghitung integral tentu secara analitis."
)

if not is_valid:
    st.error(status_msg)
    st.info(
        "Perbaiki atau muat dataset di halaman 1. Eksplorasi Data sebelum menjalankan pemodelan."
    )
    st.stop()

t_obs = state.df["waktu"].to_numpy(dtype=float)
b_obs = state.df["bandwidth"].to_numpy(dtype=float)
t_min = float(t_obs.min())
t_max = float(t_obs.max())
max_degree = max(1, min(6, len(t_obs) - 1))

ctrl_col1, ctrl_col2 = st.columns([1, 2], gap="large")

with ctrl_col1:
    degree = st.slider(
        "Derajat Polinomial (d)",
        min_value=1,
        max_value=max_degree,
        value=min(state.poly_degree, max_degree),
        help="Derajat terlalu tinggi pada sedikit titik berisiko overfitting.",
    )
    st.session_state["poly_degree"] = degree

with ctrl_col2:
    bound_mode = st.radio(
        "Pengaturan Batas Integrasi [a, b]",
        options=["Slider", "Input Angka Presisi"],
        horizontal=True,
    )
    if bound_mode == "Slider":
        domain_range = st.slider(
            f"Batas Integrasi [a, b] ({state.time_unit})",
            min_value=t_min,
            max_value=t_max,
            value=(state.domain_a, state.domain_b),
        )
        a_val, b_val = float(domain_range[0]), float(domain_range[1])
    else:
        num_c1, num_c2 = st.columns(2)
        a_val = float(
            num_c1.number_input(
                f"Batas Bawah a ({state.time_unit})",
                min_value=t_min,
                max_value=t_max,
                value=state.domain_a,
                step=0.25,
                format="%.4f",
            )
        )
        b_val = float(
            num_c2.number_input(
                f"Batas Atas b ({state.time_unit})",
                min_value=t_min,
                max_value=t_max,
                value=state.domain_b,
                step=0.25,
                format="%.4f",
            )
        )
if b_val <= a_val:
    st.warning(
        "Batas atas b harus lebih besar daripada batas bawah a. Geser slider batas integrasi."
    )
    st.stop()

st.session_state["domain_a"] = a_val
st.session_state["domain_b"] = b_val

fit_res = fit_polynomial(t_obs, b_obs, degree=degree)
analytical_res = compute_analytical_integral(fit_res.coefficients, a=a_val, b=b_val)
unit_res = convert_integral_units(
    analytical_res.value_raw, state.time_unit, state.rate_unit
)

chart_mode = st.radio(
    "Mode Tampilan Grafik",
    options=[
        "Kurva Polinomial Analitis",
        "Garis Patah-Patah (Trapesium)",
        "Gabungan (Analitis + Trapesium)",
    ],
    horizontal=True,
)

show_mean_line = st.checkbox(
    "Tampilkan garis nilai rata-rata integral (B̄ = 1/(b-a) ∫ B(t) dt)",
    value=True,
)
mean_b = analytical_res.value_raw / (b_val - a_val)

fig = build_integral_chart(
    t_obs=t_obs,
    b_obs=b_obs,
    coefficients=fit_res.coefficients,
    a=a_val,
    b=b_val,
    time_unit=state.time_unit,
    rate_unit=state.rate_unit,
    degree=degree,
    chart_mode=chart_mode,
    mean_value=mean_b if show_mean_line else None,
)

fig = build_integral_chart(
    t_obs=t_obs,
    b_obs=b_obs,
    coefficients=fit_res.coefficients,
    a=a_val,
    b=b_val,
    time_unit=state.time_unit,
    rate_unit=state.rate_unit,
    degree=degree,
    chart_mode=chart_mode,
)
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Data (MB)", f"{unit_res.megabytes:,.2f} MB")
m2.metric("Total Data (GB)", f"{unit_res.gigabytes:,.4f} GB")
m3.metric("Koefisien Determinasi (R²)", f"{fit_res.r_squared:.4f}")
m4.metric("RMSE", f"{fit_res.rmse:.3f} {state.rate_unit}")

st.divider()

st.subheader("Langkah Perhitungan Integral Analitis (SymPy)")
st.markdown("1. Model fungsi kontinu $B(t)$ hasil regresi polinomial:")
st.latex(analytical_res.latex_b_t)

st.markdown("2. Antiturunan (integral tak tentu) $F(t)$:")
st.latex(analytical_res.latex_antiderivative)

st.markdown("3. Evaluasi integral tentu berdasarkan Teorema Dasar Kalkulus:")
st.latex(analytical_res.latex_definite_integral)
st.latex(analytical_res.latex_evaluation)

st.markdown(f"""
    4. Konversi satuan volume data:
    - Nilai integral mentah: **{unit_res.raw_value:,.4f} {unit_res.raw_unit_label}**
    - Volume dalam Megabit: **{unit_res.megabits:,.2f} Mb**
    - Volume dalam Megabyte: **{unit_res.megabytes:,.2f} MB**
    - Volume dalam Gigabyte: **{unit_res.gigabytes:,.4f} GB**
    """)
