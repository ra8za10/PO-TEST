"""
pivot.py
--------
Helpers for the interactive pivot-table feature. Kept free of any Streamlit
imports so it stays easy to unit-test in isolation.
"""

from __future__ import annotations

import pandas as pd

# Aggregation functions exposed in the UI -> pandas aggfunc name.
AGG_FUNCTIONS = {
    "Jumlah (SUM)": "sum",
    "Hitung (COUNT)": "count",
    "Rata-rata (MEAN)": "mean",
    "Maksimum (MAX)": "max",
    "Minimum (MIN)": "min",
}


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return a copy where the given columns are coerced to numbers.

    Values read back from Google Sheets arrive as strings; numeric aggregations
    (sum/mean) need real numbers. Unparseable cells become NaN.
    """
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def build_pivot(
    df: pd.DataFrame,
    rows: list[str],
    columns: list[str],
    values: str,
    aggfunc: str,
) -> pd.DataFrame:
    """Construct a pivot table from user-selected dimensions.

    Parameters mirror a spreadsheet pivot: `rows` (index), `columns`, the
    `values` field to aggregate, and the `aggfunc` to apply. For sum/mean/etc.
    we coerce the value column to numeric first; COUNT works on any dtype.
    """
    if not rows or not values:
        raise ValueError("Pilih minimal satu kolom baris dan satu kolom nilai.")

    working = df
    if aggfunc != "count":
        working = coerce_numeric(df, [values])

    pivot = pd.pivot_table(
        working,
        index=rows,
        columns=columns if columns else None,
        values=values,
        aggfunc=aggfunc,
        fill_value=0,
        margins=True,            # add a "Total" row/column...
        margins_name="Total",
    )
    return pivot
