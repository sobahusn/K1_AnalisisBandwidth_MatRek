"""Halaman 5: Unduh grafik PNG resolusi tinggi, CSV bersih, dan generator draf Subbab 4.2-4.6."""

from __future__ import annotations

import streamlit as st

from core.calculus import (
    compare_methods,
    compute_analytical_integral,
    compute_numeric_integrals,
    convert_integral_units,
)
from core.fitting import fit_polynomial, format_polynomial_text
from core.plotting import (
    build_comparison_bar_chart,
    build_integral_chart,
    export_figure_png,
)
from core.state_manager import get_active_state, validate_dataset

state = get_active_state()
is_valid, status_msg = validate_dataset(state.df)

st.title("5. Ekspor Grafik, Data Bersih, dan Draf Laporan")
st.caption(
    "Menyiapkan artefak siap pakai untuk penyusunan laporan Mini Research Subbab 4.2 hingga 4.6."
)

if not is_valid:
    st.error(status_msg)
    st.info(
        "Pastikan dataset aktif valid di halaman 1. Eksplorasi Data sebelum mengekspor laporan."
    )
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

fig_integral = build_integral_chart(
    t_obs=t_obs,
    b_obs=b_obs,
    coefficients=fit_res.coefficients,
    a=a_val,
    b=b_val,
    time_unit=state.time_unit,
    rate_unit=state.rate_unit,
    degree=degree,
)
fig_comp = build_comparison_bar_chart(
    u_ana.megabytes, u_trap.megabytes, u_simp.megabytes
)

st.subheader("Unduh Artefak Gambar dan Data")
d1, d2, d3 = st.columns(3)

with d1:
    csv_bytes = state.df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Unduh Dataset Bersih (CSV)",
        data=csv_bytes,
        file_name="dataset_bandwidth_bersih.csv",
        mime="text/csv",
        use_container_width=True,
    )

with d2:
    try:
        png_integral = export_figure_png(fig_integral)
        st.download_button(
            label="Unduh Grafik Kurva B(t) (PNG)",
            data=png_integral,
            file_name="grafik_kurva_bandwidth.png",
            mime="image/png",
            use_container_width=True,
        )
    except (ValueError, RuntimeError) as exc:
        st.warning(f"Ekspor PNG membutuhkan paket kaleido. Detail: {exc}")

with d3:
    try:
        png_comp = export_figure_png(fig_comp)
        st.download_button(
            label="Unduh Grafik Komparasi (PNG)",
            data=png_comp,
            file_name="grafik_komparasi_metode.png",
            mime="image/png",
            use_container_width=True,
        )
    except (ValueError, RuntimeError) as exc:
        st.warning(f"Ekspor PNG membutuhkan paket kaleido. Detail: {exc}")

st.divider()

poly_text = format_polynomial_text(fit_res.coefficients, precision=4)

draft_report = f"""## 4.2 Data Pengamatan dan Periode Analisis
Penelitian ini menggunakan dataset "{state.dataset_name}" yang terdiri dari {len(state.df)} titik pengamatan waktu pada selang [{a_val:g}, {b_val:g}] {state.time_unit}. Laju transfer data diukur dalam satuan {state.rate_unit}, dengan nilai minimum {state.df['bandwidth'].min():.2f} {state.rate_unit}, maksimum {state.df['bandwidth'].max():.2f} {state.rate_unit}, dan rata-rata {state.df['bandwidth'].mean():.2f} {state.rate_unit}.

## 4.3 Pemodelan Fungsi Kontinu B(t)
Berdasarkan metode kuadrat terkecil (regresi polinomial derajat {degree}), kurva laju bandwidth terhadap waktu dimodelkan sebagai:
{poly_text}

Evaluasi kecocokan model terhadap titik observasi menghasilkan koefisien determinasi R² = {fit_res.r_squared:.4f} dan Root Mean Square Error (RMSE) = {fit_res.rmse:.4f} {state.rate_unit}.

## 4.4 Perhitungan Total Transfer Data Secara Analitis
Total volume data selama periode [{a_val:g}, {b_val:g}] {state.time_unit} diperoleh melalui integral tentu fungsi B(t):
- Nilai integral mentah: {u_ana.raw_value:,.4f} {u_ana.raw_unit_label}
- Konversi Megabit: {u_ana.megabits:,.2f} Mb
- Konversi Megabyte (desimal, 1 MB = 8 Mb): {u_ana.megabytes:,.2f} MB
- Konversi Gigabyte (1 GB = 1000 MB): {u_ana.gigabytes:,.4f} GB

## 4.5 Perbandingan Integral Analitis dengan Metode Numerik
Hasil integral analitis dibandingkan dengan pendekatan numerik pada {numeric_res.n_points_used} titik data diskrit dalam selang yang sama:
- Integral Analitis (Polinomial d={degree}): {u_ana.megabytes:,.2f} MB ({u_ana.gigabytes:,.4f} GB)
- Aturan Trapesium: {u_trap.megabytes:,.2f} MB (galat relatif {comp.trapezoid_rel_error_pct:.3f}%)
- Aturan Simpson: {u_simp.megabytes:,.2f} MB (galat relatif {comp.simpson_rel_error_pct:.3f}%)

Perbedaan nilai antar metode muncul karena pendekatan polinomial menghaluskan fluktuasi data observasi, sedangkan Trapesium dan Simpson menjumlahkan luas pias langsung dari titik sampel diskrit.

## 4.6 Asumsi dan Keterbatasan Model
1. Fungsi B(t) mengasumsikan laju transfer kontinu pada [{a_val:g}, {b_val:g}], sedangkan trafik paket jaringan di lapisan fisik bersifat diskrit dan rentan lonjakan mendadak.
2. Pemilihan derajat polinomial perlu dibatasi agar model tidak mengalami osilasi berlebihan (overfitting) di antara titik sampel.
3. Model polinomial hanya sah untuk interpolasi dalam rentang pengamatan; ekstrapolasi di luar [{t_obs.min():g}, {t_obs.max():g}] {state.time_unit} dapat menghasilkan prediksi tidak realistis seperti nilai bandwidth negatif.
"""

st.subheader("Draf Teks Laporan (Subbab 4.2 sampai 4.6)")
edited_draft = st.text_area(
    "Sunting draf sebelum diunduh atau disalin", value=draft_report, height=420
)

st.download_button(
    label="Unduh Draf Laporan (Markdown)",
    data=edited_draft.encode("utf-8"),
    file_name="draf_subbab_4_2_sampai_4_6.md",
    mime="text/markdown",
    type="primary",
)
