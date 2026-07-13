"""Exportable composition of schema, merge, and panel validation evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from empirical_standards.data.merge import MergeReport
from empirical_standards.data.panel import PanelDiagnostics
from empirical_standards.data.schema import SchemaValidationReport


@dataclass(frozen=True)
class DataValidationReport:
    schema: SchemaValidationReport
    panel: PanelDiagnostics | None = None
    merge: MergeReport | None = None

    @property
    def valid(self) -> bool:
        panel_valid = self.panel is None or (
            self.panel.duplicate_key_rows == 0 and self.panel.missing_key_rows == 0
        )
        return self.schema.valid and panel_valid

    def export(self, directory: str | Path, *, prefix: str = "data_validation") -> dict[str, Path]:
        output = Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        paths: dict[str, Path] = {}
        tables = {
            "schema_issues": self.schema.issues,
            "schema_columns": self.schema.column_summary,
        }
        if self.panel is not None:
            tables["panel_summary"] = self.panel.summary().rename("value").reset_index()
            tables["panel_time_coverage"] = self.panel.time_coverage
            tables["panel_variable_variation"] = self.panel.variable_variation
        if self.merge is not None:
            tables["merge_left_only_keys"] = self.merge.left_only_keys
            tables["merge_right_only_keys"] = self.merge.right_only_keys
        for name, table in tables.items():
            path = output / f"{prefix}_{name}.csv"
            table.to_csv(path, index=False)
            paths[name] = path
        summary: dict[str, object] = {
            "valid": self.valid,
            "schema": self.schema.summary().to_dict(),
            "panel": self.panel.summary().to_dict() if self.panel is not None else None,
            "merge": (
                {
                    key: value
                    for key, value in asdict(self.merge).items()
                    if key not in {"left_only_keys", "right_only_keys"}
                }
                if self.merge is not None
                else None
            ),
            "files": sorted(path.name for path in paths.values()),
        }
        summary_path = output / f"{prefix}_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        paths["summary"] = summary_path
        return paths
