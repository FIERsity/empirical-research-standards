from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_research_workflow_runs_and_exports_audit_trail(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "examples" / "research_workflow.py"),
            "--output",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = json.loads((tmp_path / "workflow_manifest.json").read_text(encoding="utf-8"))
    assert manifest["original_nobs"] == manifest["estimation_nobs"] == 800
    assert manifest["primary_covariance"] == "cluster_entity"
    assert "parallel_trends" in manifest
    assert "common-adoption DID" in completed.stdout
    required = {
        "research_workflow_coefficients.csv",
        "research_workflow_models.csv",
        "research_workflow_specifications.csv",
        "research_workflow_samples.csv",
        "research_workflow_provenance.csv",
        "panel_diagnostics.csv",
        "covariance_sensitivity.csv",
        "placebo_results.csv",
        "heterogeneity_results.csv",
    }
    assert required.issubset({path.name for path in tmp_path.iterdir()})
