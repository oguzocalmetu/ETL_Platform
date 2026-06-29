"""
Validation Service — applies validation rules to a Polars DataFrame.
Returns valid rows and rejected records.
"""
from dataclasses import dataclass, field
from typing import Any
import re
import polars as pl


@dataclass
class RejectedRow:
    row_number: int
    source_data: dict
    error_column: str
    error_rule: str
    error_message: str


@dataclass
class ValidationResult:
    valid_df: pl.DataFrame
    rejected_records: list[RejectedRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate(df: pl.DataFrame, validation_rules: list) -> ValidationResult:
    """
    Apply all validation rules.
    Rules with action_on_fail=REJECT remove rows from valid_df.
    Rules with action_on_fail=WARN add to warnings.
    Rules with action_on_fail=STOP raise immediately.
    """
    rejected: list[RejectedRow] = []
    warnings: list[str] = []
    reject_mask = pl.Series("_reject", [False] * len(df))

    for rule in validation_rules:
        col = None
        if hasattr(rule, 'mapping') and rule.mapping:
            col = rule.mapping.target_column

        rule_type = rule.rule_type.upper()
        params = rule.params or {}
        action = (rule.action_on_fail or "REJECT").upper()

        fail_mask = _evaluate_rule(df, col, rule_type, params)

        if fail_mask is None:
            continue

        failing_indices = fail_mask.arg_true().to_list()
        if not failing_indices:
            continue

        msg = _rule_message(rule_type, col, params)

        if action == "STOP":
            raise RuntimeError(f"Validation STOP kuralı tetiklendi: {msg} — {len(failing_indices)} hatalı kayıt")

        for idx in failing_indices:
            row_dict = {c: df[c][idx] for c in df.columns}
            rejected.append(RejectedRow(
                row_number=idx,
                source_data=row_dict,
                error_column=col or "",
                error_rule=rule_type,
                error_message=msg,
            ))
            if action == "REJECT":
                reject_mask[idx] = True

        if action == "WARN":
            warnings.append(f"{msg}: {len(failing_indices)} kayıt etkilendi")

    valid_df = df.filter(~reject_mask)
    return ValidationResult(valid_df=valid_df, rejected_records=rejected, warnings=warnings)


def _evaluate_rule(df: pl.DataFrame, col: str | None, rule_type: str, params: dict) -> pl.Series | None:
    """Return a boolean Series where True = row fails the rule."""

    if rule_type == "NOT_NULL":
        if col and col in df.columns:
            return df[col].is_null()

    elif rule_type == "UNIQUE":
        if col and col in df.columns:
            return df[col].is_duplicated()

    elif rule_type == "REGEX":
        pattern = params.get("pattern", "")
        if col and col in df.columns and pattern:
            return ~df[col].cast(pl.Utf8).str.contains(pattern)

    elif rule_type == "RANGE":
        if col and col in df.columns:
            min_val = params.get("min")
            max_val = params.get("max")
            series = df[col]
            mask = pl.Series("_fail", [False] * len(df))
            if min_val is not None:
                mask = mask | (series < min_val)
            if max_val is not None:
                mask = mask | (series > max_val)
            return mask

    elif rule_type == "DATE_FORMAT":
        fmt = params.get("format", "%Y-%m-%d")
        if col and col in df.columns:
            # Try parsing — null result means format mismatch
            parsed = df[col].cast(pl.Utf8).str.to_date(fmt, strict=False)
            return parsed.is_null() & df[col].is_not_null()

    elif rule_type == "DUPLICATE_CHECK":
        # Full row duplicate
        return df.is_duplicated()

    return None


def _rule_message(rule_type: str, col: str | None, params: dict) -> str:
    col_label = f"'{col}' kolonu" if col else "Satır"
    messages = {
        "NOT_NULL": f"{col_label} boş (null) olamaz",
        "UNIQUE": f"{col_label} benzersiz olmalı, tekrar eden değer var",
        "REGEX": f"{col_label} regex doğrulaması başarısız: {params.get('pattern', '')}",
        "RANGE": f"{col_label} geçerli aralık dışında [{params.get('min')}, {params.get('max')}]",
        "DATE_FORMAT": f"{col_label} tarih formatı geçersiz: {params.get('format', '')}",
        "DUPLICATE_CHECK": "Tekrar eden kayıt tespit edildi",
    }
    return messages.get(rule_type, f"Validation başarısız: {rule_type}")
