"""Regresi polinomial B(t) menggunakan numpy.polyfit dan metrik evaluasi kebaikan model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PolynomialFitResult:
    """Hasil regresi polinomial beserta metrik galat pada data observasi."""

    degree: int
    coefficients: np.ndarray
    y_pred: np.ndarray
    r_squared: float
    rmse: float
    mae: float


def fit_polynomial(t: np.ndarray, b: np.ndarray, degree: int) -> PolynomialFitResult:
    """Mencocokkan kurva polinomial berderajat `degree` ke data (t, B(t))."""
    t_arr = np.asarray(t, dtype=float)
    b_arr = np.asarray(b, dtype=float)

    if t_arr.size < 2:
        raise ValueError(
            "Minimal dibutuhkan 2 titik data untuk membentuk fungsi regresi."
        )
    if t_arr.size != b_arr.size:
        raise ValueError("Panjang vektor waktu dan bandwidth harus sama.")

    safe_degree = int(np.clip(degree, 1, t_arr.size - 1))
    coeffs = np.polyfit(t_arr, b_arr, deg=safe_degree)
    y_pred = np.polyval(coeffs, t_arr)

    residuals = b_arr - y_pred
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((b_arr - np.mean(b_arr)) ** 2))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0.0 else 1.0
    rmse = float(np.sqrt(np.mean(residuals**2)))
    mae = float(np.mean(np.abs(residuals)))

    return PolynomialFitResult(
        degree=safe_degree,
        coefficients=coeffs,
        y_pred=y_pred,
        r_squared=r_squared,
        rmse=rmse,
        mae=mae,
    )


def evaluate_polynomial(coefficients: np.ndarray, t_values: np.ndarray) -> np.ndarray:
    """Mengevaluasi polinomial pada array nilai t."""
    return np.polyval(
        np.asarray(coefficients, dtype=float), np.asarray(t_values, dtype=float)
    )


def format_polynomial_text(coefficients: np.ndarray, precision: int = 4) -> str:
    """Menyusun persamaan teks B(t) yang mudah dibaca untuk laporan dan tabel."""
    deg = len(coefficients) - 1
    terms: list[str] = []
    for idx, coeff in enumerate(coefficients):
        power = deg - idx
        if abs(coeff) < 1e-12:
            continue
        sign = "-" if coeff < 0 else "+"
        val = f"{abs(coeff):.{precision}f}"
        if power == 0:
            term = val
        elif power == 1:
            term = f"{val}t"
        else:
            term = f"{val}t^{power}"

        if not terms:
            terms.append(f"-{term}" if sign == "-" else term)
        else:
            terms.append(f"{sign} {term}")

    return "B(t) = " + (" ".join(terms) if terms else "0")
