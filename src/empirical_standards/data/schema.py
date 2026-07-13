"""Explicit, dataframe-native table schema validation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

ColumnKind = Literal["numeric", "integer", "string", "boolean", "datetime"]


@dataclass(frozen=True)
class ColumnRule:
    name: str
    kind: ColumnKind
    nullable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    allowed: tuple[object, ...] | None = None


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[ColumnRule, ...]
    unique_keys: tuple[tuple[str, ...], ...] = ()
    allow_extra_columns: bool = True


@dataclass(frozen=True)
class SchemaValidationReport:
    schema_name: str
    valid: bool
    rows: int
    columns: int
    issues: pd.DataFrame
    column_summary: pd.DataFrame

    def summary(self) -> pd.Series:
        errors = int((self.issues["severity"] == "error").sum()) if not self.issues.empty else 0
        warnings = (
            int((self.issues["severity"] == "warning").sum()) if not self.issues.empty else 0
        )
        return pd.Series(
            {
                "schema": self.schema_name,
                "valid": self.valid,
                "rows": self.rows,
                "columns": self.columns,
                "errors": errors,
                "warnings": warnings,
            }
        )


def _kind_matches(series: pd.Series, kind: ColumnKind) -> bool:
    if kind == "numeric":
        return bool(pd.api.types.is_numeric_dtype(series))
    if kind == "integer":
        non_missing = series.dropna()
        return bool(
            pd.api.types.is_integer_dtype(series)
            or (
                pd.api.types.is_numeric_dtype(series)
                and np.isclose(non_missing.astype(float) % 1, 0).all()
            )
        )
    if kind == "string":
        return bool(pd.api.types.is_string_dtype(series) or series.dtype == object)
    if kind == "boolean":
        return bool(pd.api.types.is_bool_dtype(series))
    return bool(pd.api.types.is_datetime64_any_dtype(series))


def validate_schema(
    data: pd.DataFrame, schema: TableSchema, *, sample_size: int = 5
) -> SchemaValidationReport:
    """Validate required columns, kinds, missingness, domains, ranges, and unique keys."""
    if sample_size < 0:
        raise ValueError("sample_size must be non-negative")
    names = [rule.name for rule in schema.columns]
    if len(names) != len(set(names)):
        raise ValueError("schema column names must be unique")
    issues: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    def add_issue(rule: str, column: str, count: int, samples: Sequence[object]) -> None:
        issues.append(
            {
                "severity": "error",
                "rule": rule,
                "column": column,
                "count": count,
                "sample_values": list(samples),
            }
        )

    missing_columns = [name for name in names if name not in data]
    for name in missing_columns:
        add_issue("required_column", name, len(data), [])
    extra = [name for name in data.columns if name not in names]
    if extra and not schema.allow_extra_columns:
        add_issue("extra_columns", "", len(extra), extra[:sample_size])

    for rule in schema.columns:
        if rule.name not in data:
            continue
        series = data[rule.name]
        missing = int(series.isna().sum())
        summaries.append(
            {
                "column": rule.name,
                "expected_kind": rule.kind,
                "actual_dtype": str(series.dtype),
                "rows": len(series),
                "missing": missing,
                "unique": int(series.nunique(dropna=True)),
            }
        )
        if not _kind_matches(series, rule.kind):
            add_issue("column_kind", rule.name, len(series) - missing, [str(series.dtype)])
            continue
        if missing and not rule.nullable:
            add_issue("non_nullable", rule.name, missing, [])
        non_missing = series.dropna()
        if rule.allowed is not None:
            invalid = non_missing.loc[~non_missing.isin(rule.allowed)]
            if len(invalid):
                add_issue(
                    "allowed_values",
                    rule.name,
                    len(invalid),
                    invalid.drop_duplicates().head(sample_size).tolist(),
                )
        if rule.minimum is not None and pd.api.types.is_numeric_dtype(non_missing):
            invalid = non_missing.loc[non_missing < rule.minimum]
            if len(invalid):
                add_issue("minimum", rule.name, len(invalid), invalid.head(sample_size).tolist())
        if rule.maximum is not None and pd.api.types.is_numeric_dtype(non_missing):
            invalid = non_missing.loc[non_missing > rule.maximum]
            if len(invalid):
                add_issue("maximum", rule.name, len(invalid), invalid.head(sample_size).tolist())

    for keys in schema.unique_keys:
        absent = [key for key in keys if key not in data]
        if absent:
            raise ValueError(f"unique key columns are absent from data: {absent}")
        duplicate = data.duplicated(list(keys), keep=False)
        if duplicate.any():
            samples = data.loc[duplicate, list(keys)].drop_duplicates().head(sample_size)
            add_issue(
                "unique_key",
                ",".join(keys),
                int(duplicate.sum()),
                samples.to_dict("records"),
            )

    issue_table = pd.DataFrame(
        issues, columns=["severity", "rule", "column", "count", "sample_values"]
    )
    return SchemaValidationReport(
        schema.name,
        issue_table.empty,
        len(data),
        len(data.columns),
        issue_table,
        pd.DataFrame(summaries),
    )
