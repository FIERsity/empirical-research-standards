"""Explicit subprocess bridge for versioned R estimator scripts."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class RBackendEnvironment:
    available: bool
    rscript: str | None
    r_version: str | None
    packages: dict[str, str | None]


def check_r_environment(packages: tuple[str, ...]) -> RBackendEnvironment:
    executable = shutil.which("Rscript")
    if executable is None:
        return RBackendEnvironment(False, None, None, {package: None for package in packages})
    expression = (
        "cat(R.version.string, '\\n'); "
        f"for (p in c({','.join(repr(package) for package in packages)})) "
        "cat(p, if(requireNamespace(p, quietly=TRUE)) as.character(packageVersion(p)) "
        "else 'NOT_INSTALLED', '\\n')"
    )
    completed = subprocess.run(
        [executable, "-e", expression], check=True, capture_output=True, text=True
    )
    lines = completed.stdout.strip().splitlines()
    versions: dict[str, str | None] = {}
    for line in lines[1:]:
        package, version = line.split(maxsplit=1)
        version = version.strip()
        versions[package] = None if version == "NOT_INSTALLED" else version
    return RBackendEnvironment(
        all(versions.get(package) is not None for package in packages),
        executable,
        lines[0].strip(),
        versions,
    )


def run_r_backend(
    data: pd.DataFrame,
    specification: dict[str, object],
    *,
    script: str | Path,
    required_packages: tuple[str, ...],
) -> tuple[dict[str, object], dict[str, pd.DataFrame]]:
    """Run one declared R script with frozen CSV/JSON inputs and structured outputs."""
    environment = check_r_environment(required_packages)
    if not environment.available or environment.rscript is None:
        missing = [name for name, version in environment.packages.items() if version is None]
        raise RuntimeError(f"R backend unavailable; missing R packages: {missing}")
    script_path = Path(script).resolve()
    if not script_path.is_file():
        raise FileNotFoundError(f"R backend script not found: {script_path}")
    with tempfile.TemporaryDirectory(prefix="empirical-standards-r-") as temporary:
        directory = Path(temporary)
        input_path = directory / "input.csv"
        spec_path = directory / "specification.json"
        output_path = directory / "output"
        output_path.mkdir()
        data.to_csv(input_path, index=False)
        spec_path.write_text(json.dumps(specification, indent=2), encoding="utf-8")
        completed = subprocess.run(
            [
                environment.rscript,
                str(script_path),
                str(input_path),
                str(spec_path),
                str(output_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"R backend failed: {message}")
        metadata = json.loads((output_path / "result.json").read_text(encoding="utf-8"))
        metadata["r_version"] = environment.r_version
        metadata["package_versions"] = environment.packages
        metadata["script"] = str(script_path)
        tables = {
            path.stem: pd.read_csv(path)
            for path in sorted(output_path.glob("*.csv"))
        }
        return metadata, tables
