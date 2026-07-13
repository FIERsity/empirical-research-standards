from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "apply-empirical-standards"


def test_skill_metadata_and_linked_resources() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", maxsplit=2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata.keys() == {"name", "description"}
    assert metadata["name"] == SKILL.name
    assert "OLS" in metadata["description"]
    assert "DID" in metadata["description"]
    assert "IV" in metadata["description"]

    for relative_path in (
        "references/method-selection.md",
        "references/api-patterns.md",
        "references/output-checklist.md",
    ):
        assert f"({relative_path})" in body
        assert (SKILL / relative_path).is_file()

    agent_metadata = yaml.safe_load(
        (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    assert "$apply-empirical-standards" in agent_metadata["interface"]["default_prompt"]


def test_skill_environment_check_runs() -> None:
    completed = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "check_environment.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "required APIs: OK (11)" in completed.stdout


def test_model_selection_guide_covers_design_paths_and_stop_conditions() -> None:
    guide = (ROOT / "docs" / "model_selection.md").read_text(encoding="utf-8")
    for required in (
        "fit_ols",
        "fit_fixed_effects",
        "fit_did",
        "fit_staggered_did",
        "fit_iv_2sls",
        "Stop conditions",
        "停止",
    ):
        assert required in guide


def test_backend_policy_is_explicit_and_bilingual() -> None:
    policy = (ROOT / "docs" / "backend_policy.md").read_text(encoding="utf-8")
    for required in (
        "Python-first, not Python-only",
        "Switch to R immediately",
        "Backend selection must never be silent",
        "不是 Python-only",
    ):
        assert required in policy
