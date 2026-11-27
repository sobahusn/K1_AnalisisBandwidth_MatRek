"""Komputasi integral analitis simbolik (SymPy), integrasi numerik (SciPy), dan konversi satuan data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp
from scipy.integrate import simpson, trapezoid
from sympy.parsing.sympy_parser import parse_expr

from core.state_manager import RATE_TO_MB_PER_SEC, TIME_UNITS


@dataclass(frozen=True)
class AnalyticalIntegralResult:
    """Hasil integral tentu secara analitis beserta ekspresi LaTeX untuk tampilan langkah."""

    value_raw: float
    f_at_a: float
    f_at_b: float
    latex_b_t: str
    latex_antiderivative: str
    latex_definite_integral: str
    latex_evaluation: str


@dataclass(frozen=True)
class NumericIntegralResult:
    """Hasil integrasi numerik Aturan Trapesium dan Simpson pada data diskrit."""

    trapezoid_raw: float
    simpson_raw: float
    n_points_used: int


@dataclass(frozen=True)
class UnitConversionResult:
    """Konversi nilai integral mentah ke Megabit, Megabyte (MB), dan Gigabyte (GB)."""

    raw_value: float
    raw_unit_label: str
    megabits: float
    megabytes: float
    gigabytes: float


@dataclass(frozen=True)
class ComparisonSummary:
    """Perbandingan integral analitis terhadap pendekatan Trapesium dan Simpson."""

    analytical_raw: float
    trapezoid_raw: float
    simpson_raw: float
    trapezoid_abs_error: float
    trapezoid_rel_error_pct: float
    simpson_abs_error: float
    simpson_rel_error_pct: float


def _build_sympy_poly(
    coefficients: np.ndarray, symbol: sp.Symbol, sig_digits: int = 5
) -> sp.Expr:
    """Membentuk ekspresi polinomial SymPy dengan pembulatan tampilan yang rapi."""
    deg = len(coefficients) - 1
    expr = sp.Integer(0)
    for idx, coeff in enumerate(coefficients):
        if abs(coeff) < 1e-12:
            continue
        power = deg - idx
        rounded = float(f"{coeff:.{sig_digits}g}")
        expr += sp.Float(rounded, sig_digits) * (symbol**power)
    return expr


def compute_analytical_integral(
    coefficients: np.ndarray,
    a: float,
    b: float,
) -> AnalyticalIntegralResult:
    """Menghitung integral tentu polinomial B(t) pada [a, b] dan menyusun langkah LaTeX."""
    if b <= a:
        raise ValueError("Batas atas b harus lebih besar daripada batas bawah a.")

    coeffs = np.asarray(coefficients, dtype=float)
    antideriv_coeffs = np.polyint(coeffs)
    f_at_a = float(np.polyval(antideriv_coeffs, a))
    f_at_b = float(np.polyval(antideriv_coeffs, b))
    exact_val = f_at_b - f_at_a

    t_sym = sp.Symbol("t", real=True)
    b_expr = _build_sympy_poly(coeffs, t_sym, sig_digits=5)
    f_expr = sp.integrate(b_expr, t_sym)

    latex_b_t = f"B(t) = {sp.latex(b_expr)}"
    latex_antideriv = rf"F(t) = \int B(t)\,dt = {sp.latex(f_expr)} + C"
    latex_definite = (
        rf"\int_{{{a:g}}}^{{{b:g}}} B(t)\,dt = \Big[ F(t) \Big]_{{{a:g}}}^{{{b:g}}} "
        f"= F({b:g}) - F({a:g})"
    )
    latex_eval = (
        f"F({b:g}) - F({a:g}) = {f_at_b:,.4f} - ({f_at_a:,.4f}) = {exact_val:,.4f}"
    )

    return AnalyticalIntegralResult(
        value_raw=exact_val,
        f_at_a=f_at_a,
        f_at_b=f_at_b,
        latex_b_t=latex_b_t,
        latex_antiderivative=latex_antideriv,
        latex_definite_integral=latex_definite,
        latex_evaluation=latex_eval,
    )


def compute_numeric_integrals(
    t: np.ndarray,
    b_values: np.ndarray,
    a: float,
    b: float,
) -> NumericIntegralResult:
    """Menghitung integral numerik Trapesium dan Simpson pada rentang data [a, b]."""
    t_arr = np.asarray(t, dtype=float)
    b_arr = np.asarray(b_values, dtype=float)

    mask = (t_arr >= a) & (t_arr <= b)
    t_sub = t_arr[mask]
    b_sub = b_arr[mask]

    # Sisipkan batas a atau b lewat interpolasi linear jika tidak persis jatuh pada titik sampel.
    if t_sub.size == 0 or t_sub[0] > a:
        b_at_a = float(np.interp(a, t_arr, b_arr))
        t_sub = np.insert(t_sub, 0, a)
        b_sub = np.insert(b_sub, 0, b_at_a)
    if t_sub[-1] < b:
        b_at_b = float(np.interp(b, t_arr, b_arr))
        t_sub = np.append(t_sub, b)
        b_sub = np.append(b_sub, b_at_b)

    trap_val = float(trapezoid(b_sub, x=t_sub))
    if t_sub.size >= 3:
        simp_val = float(simpson(b_sub, x=t_sub))
    else:
        simp_val = trap_val

    return NumericIntegralResult(
        trapezoid_raw=trap_val,
        simpson_raw=simp_val,
        n_points_used=int(t_sub.size),
    )


def compute_custom_symbolic_integral(
    expr_str: str,
    a: float,
    b: float,
) -> tuple[AnalyticalIntegralResult, np.ndarray, np.ndarray]:
    """Mem-parsing persamaan B(t) manual, menghitung integral tentu, dan menghasilkan kurva evaluasi."""
    if b <= a:
        raise ValueError("Batas atas b harus lebih besar daripada batas bawah a.")

    t_sym = sp.Symbol("t", real=True)
    allowed_locals = {
        "t": t_sym,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "exp": sp.exp,
        "sqrt": sp.sqrt,
        "log": sp.log,
        "pi": sp.pi,
    }
    b_expr = parse_expr(expr_str, local_dict=allowed_locals)
    if not b_expr.free_symbols.issubset({t_sym}):
        raise ValueError(
            "Gunakan variabel 't' saja sebagai peubah waktu pada persamaan B(t)."
        )

    f_expr = sp.integrate(b_expr, t_sym)
    if f_expr.has(sp.Integral):
        exact_val = float(sp.N(sp.Integral(b_expr, (t_sym, a, b))))
        f_at_a, f_at_b = 0.0, exact_val
        latex_antideriv = r"F(t) = \int B(t)\,dt \text{ (dievaluasi numerik adaptif)}"
        latex_eval = f"\\int_{{{a:g}}}^{{{b:g}}} B(t)\\,dt \\approx {exact_val:,.4f}"
    else:
        f_at_a = float(sp.N(f_expr.subs(t_sym, a)))
        f_at_b = float(sp.N(f_expr.subs(t_sym, b)))
        exact_val = f_at_b - f_at_a
        latex_antideriv = f"F(t) = \\int B(t)\\,dt = {sp.latex(f_expr)} + C"
        latex_eval = (
            f"F({b:g}) - F({a:g}) = {f_at_b:,.4f} - ({f_at_a:,.4f}) = {exact_val:,.4f}"
        )

    latex_b_t = f"B(t) = {sp.latex(b_expr)}"
    latex_definite = (
        f"\\int_{{{a:g}}}^{{{b:g}}} B(t)\\,dt = \\Big[ F(t) \\Big]_{{{a:g}}}^{{{b:g}}} "
        f"= F({b:g}) - F({a:g})"
    )

    t_grid = np.linspace(a, b, 250)
    b_func = sp.lambdify(t_sym, b_expr, modules="numpy")
    # Broadcast menangani ekspresi konstan (misalnya B(t) = 10) yang mengembalikan skalar.
    b_grid = np.broadcast_to(
        np.asarray(b_func(t_grid), dtype=float), t_grid.shape
    ).copy()

    result = AnalyticalIntegralResult(
        value_raw=exact_val,
        f_at_a=f_at_a,
        f_at_b=f_at_b,
        latex_b_t=latex_b_t,
        latex_antiderivative=latex_antideriv,
        latex_definite_integral=latex_definite,
        latex_evaluation=latex_eval,
    )
    return result, t_grid, b_grid


def convert_integral_units(
    raw_value: float,
    time_unit: str,
    rate_unit: str,
) -> UnitConversionResult:
    """Mengonversi luas kurva mentah ke satuan volume data (Mb, MB, GB) berbasis standar desimal."""
    sec_multiplier = TIME_UNITS[time_unit]
    mb_per_rate_sec = RATE_TO_MB_PER_SEC[rate_unit]

    megabytes = raw_value * sec_multiplier * mb_per_rate_sec
    gigabytes = megabytes / 1000.0
    megabits = megabytes * 8.0

    return UnitConversionResult(
        raw_value=raw_value,
        raw_unit_label=f"{rate_unit} * {time_unit}",
        megabits=megabits,
        megabytes=megabytes,
        gigabytes=gigabytes,
    )


def compare_methods(
    analytical_raw: float,
    trapezoid_raw: float,
    simpson_raw: float,
) -> ComparisonSummary:
    """Menghitung selisih absolut dan galat relatif (%) terhadap acuan integral analitis."""
    denom = abs(analytical_raw) if abs(analytical_raw) > 1e-12 else 1.0
    trap_abs = abs(trapezoid_raw - analytical_raw)
    simp_abs = abs(simpson_raw - analytical_raw)

    return ComparisonSummary(
        analytical_raw=analytical_raw,
        trapezoid_raw=trapezoid_raw,
        simpson_raw=simpson_raw,
        trapezoid_abs_error=trap_abs,
        trapezoid_rel_error_pct=(trap_abs / denom) * 100.0,
        simpson_abs_error=simp_abs,
        simpson_rel_error_pct=(simp_abs / denom) * 100.0,
    )
