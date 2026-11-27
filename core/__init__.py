"""Modul komputasi matematika, manajemen state, dan visualisasi untuk K1_AnalisisBandwidth_MatRek."""

from core.calculus import (
    AnalyticalIntegralResult,
    ComparisonSummary,
    NumericIntegralResult,
    UnitConversionResult,
    compare_methods,
    compute_analytical_integral,
    compute_custom_symbolic_integral,
    compute_numeric_integrals,
    convert_integral_units,
)
from core.fitting import (
    PolynomialFitResult,
    evaluate_polynomial,
    fit_polynomial,
    format_polynomial_text,
)
from core.plotting import (
    build_comparison_bar_chart,
    build_extrapolation_chart,
    build_integral_chart,
    export_figure_png,
)
from core.state_manager import (
    PRESET_DATASETS,
    RATE_UNITS,
    TIME_UNITS,
    clean_bandwidth_dataframe,
    get_active_state,
    init_session_state,
    load_preset_dataset,
    set_active_dataset,
    validate_dataset,
)

__all__ = [
    "PRESET_DATASETS",
    "RATE_UNITS",
    "TIME_UNITS",
    "AnalyticalIntegralResult",
    "ComparisonSummary",
    "NumericIntegralResult",
    "PolynomialFitResult",
    "UnitConversionResult",
    "build_comparison_bar_chart",
    "build_extrapolation_chart",
    "build_integral_chart",
    "clean_bandwidth_dataframe",
    "compare_methods",
    "compute_analytical_integral",
    "compute_custom_symbolic_integral",
    "compute_numeric_integrals",
    "convert_integral_units",
    "evaluate_polynomial",
    "export_figure_png",
    "fit_polynomial",
    "format_polynomial_text",
    "get_active_state",
    "init_session_state",
    "load_preset_dataset",
    "set_active_dataset",
    "validate_dataset",
]
