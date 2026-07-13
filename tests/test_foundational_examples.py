from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("script", "required_files"),
    [
        ("ols_example.py", {"design.json", "ols_example_coefficients.csv"}),
        (
            "fixed_effects_example.py",
            {"design.json", "fixed_effects_example_coefficients.csv", "variable_variation.csv"},
        ),
        (
            "did_example.py",
            {"design.json", "did_example_coefficients.csv", "placebo_results.csv"},
        ),
    ],
)
def test_foundational_example_runs(
    tmp_path: Path, script: str, required_files: set[str]
) -> None:
    root = Path(__file__).parents[1]
    output = tmp_path / script.removesuffix(".py")
    subprocess.run(
        [sys.executable, str(root / "examples" / script), "--output", str(output)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert required_files.issubset({path.name for path in output.iterdir()})
    design = json.loads((output / "design.json").read_text(encoding="utf-8"))
    assert "claim_type" in design
    assert "primary_covariance" in design
