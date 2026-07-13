from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_event_study, fit_fixed_effects, fit_ols
from empirical_standards.reporting import (
    collect_models,
    event_study_plot_data,
    export_model_collection,
)


def test_collection_and_exports(tmp_path: Path) -> None:
    rng = np.random.default_rng(5)
    entity = np.repeat(np.arange(20), 5)
    time = np.tile(np.arange(5), 20)
    x = rng.normal(size=len(entity))
    y = rng.normal(size=20)[entity] + 0.2 * time + 1.2 * x + rng.normal(scale=0.1, size=len(entity))
    data = pd.DataFrame({"id": entity, "time": time, "x": x, "y": y})
    models = {
        "ols": fit_ols(data, "y", ["x"]),
        "twfe": fit_fixed_effects(data, "y", ["x"], entity="id", time="time", time_effects=True),
    }
    collection = collect_models(models)
    assert set(collection.coefficients["model"]) == {"ols", "twfe"}
    assert set(collection.models["model"]) == {"ols", "twfe"}
    assert "settings.covariance" in collection.specifications
    paths = export_model_collection(collection, tmp_path, prefix="test")
    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    assert set(pd.ExcelFile(paths["excel"]).sheet_names) == {
        "coefficients",
        "models",
        "specifications",
        "samples",
        "provenance",
    }


def test_event_plot_data() -> None:
    rng = np.random.default_rng(9)
    entity = np.repeat(np.arange(30), 6)
    time = np.tile(np.arange(6), 30)
    adoption = np.where(entity < 15, 3.0, np.nan)
    y = (
        rng.normal(size=30)[entity]
        + 0.1 * time
        + 1.0 * (time >= adoption)
        + rng.normal(scale=0.1, size=len(entity))
    )
    data = pd.DataFrame({"id": entity, "time": time, "adoption": adoption, "y": y})
    result = fit_event_study(data, "y", "adoption", entity="id", time="time", window=(-2, 2))
    plot_data = event_study_plot_data(result)
    assert list(plot_data["event_time"]) == [-2, 0, 1, 2]
