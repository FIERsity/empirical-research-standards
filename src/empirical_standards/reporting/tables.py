"""Estimator-neutral result collection and export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import pandas as pd


class StandardResult(Protocol):
    def tidy(self) -> pd.DataFrame: ...
    def glance(self) -> pd.Series: ...
    def model_spec(self) -> dict[str, Any]: ...
    def sample_info(self) -> dict[str, Any]: ...
    def provenance(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ModelCollection:
    coefficients: pd.DataFrame
    models: pd.DataFrame
    specifications: pd.DataFrame
    samples: pd.DataFrame
    provenance: pd.DataFrame


def _records(models: dict[str, StandardResult], method: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name, result in models.items():
        values = getattr(result, method)()
        rows.append({"model": name, **values})
    return pd.json_normalize(rows, sep=".")


def collect_models(models: dict[str, StandardResult]) -> ModelCollection:
    """Collect heterogeneous estimators through the shared public result contract."""
    if not models or any(not name for name in models):
        raise ValueError("models must be a non-empty mapping with non-empty names")
    coefficient_tables: list[pd.DataFrame] = []
    glance_rows: list[pd.Series] = []
    for name, result in models.items():
        table = result.tidy().copy()
        table.insert(0, "model", name)
        coefficient_tables.append(table)
        row = result.glance().copy()
        row["model"] = name
        glance_rows.append(row)
    model_table = pd.DataFrame(glance_rows).set_index("model").reset_index()
    return ModelCollection(
        coefficients=pd.concat(coefficient_tables, ignore_index=True, sort=False),
        models=model_table,
        specifications=_records(models, "model_spec"),
        samples=_records(models, "sample_info"),
        provenance=_records(models, "provenance"),
    )


def event_study_plot_data(result: StandardResult) -> pd.DataFrame:
    """Normalize event-study-like tidy results for plotting without drawing the figure."""
    table = result.tidy().copy()
    required = {"event_time", "estimate", "conf_low", "conf_high"}
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"result does not provide event-study plotting columns: {missing}")
    columns = ["event_time", "estimate", "conf_low", "conf_high"]
    optional = [
        name for name in ("std_error", "p_value", "cohorts", "treated_entities") if name in table
    ]
    return table[columns + optional].sort_values("event_time").reset_index(drop=True)


def export_model_collection(
    collection: ModelCollection,
    directory: str | Path,
    *,
    prefix: str = "models",
) -> dict[str, Path]:
    """Export CSV tables, one Excel workbook, and a compact LaTeX coefficient table."""
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    tables = {
        "coefficients": collection.coefficients,
        "models": collection.models,
        "specifications": collection.specifications,
        "samples": collection.samples,
        "provenance": collection.provenance,
    }
    paths: dict[str, Path] = {}
    for name, table in tables.items():
        path = output / f"{prefix}_{name}.csv"
        table.to_csv(path, index=False)
        paths[f"csv_{name}"] = path
    excel = output / f"{prefix}.xlsx"
    with pd.ExcelWriter(excel, engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name[:31], index=False)
    paths["excel"] = excel
    latex = output / f"{prefix}_coefficients.tex"
    latex.write_text(
        collection.coefficients.to_latex(index=False, float_format="%.6f"), encoding="utf-8"
    )
    paths["latex"] = latex
    return paths
