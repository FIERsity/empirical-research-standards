"""Small shared contracts for model specifications, samples, and provenance."""

from __future__ import annotations

import hashlib
import platform
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ModelSpec:
    estimator: str
    outcome: str
    predictors: tuple[str, ...]
    settings: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SampleInfo:
    original_nobs: int
    estimation_nobs: int
    dropped_nobs: int
    columns: tuple[str, ...]
    data_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Provenance:
    python_version: str
    platform: str
    package_versions: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelMetadata:
    spec: ModelSpec
    sample: SampleInfo
    provenance: Provenance


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def _fingerprint(data: pd.DataFrame) -> str:
    """Hash values, index, column names, and dtypes in deterministic row order."""
    digest = hashlib.sha256()
    digest.update("\x1f".join(map(str, data.columns)).encode())
    digest.update("\x1f".join(map(str, data.dtypes)).encode())
    digest.update(pd.util.hash_pandas_object(data, index=True).to_numpy().tobytes())
    return f"sha256:{digest.hexdigest()}"


def build_metadata(
    *,
    estimator: str,
    outcome: str,
    predictors: tuple[str, ...],
    settings: dict[str, Any],
    sample: pd.DataFrame,
    original_nobs: int,
) -> ModelMetadata:
    """Build metadata from the exact ordered estimation sample."""
    return ModelMetadata(
        spec=ModelSpec(estimator, outcome, predictors, settings),
        sample=SampleInfo(
            original_nobs=original_nobs,
            estimation_nobs=len(sample),
            dropped_nobs=original_nobs - len(sample),
            columns=tuple(map(str, sample.columns)),
            data_fingerprint=_fingerprint(sample),
        ),
        provenance=Provenance(
            python_version=platform.python_version(),
            platform=platform.platform(),
            package_versions={
                name: _package_version(name)
                for name in (
                    "empirical-standards",
                    "numpy",
                    "pandas",
                    "statsmodels",
                    "linearmodels",
                )
            },
        ),
    )
