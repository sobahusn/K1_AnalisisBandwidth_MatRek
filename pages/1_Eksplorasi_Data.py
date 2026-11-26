"""Halaman 1: Pemilihan preset CSV, unggah CSV/XLSX, pengaturan satuan, dan editor tabel interaktif."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.state_manager import (
    PRESET_DATASETS,
    RATE_UNITS,
    TIME_UNITS,
    clean_bandwidth_dataframe,
    get_active_state,
    load_preset_dataset,
    set_active_dataset,
    validate_dataset,
)

state = get_active_state()

st.title("1. Eksplorasi Data dan Penentuan Satuan")
st.caption(
    "Langkah 1 & 2 Penelitian: Menetapkan periode [a, b], satuan pengukuran, dan menyusun tabel data B(t)."
)

source_tab1, source_tab2 = st.tabs(["Dataset Preset", "Unggah CSV / XLSX"])

with source_tab1:
    preset_names = list(PRESET_DATASETS.keys())
    default_idx = (
        preset_names.index(state.dataset_name)
        if state.dataset_name in preset_names
        else 0
    )
    selected_preset = st.selectbox(
        "Pilih skenario data bawaan", options=preset_names, index=default_idx
    )
    st.caption(PRESET_DATASETS[selected_preset]["description"])

    if st.button("Muat Dataset Preset", type="primary"):
        df_preset, t_unit, r_unit = load_preset_dataset(selected_preset)
        set_active_dataset(
            df_preset, selected_preset, time_unit=t_unit, rate_unit=r_unit
        )
        st.success(f"Dataset '{selected_preset}' dimuat ({len(df_preset)} titik).")
        st.rerun()

with source_tab2:
    st.markdown(
        "Berkas harus memuat minimal 2 kolom numerik: kolom pertama sebagai `waktu` dan kolom kedua sebagai `bandwidth`."
    )
    uploaded_file = st.file_uploader("Unggah berkas data", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".xlsx"):
                raw_df = pd.read_excel(uploaded_file)
            else:
                raw_df = pd.read_csv(uploaded_file)

            cleaned_df = clean_bandwidth_dataframe(raw_df)
            valid_upload, upload_msg = validate_dataset(cleaned_df)
            if not valid_upload:
                st.error(f"Berkas gagal divalidasi: {upload_msg}")
            else:
                st.dataframe(
                    cleaned_df.head(10), use_container_width=True, hide_index=True
                )
                if st.button("Terapkan Berkas Unggahan", type="primary"):
                    set_active_dataset(cleaned_df, f"Unggahan: {uploaded_file.name}")
                    st.success(f"Berkas '{uploaded_file.name}' aktif untuk analisis.")
                    st.rerun()
        except Exception as exc:
            st.error(
                f"Gagal membaca berkas. Pastikan format CSV atau XLSX tidak rusak. Detail: {exc}"
            )

st.divider()

st.subheader("Pengaturan Satuan dan Penyuntingan Data")
unit_col1, unit_col2 = st.columns(2)
time_options = list(TIME_UNITS.keys())
rate_options = list(RATE_UNITS)

chosen_time = unit_col1.selectbox(
    "Satuan Waktu (sumbu t)",
    options=time_options,
    index=time_options.index(state.time_unit) if state.time_unit in time_options else 0,
)
chosen_rate = unit_col2.selectbox(
    "Satuan Laju Transfer B(t)",
    options=rate_options,
    index=rate_options.index(state.rate_unit) if state.rate_unit in rate_options else 0,
)

if chosen_time != state.time_unit or chosen_rate != state.rate_unit:
    st.session_state["time_unit"] = chosen_time
    st.session_state["rate_unit"] = chosen_rate

edited_df = st.data_editor(
    state.df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "waktu": st.column_config.NumberColumn(
            label=f"Waktu ({chosen_time})",
            help="Nilai waktu pengamatan. Duplikat waktu akan dirata-rata otomatis saat disimpan.",
            format="%.2f",
        ),
        "bandwidth": st.column_config.NumberColumn(
            label=f"Bandwidth ({chosen_rate})",
            help="Laju transfer data non-negatif.",
            min_value=0.0,
            format="%.2f",
        ),
    },
    key="bandwidth_data_editor",
)

if st.button("Simpan Perubahan Tabel"):
    cleaned_edit = clean_bandwidth_dataframe(edited_df)
    valid_edit, edit_msg = validate_dataset(cleaned_edit)
    if not valid_edit:
        st.error(edit_msg)
    else:
        set_active_dataset(
            cleaned_edit,
            dataset_name=state.dataset_name,
            time_unit=chosen_time,
            rate_unit=chosen_rate,
        )
        st.success(f"Perubahan disimpan ({len(cleaned_edit)} titik waktu unik).")
        st.rerun()

st.divider()

current_state = get_active_state()
is_valid, status_msg = validate_dataset(current_state.df)
if is_valid:
    st.subheader("Statistik Deskriptif Dataset Aktif")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jumlah Titik", f"{len(current_state.df)}")
    c2.metric(
        "Durasi Total",
        f"{current_state.df['waktu'].max() - current_state.df['waktu'].min():g} {current_state.time_unit}",
    )
    c3.metric(
        "Laju Minimum",
        f"{current_state.df['bandwidth'].min():.2f} {current_state.rate_unit}",
    )
    c4.metric(
        "Laju Maksimum",
        f"{current_state.df['bandwidth'].max():.2f} {current_state.rate_unit}",
    )
else:
    st.warning(status_msg)
