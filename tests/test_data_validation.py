from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.errors import MergeError

from empirical_standards.data import (
    ColumnRule,
    DataValidationReport,
    TableSchema,
    diagnose_panel,
    merge_validated,
    validate_schema,
)


def test_balanced_panel_and_variation() -> None:
    data = pd.DataFrame(
        {
            "id": np.repeat([1, 2, 3], 3),
            "year": np.tile([2020, 2021, 2022], 3),
            "time_invariant": np.repeat([10.0, 20.0, 30.0], 3),
            "common_trend": np.tile([1.0, 2.0, 3.0], 3),
            "varying": np.arange(9, dtype=float),
        }
    )
    report = diagnose_panel(
        data,
        entity="id",
        time="year",
        variables=["time_invariant", "common_trend", "varying"],
    )
    assert report.balanced
    assert report.coverage_rate == 1.0
    assert report.absorbed_by_entity == ("time_invariant",)
    assert report.absorbed_by_time == ("common_trend",)
    assert report.singleton_entities == ()


def test_unbalanced_duplicates_missing_keys_and_singletons() -> None:
    data = pd.DataFrame({"id": [1, 1, 2, 3, 3, np.nan], "year": [1, 1, 1, 1, 2, 2], "x": range(6)})
    report = diagnose_panel(data, entity="id", time="year", variables=["x"])
    assert not report.balanced
    assert report.duplicate_key_rows == 2
    assert report.missing_key_rows == 1
    assert report.singleton_entities == (2.0,)


def test_many_to_one_merge_and_unmatched_report() -> None:
    left = pd.DataFrame({"id": [1, 1, 2, 3], "year": [2020, 2021, 2020, 2020], "y": range(4)})
    right = pd.DataFrame({"id": [1, 2, 4], "region": ["a", "b", "c"]})
    result = merge_validated(left, right, on="id", relationship="many_to_one")
    assert len(result.data) == 4
    assert result.report.matched_rows == 3
    assert result.report.left_only_rows == 1
    assert result.report.right_only_rows == 1
    assert result.report.left_only_keys["id"].tolist() == [3]


def test_merge_cardinality_and_match_requirements_fail() -> None:
    left = pd.DataFrame({"id": [1, 1, 2]})
    right = pd.DataFrame({"id": [1, 2]})
    with pytest.raises(MergeError):
        merge_validated(left, right, on="id", relationship="one_to_one")
    with pytest.raises(ValueError, match="left rows"):
        merge_validated(
            pd.DataFrame({"id": [1, 3]}),
            right,
            on="id",
            relationship="one_to_one",
            require_all_left=True,
        )


def test_missing_merge_keys_fail() -> None:
    with pytest.raises(ValueError, match="must not contain missing"):
        merge_validated(
            pd.DataFrame({"id": [1, np.nan]}),
            pd.DataFrame({"id": [1]}),
            on="id",
            relationship="many_to_one",
        )


def test_schema_validation_and_exportable_report(tmp_path) -> None:
    data = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "year": [2020, 2021, 2020, 2021],
            "outcome": [1.0, 1.2, 2.0, 2.4],
            "treated": [0, 1, 0, 1],
        }
    )
    schema = TableSchema(
        "panel",
        columns=(
            ColumnRule("id", "integer"),
            ColumnRule("year", "integer", minimum=2000, maximum=2030),
            ColumnRule("outcome", "numeric"),
            ColumnRule("treated", "integer", allowed=(0, 1)),
        ),
        unique_keys=(("id", "year"),),
        allow_extra_columns=False,
    )
    schema_report = validate_schema(data, schema)
    panel_report = diagnose_panel(data, entity="id", time="year", variables=["outcome"])
    report = DataValidationReport(schema_report, panel_report)
    assert schema_report.valid and report.valid
    paths = report.export(tmp_path)
    assert all(path.exists() for path in paths.values())


def test_schema_reports_all_major_failures() -> None:
    data = pd.DataFrame(
        {
            "id": [1, 1, 1],
            "year": [1990, 1990, 2040],
            "treated": [0, 2, np.nan],
            "extra": [1, 2, 3],
        }
    )
    schema = TableSchema(
        "bad_panel",
        columns=(
            ColumnRule("id", "integer"),
            ColumnRule("year", "integer", minimum=2000, maximum=2030),
            ColumnRule("outcome", "numeric"),
            ColumnRule("treated", "integer", allowed=(0, 1)),
        ),
        unique_keys=(("id", "year"),),
        allow_extra_columns=False,
    )
    report = validate_schema(data, schema)
    assert not report.valid
    assert set(report.issues["rule"]) == {
        "required_column",
        "extra_columns",
        "minimum",
        "maximum",
        "non_nullable",
        "allowed_values",
        "unique_key",
    }
