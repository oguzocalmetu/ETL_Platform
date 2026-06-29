"""
Transform Service — applies column-level transformation rules to a Polars DataFrame.
Each rule is applied in apply_order sequence per column mapping.
"""
from typing import Any
import polars as pl

from app.connectors.base import DataException


POLARS_CAST_MAP = {
    "integer": pl.Int32, "int": pl.Int32,
    "bigint": pl.Int64, "long": pl.Int64,
    "smallint": pl.Int16,
    "float": pl.Float32,
    "double": pl.Float64, "decimal": pl.Float64,
    "string": pl.Utf8, "varchar": pl.Utf8, "text": pl.Utf8,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "timestamp": pl.Datetime,
}


def _apply_single_transform(series: pl.Series, transform_type: str, params: dict[str, Any]) -> pl.Series:
    t = transform_type.upper()

    if t == "TRIM":
        return series.str.strip_chars()

    elif t == "UPPER":
        return series.str.to_uppercase()

    elif t == "LOWER":
        return series.str.to_lowercase()

    elif t == "REPLACE":
        return series.str.replace_all(params["from"], params["to"])

    elif t == "CAST":
        to_type = params.get("to_type", "string").lower()
        polars_type = POLARS_CAST_MAP.get(to_type, pl.Utf8)
        try:
            return series.cast(polars_type, strict=False)
        except Exception as e:
            raise DataException("CAST_ERROR", f"'{series.name}' cast edilemedi: {to_type}", str(e))

    elif t == "TO_DATE":
        fmt = params.get("format", "%Y-%m-%d")
        return series.str.to_date(fmt, strict=False)

    elif t == "TO_TIMESTAMP":
        fmt = params.get("format", "%Y-%m-%d %H:%M:%S")
        return series.str.to_datetime(fmt, strict=False)

    elif t == "SUBSTRING":
        start = params.get("start", 0)
        length = params.get("length")
        if length:
            return series.str.slice(start, length)
        return series.str.slice(start)

    elif t == "CONCAT":
        # Concat with a literal value: params = {"value": "prefix_", "position": "prefix|suffix"}
        val = params.get("value", "")
        position = params.get("position", "suffix")
        if position == "prefix":
            return pl.lit(val) + series
        return series + pl.lit(val)

    elif t == "COALESCE":
        default = params.get("default", "")
        return series.fill_null(pl.lit(default))

    elif t == "DEFAULT_VALUE":
        default = params.get("value", "")
        return series.fill_null(pl.lit(default))

    elif t == "NULL_HANDLING":
        strategy = params.get("strategy", "fill")  # fill, drop (drop handled at df level)
        if strategy == "fill":
            return series.fill_null(pl.lit(params.get("fill_value", "")))
        return series  # drop handled separately

    elif t == "CASE_WHEN":
        # params: {"conditions": [{"when": "value1", "then": "result1"}, ...], "else": "default"}
        conditions = params.get("conditions", [])
        expr = pl.when(pl.lit(False)).then(pl.lit(None))
        for cond in conditions:
            expr = expr.when(series == cond["when"]).then(pl.lit(cond["then"]))
        expr = expr.otherwise(pl.lit(params.get("else", None)))
        return expr

    else:
        # Unknown transform — pass through
        return series


def apply_transforms(df: pl.DataFrame, mappings: list) -> pl.DataFrame:
    """
    Apply all transform rules from column mappings to the DataFrame.
    mappings: list of ColumnMapping ORM objects (with .source_column, .target_column, .transform_rules)
    """
    for mapping in mappings:
        if mapping.is_excluded:
            if mapping.source_column and mapping.source_column in df.columns:
                df = df.drop(mapping.source_column)
            continue

        if mapping.is_constant:
            # Add a constant/literal column
            df = df.with_columns(pl.lit(mapping.constant_value).alias(mapping.target_column))
            continue

        col = mapping.source_column
        if col not in df.columns:
            if not mapping.is_nullable and mapping.default_value is None:
                raise DataException(
                    "COLUMN_NOT_FOUND",
                    f"Kaynak kolon bulunamadı: '{col}'",
                )
            # Column missing but nullable — add null column
            df = df.with_columns(pl.lit(mapping.default_value).alias(mapping.target_column))
            continue

        # Apply transforms in order
        series = df[col]
        for rule in sorted(mapping.transform_rules, key=lambda r: r.apply_order):
            series = _apply_single_transform(series, rule.transform_type, rule.params or {})

        # Rename source → target
        if mapping.source_column != mapping.target_column:
            df = df.drop(col).with_columns(series.alias(mapping.target_column))
        else:
            df = df.with_columns(series.alias(col))

    return df
