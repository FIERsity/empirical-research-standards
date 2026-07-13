from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from empirical_standards import diagnose_iv_relevance, fit_iv_2sls, summarize_first_stage


def make_iv_data(strength: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(714)
    n = 1500
    z1, z2, x = rng.normal(size=(3, n))
    structural_error = rng.normal(size=n)
    endogenous_noise = 0.7 * structural_error + rng.normal(size=n)
    endogenous = strength * z1 + 0.6 * strength * z2 + 0.4 * x + endogenous_noise
    y = 1.0 + 0.8 * x + 2.0 * endogenous + structural_error
    cluster = np.repeat(np.arange(75), 20)
    return pd.DataFrame(
        {"y": y, "x": x, "endogenous": endogenous, "z1": z1, "z2": z2, "cluster": cluster}
    )


def test_iv_recovers_effect_and_diagnostics() -> None:
    result = fit_iv_2sls(
        make_iv_data(), "y", exogenous=["x"], endogenous=["endogenous"], instruments=["z1", "z2"]
    )
    assert result.coefficients["endogenous"] == pytest.approx(2.0, abs=0.08)
    assert result.first_stage.loc[0, "partial_r_squared"] > 0.3
    assert result.first_stage.loc[0, "excluded_instruments_statistic"] > 100
    assert result.wu_hausman_p_value < 0.05
    assert np.isfinite(result.sargan_statistic)
    assert np.isfinite(result.robust_overidentification_statistic)
    assert result.model_spec()["settings"]["robust_overidentification_test"] == "Wooldridge score"


def test_weak_instruments_are_visible() -> None:
    strong = fit_iv_2sls(
        make_iv_data(1.0), "y", exogenous=["x"], endogenous=["endogenous"], instruments=["z1", "z2"]
    )
    weak = fit_iv_2sls(
        make_iv_data(0.02),
        "y",
        exogenous=["x"],
        endogenous=["endogenous"],
        instruments=["z1", "z2"],
    )
    assert (
        weak.first_stage.loc[0, "partial_r_squared"]
        < strong.first_stage.loc[0, "partial_r_squared"]
    )
    assert (
        weak.first_stage.loc[0, "excluded_instruments_statistic"]
        < strong.first_stage.loc[0, "excluded_instruments_statistic"]
    )
    summary = summarize_first_stage(strong)
    assert summary.loc[0, "statistic_kind"] == "robust_excluded_instrument_Wald"
    assert not bool(summary.loc[0, "is_kleibergen_paap"])
    assert summary.loc[0, "wald_per_excluded_instrument"] == pytest.approx(
        summary.loc[0, "excluded_instruments_statistic"] / 2
    )


def test_clustered_iv_and_tidy_contract() -> None:
    result = fit_iv_2sls(
        make_iv_data(),
        "y",
        exogenous=["x"],
        endogenous=["endogenous"],
        instruments=["z1", "z2"],
        covariance="cluster",
        cluster="cluster",
    )
    assert result.covariance == "cluster"
    assert list(result.tidy()["term"]) == ["const", "x", "endogenous"]
    assert result.glance()["estimator"] == "iv_2sls"
    assert result.sample_info()["estimation_nobs"] == 1500


def test_iv_validation() -> None:
    data = make_iv_data()
    with pytest.raises(ValueError, match="underidentified"):
        fit_iv_2sls(
            data.assign(e2=data["endogenous"] + 1),
            "y",
            exogenous=["x"],
            endogenous=["endogenous", "e2"],
            instruments=["z1"],
        )


def test_conditional_relevance_matches_single_endogenous_first_stage() -> None:
    data = make_iv_data()
    diagnostics = diagnose_iv_relevance(
        data, exogenous=["x"], endogenous=["endogenous"], instruments=["z1", "z2"]
    )
    direct = fit_iv_2sls(
        data,
        "y",
        exogenous=["x"],
        endogenous=["endogenous"],
        instruments=["z1", "z2"],
        covariance="unadjusted",
    )
    row = diagnostics.conditional_tests.iloc[0]
    assert row["conditional_f_statistic"] == pytest.approx(
        direct.first_stage.loc[0, "excluded_instruments_statistic"]
    )
    assert diagnostics.rank_condition_satisfied
    assert diagnostics.summary()["required_rank"] == 1


def test_multi_endogenous_conditional_relevance_exposes_weak_direction() -> None:
    rng = np.random.default_rng(917)
    n = 1000
    x, z1, z2, noise1, noise2 = rng.normal(size=(5, n))
    data = pd.DataFrame(
        {
            "x": x,
            "z1": z1,
            "z2": z2,
            "e1": z1 + 0.2 * x + noise1,
            "e2": 0.02 * z2 + 0.2 * x + noise2,
        }
    )
    diagnostics = diagnose_iv_relevance(
        data, exogenous=["x"], endogenous=["e1", "e2"], instruments=["z1", "z2"]
    )
    table = diagnostics.conditional_tests.set_index("endogenous")
    assert table.loc["e1", "conditional_f_statistic"] > 100
    assert table.loc["e2", "conditional_f_statistic"] < 5
    assert diagnostics.cross_moment_rank == 2
    assert diagnostics.rank_condition_satisfied


def test_iv_relevance_validation() -> None:
    data = make_iv_data()
    with pytest.raises(ValueError, match="at least as many instruments"):
        diagnose_iv_relevance(
            data.assign(e2=data["endogenous"] + 1),
            exogenous=["x"],
            endogenous=["endogenous", "e2"],
            instruments=["z1"],
        )
    with pytest.raises(ValueError, match="rank deficient"):
        diagnose_iv_relevance(
            data.assign(z_duplicate=data["z1"]),
            exogenous=["x"],
            endogenous=["endogenous"],
            instruments=["z1", "z_duplicate"],
        )
    with pytest.raises(ValueError, match="must not overlap"):
        fit_iv_2sls(data, "y", exogenous=["x"], endogenous=["endogenous"], instruments=["x"])
    with pytest.raises(ValueError, match="cluster is required"):
        fit_iv_2sls(
            data,
            "y",
            exogenous=["x"],
            endogenous=["endogenous"],
            instruments=["z1"],
            covariance="cluster",
        )
