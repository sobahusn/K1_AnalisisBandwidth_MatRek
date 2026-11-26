"""Visualisasi interaktif Plotly dan ekspor gambar PNG resolusi tinggi."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from core.fitting import evaluate_polynomial

# Palet terkendali: 2 warna inti (biru slate, teal) + 1 aksen (terakota).
COLOR_PRIMARY = "#1E3A5F"
COLOR_SECONDARY = "#0F766E"
COLOR_ACCENT = "#C2410C"
COLOR_FILL = "rgba(194, 65, 12, 0.18)"
COLOR_GRID = "#E2E8F0"
COLOR_TEXT = "#0F172A"
COLOR_MUTED = "#475569"


def _apply_base_layout(
    fig: go.Figure, title: str, x_title: str, y_title: str
) -> go.Figure:
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 16, "color": COLOR_TEXT},
            "x": 0.0,
            "xanchor": "left",
        },
        xaxis={
            "title": x_title,
            "showgrid": True,
            "gridcolor": COLOR_GRID,
            "zeroline": False,
            "color": COLOR_MUTED,
        },
        yaxis={
            "title": y_title,
            "showgrid": True,
            "gridcolor": COLOR_GRID,
            "zeroline": True,
            "zerolinecolor": "#CBD5E1",
            "color": COLOR_MUTED,
        },
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font={"family": "sans-serif", "size": 12, "color": COLOR_TEXT},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
        margin={"l": 55, "r": 25, "t": 65, "b": 50},
        hovermode="x unified",
    )
    return fig


def build_integral_chart(
    t_obs: np.ndarray,
    b_obs: np.ndarray,
    coefficients: np.ndarray,
    a: float,
    b: float,
    time_unit: str,
    rate_unit: str,
    degree: int,
    chart_mode: str = "Kurva Polinomial Analitis",
) -> go.Figure:
    """Membuat grafik titik data, kurva B(t), garis Trapesium, dan arsiran area integral pada [a, b]."""
    t_min = float(np.min(t_obs))
    t_max = float(np.max(t_obs))

    fig = go.Figure()

    if chart_mode in ("Kurva Polinomial Analitis", "Gabungan (Analitis + Trapesium)"):
        t_curve = np.linspace(t_min, t_max, 250)
        b_curve = evaluate_polynomial(coefficients, t_curve)
        t_fill = np.linspace(a, b, 200)
        b_fill = evaluate_polynomial(coefficients, t_fill)

        fig.add_trace(
            go.Scatter(
                x=t_fill,
                y=b_fill,
                mode="lines",
                line={"width": 0},
                fill="tozeroy",
                fillcolor=COLOR_FILL,
                name=f"Area Analitis [{a:g}, {b:g}]",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=t_curve,
                y=b_curve,
                mode="lines",
                line={"color": COLOR_PRIMARY, "width": 2.5},
                name=f"Model Polinomial B(t) (d={degree})",
            )
        )

    if chart_mode in (
        "Garis Patah-Patah (Trapesium)",
        "Gabungan (Analitis + Trapesium)",
    ):
        mask = (t_obs >= a) & (t_obs <= b)
        t_sub = t_obs[mask]
        b_sub = b_obs[mask]
        if t_sub.size == 0 or t_sub[0] > a:
            t_sub = np.insert(t_sub, 0, a)
            b_sub = np.insert(b_sub, 0, float(np.interp(a, t_obs, b_obs)))
        if t_sub[-1] < b:
            t_sub = np.append(t_sub, b)
            b_sub = np.append(b_sub, float(np.interp(b, t_obs, b_obs)))

        if chart_mode == "Garis Patah-Patah (Trapesium)":
            fig.add_trace(
                go.Scatter(
                    x=t_sub,
                    y=b_sub,
                    mode="lines",
                    line={"width": 0},
                    fill="tozeroy",
                    fillcolor="rgba(30, 58, 95, 0.18)",
                    name=f"Area Trapesium [{a:g}, {b:g}]",
                    hoverinfo="skip",
                )
            )

        fig.add_trace(
            go.Scatter(
                x=t_obs,
                y=b_obs,
                mode="lines+markers",
                line={"color": COLOR_PRIMARY, "width": 2.0},
                marker={
                    "color": COLOR_ACCENT,
                    "size": 8,
                    "line": {"color": "#FFFFFF", "width": 1.5},
                },
                name="Garis Trapesium (Data Observasi)",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=t_obs,
                y=b_obs,
                mode="markers",
                marker={
                    "color": COLOR_ACCENT,
                    "size": 8,
                    "line": {"color": "#FFFFFF", "width": 1.5},
                },
                name="Data Observasi",
            )
        )

    fig.add_vline(x=a, line_dash="dot", line_color=COLOR_MUTED, line_width=1.2)
    fig.add_vline(x=b, line_dash="dot", line_color=COLOR_MUTED, line_width=1.2)

    return _apply_base_layout(
        fig,
        title=f"Laju Bandwidth B(t) dan Luas Transfer Data pada [{a:g}, {b:g}] {time_unit}",
        x_title=f"Waktu t ({time_unit})",
        y_title=f"Laju Bandwidth ({rate_unit})",
    )


def build_extrapolation_chart(
    t_obs: np.ndarray,
    b_obs: np.ndarray,
    coefficients: np.ndarray,
    extra_horizon: float,
    time_unit: str,
    rate_unit: str,
    degree: int,
) -> go.Figure:
    """Memvisualisasikan kurva model di dalam domain observasi dan proyeksi ekstrapolasi."""
    t_min = float(np.min(t_obs))
    t_max = float(np.max(t_obs))
    t_end = t_max + max(extra_horizon, 1e-6)

    t_in = np.linspace(t_min, t_max, 200)
    b_in = evaluate_polynomial(coefficients, t_in)

    t_out = np.linspace(t_max, t_end, 120)
    b_out = evaluate_polynomial(coefficients, t_out)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=t_in,
            y=b_in,
            mode="lines",
            line={"color": COLOR_PRIMARY, "width": 2.5},
            name=f"Interpolasi B(t) (d={degree})",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=t_out,
            y=b_out,
            mode="lines",
            line={"color": COLOR_ACCENT, "width": 2.5, "dash": "dash"},
            name="Ekstrapolasi di Luar Domain",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=t_obs,
            y=b_obs,
            mode="markers",
            marker={
                "color": COLOR_SECONDARY,
                "size": 8,
                "line": {"color": "#FFFFFF", "width": 1.2},
            },
            name="Data Observasi",
        )
    )

    fig.add_vline(
        x=t_max,
        line_dash="dot",
        line_color=COLOR_MUTED,
        annotation_text="Batas Observasi",
        annotation_position="top right",
    )

    return _apply_base_layout(
        fig,
        title=f"Uji Ekstrapolasi Polinomial Derajat {degree} hingga t = {t_end:g} {time_unit}",
        x_title=f"Waktu t ({time_unit})",
        y_title=f"Laju Bandwidth ({rate_unit})",
    )


def build_comparison_bar_chart(
    analytical_mb: float,
    trapezoid_mb: float,
    simpson_mb: float,
) -> go.Figure:
    """Membuat diagram batang perbandingan total transfer data (MB) dari 3 metode integrasi."""
    methods = ["Analitis (SymPy)", "Numerik Trapesium", "Numerik Simpson"]
    values = [analytical_mb, trapezoid_mb, simpson_mb]
    colors = [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT]

    fig = go.Figure(
        data=[
            go.Bar(
                x=methods,
                y=values,
                marker_color=colors,
                text=[f"{v:,.2f} MB" for v in values],
                textposition="outside",
                width=0.45,
            )
        ]
    )

    max_val = max(values) if values else 1.0
    fig.update_yaxes(range=[0, max_val * 1.18 if max_val > 0 else 1.0])

    return _apply_base_layout(
        fig,
        title="Perbandingan Total Transfer Data Berdasarkan Metode Integrasi",
        x_title="Metode Integrasi",
        y_title="Total Volume Data (MB)",
    )


def export_figure_png(
    fig: go.Figure, width: int = 1280, height: int = 720, scale: int = 2
) -> bytes:
    """Merender grafik Plotly menjadi byte PNG resolusi tinggi melalui Kaleido."""
    return fig.to_image(format="png", width=width, height=height, scale=scale)
