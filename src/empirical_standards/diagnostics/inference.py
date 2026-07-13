"""Robust resampling, influence, and multiple-testing diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from empirical_standards.causal.did import fit_did
from empirical_standards.panel.fixed_effects import PanelCovariance, fit_fixed_effects

WildWeight = Literal["rademacher", "webb"]
AdjustmentMethod = Literal["bonferroni", "holm", "fdr_bh"]


@dataclass(frozen=True)
class WildClusterBootstrapResult:
    coefficient: str
    estimate: float
    standard_error: float
    statistic: float
    bootstrap_p_value: float
    conf_low: float
    conf_high: float
    replications: int
    successful_replications: int
    weight_distribution: WildWeight


@dataclass(frozen=True)
class PermutationResult:
    observed_effect: float
    permutation_p_value: float
    null_distribution: pd.Series
    replications: int
    random_state: int | None


@dataclass(frozen=True)
class LeaveOneClusterOutResult:
    coefficient: str
    full_sample_estimate: float
    estimates: pd.DataFrame
    minimum_estimate: float
    maximum_estimate: float
    maximum_absolute_change: float


def _validate_reps(replications: int) -> None:
    if replications < 50:
        raise ValueError("replications must be at least 50")


def wild_cluster_bootstrap_fe(
    data: pd.DataFrame,
    outcome: str,
    predictors: list[str] | tuple[str, ...],
    *,
    coefficient: str,
    entity: str,
    time: str,
    cluster: str,
    entity_effects: bool = True,
    time_effects: bool = True,
    covariance: PanelCovariance = "cluster_entity",
    replications: int = 999,
    weight_distribution: WildWeight = "rademacher",
    confidence_level: float = 0.95,
    random_state: int | None = None,
) -> WildClusterBootstrapResult:
    """Run a null-imposed wild cluster bootstrap-t for one FE coefficient."""
    _validate_reps(replications)
    terms = tuple(predictors)
    if coefficient not in terms:
        raise ValueError("coefficient must be included in predictors")
    restricted_terms = tuple(term for term in terms if term != coefficient)
    if not restricted_terms:
        raise ValueError("wild bootstrap currently requires at least one restricted predictor")
    if cluster not in {entity, time}:
        raise ValueError("cluster must currently equal the entity or time column")
    if weight_distribution not in {"rademacher", "webb"}:
        raise ValueError("unsupported wild weight distribution")
    if data[[outcome, *terms, entity, time]].isna().any().any():
        raise ValueError("wild bootstrap currently requires complete model data")
    unrestricted = fit_fixed_effects(
        data,
        outcome,
        terms,
        entity=entity,
        time=time,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance=covariance,
    )
    restricted = fit_fixed_effects(
        data,
        outcome,
        restricted_terms,
        entity=entity,
        time=time,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance=covariance,
    )
    observed_estimate = float(unrestricted.coefficients[coefficient])
    observed_se = float(unrestricted.standard_errors[coefficient])
    observed_t = observed_estimate / observed_se
    raw = restricted.raw_result
    fitted_under_null = raw.fitted_values.iloc[:, 0] + raw.estimated_effects.iloc[:, 0]
    residuals = raw.resids
    indexed = data.set_index([entity, time]).sort_index()
    clusters = indexed.reset_index()[cluster].to_numpy()
    unique_clusters = pd.unique(clusters)
    rng = np.random.default_rng(random_state)
    bootstrap_t: list[float] = []
    webb_support = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
    for _ in range(replications):
        if weight_distribution == "rademacher":
            draws = rng.choice([-1.0, 1.0], size=len(unique_clusters))
        else:
            draws = rng.choice(webb_support, size=len(unique_clusters))
        weight_map = dict(zip(unique_clusters, draws, strict=True))
        weights = np.array([weight_map[value] for value in clusters])
        outcome_star = fitted_under_null.to_numpy() + residuals.to_numpy() * weights
        draw_data = indexed.reset_index()
        draw_data[outcome] = outcome_star
        try:
            draw = fit_fixed_effects(
                draw_data,
                outcome,
                terms,
                entity=entity,
                time=time,
                entity_effects=entity_effects,
                time_effects=time_effects,
                covariance=covariance,
            )
        except (ValueError, np.linalg.LinAlgError):
            continue
        draw_se = float(draw.standard_errors[coefficient])
        if draw_se > 0 and np.isfinite(draw_se):
            bootstrap_t.append(float(draw.coefficients[coefficient]) / draw_se)
    successful = len(bootstrap_t)
    if successful < max(30, int(0.8 * replications)):
        raise RuntimeError(f"only {successful} of {replications} replications were usable")
    absolute_t = np.abs(np.asarray(bootstrap_t))
    p_value = float((1 + np.sum(absolute_t >= abs(observed_t))) / (successful + 1))
    critical = float(np.quantile(absolute_t, confidence_level))
    return WildClusterBootstrapResult(
        coefficient,
        observed_estimate,
        observed_se,
        observed_t,
        p_value,
        observed_estimate - critical * observed_se,
        observed_estimate + critical * observed_se,
        replications,
        successful,
        weight_distribution,
    )


def permutation_did(
    data: pd.DataFrame,
    outcome: str,
    treated: str,
    post: str,
    *,
    entity: str,
    time: str,
    controls: list[str] | tuple[str, ...] = (),
    covariance: PanelCovariance = "cluster_entity",
    replications: int = 999,
    random_state: int | None = None,
) -> PermutationResult:
    """Permute time-invariant treatment assignment across entities and re-estimate DID."""
    _validate_reps(replications)
    if data.groupby(entity)[treated].nunique(dropna=False).max() > 1:
        raise ValueError("treated must be time-invariant within entity")
    observed = fit_did(
        data,
        outcome,
        treated,
        post,
        entity=entity,
        time=time,
        controls=controls,
        covariance=covariance,
    )
    assignments = data.drop_duplicates(entity).set_index(entity)[treated]
    if not set(assignments.unique()).issubset({0, 1}):
        raise ValueError("treated must be binary")
    rng = np.random.default_rng(random_state)
    null_effects: list[float] = []
    for _ in range(replications):
        shuffled = assignments.to_numpy().copy()
        rng.shuffle(shuffled)
        mapping = dict(zip(assignments.index, shuffled, strict=True))
        draw_data = data.copy()
        draw_data[treated] = draw_data[entity].map(mapping)
        draw = fit_did(
            draw_data,
            outcome,
            treated,
            post,
            entity=entity,
            time=time,
            controls=controls,
            covariance=covariance,
        )
        null_effects.append(draw.effect)
    null = np.asarray(null_effects)
    p_value = float((1 + np.sum(np.abs(null) >= abs(observed.effect))) / (replications + 1))
    return PermutationResult(
        observed.effect,
        p_value,
        pd.Series(null, name="permuted_effect"),
        replications,
        random_state,
    )


def leave_one_cluster_out_fe(
    data: pd.DataFrame,
    outcome: str,
    predictors: list[str] | tuple[str, ...],
    *,
    coefficient: str,
    entity: str,
    time: str,
    cluster: str,
    entity_effects: bool = True,
    time_effects: bool = True,
    covariance: PanelCovariance = "cluster_entity",
) -> LeaveOneClusterOutResult:
    """Re-estimate an FE coefficient after deleting each cluster in turn."""
    if cluster not in data:
        raise KeyError(f"cluster column {cluster!r} not found")
    clusters = list(pd.unique(data[cluster].dropna()))
    if len(clusters) < 3:
        raise ValueError("leave-one-cluster-out requires at least three clusters")
    full = fit_fixed_effects(
        data,
        outcome,
        predictors,
        entity=entity,
        time=time,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance=covariance,
    )
    if coefficient not in full.coefficients:
        raise ValueError("coefficient was not estimated")
    full_estimate = float(full.coefficients[coefficient])
    rows: list[dict[str, object]] = []
    for value in clusters:
        draw = fit_fixed_effects(
            data.loc[data[cluster] != value],
            outcome,
            predictors,
            entity=entity,
            time=time,
            entity_effects=entity_effects,
            time_effects=time_effects,
            covariance=covariance,
        )
        estimate = float(draw.coefficients[coefficient])
        rows.append(
            {
                "omitted_cluster": value,
                "estimate": estimate,
                "change": estimate - full_estimate,
                "absolute_change": abs(estimate - full_estimate),
                "nobs": draw.nobs,
            }
        )
    estimates = (
        pd.DataFrame(rows).sort_values("absolute_change", ascending=False).reset_index(drop=True)
    )
    return LeaveOneClusterOutResult(
        coefficient,
        full_estimate,
        estimates,
        float(estimates["estimate"].min()),
        float(estimates["estimate"].max()),
        float(estimates["absolute_change"].max()),
    )


def adjust_pvalues(
    p_values: pd.Series | list[float] | np.ndarray,
    *,
    method: AdjustmentMethod = "holm",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Adjust a declared family of p-values using a standard multiple-testing method."""
    if method not in {"bonferroni", "holm", "fdr_bh"}:
        raise ValueError("unsupported p-value adjustment method")
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("p_values must be a non-empty finite one-dimensional sequence")
    if ((values < 0) | (values > 1)).any():
        raise ValueError("p_values must lie between 0 and 1")
    rejected, adjusted, _, _ = multipletests(values, alpha=alpha, method=method)
    index = p_values.index if isinstance(p_values, pd.Series) else pd.RangeIndex(len(values))
    return pd.DataFrame(
        {"p_value": values, "adjusted_p_value": adjusted, "reject": rejected, "method": method},
        index=index,
    )
