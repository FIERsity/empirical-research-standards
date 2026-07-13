# API patterns

Run these patterns only after mapping names to the actual research design. The package method
documents remain authoritative for arguments and limitations.

## Data audit

```python
from empirical_standards.data import ColumnRule, TableSchema, diagnose_panel, merge_validated, validate_schema

schema = TableSchema(
    "panel",
    columns=(ColumnRule("city", "string"), ColumnRule("year", "integer")),
    unique_keys=(("city", "year"),),
)
schema_report = validate_schema(panel, schema)

merged = merge_validated(left, right, on=["city"], relationship="many_to_one")
panel = diagnose_panel(
    merged.data,
    entity="city",
    time="year",
    variables=["outcome", "treatment"],
)
print(merged.report)
print(panel.summary())
```

## OLS and fixed effects

```python
from empirical_standards import fit_fixed_effects, fit_ols

ols = fit_ols(
    data,
    outcome="y",
    predictors=["treatment", "control"],
    covariance="cluster",
    cluster="region",
)
fe = fit_fixed_effects(
    data,
    outcome="y",
    predictors=["treatment", "control"],
    entity="city",
    time="year",
    time_effects=True,
    covariance="cluster_two_way",
)
```

## DID families

```python
from empirical_standards import fit_did, fit_event_study, fit_staggered_did, fit_sun_abraham

did = fit_did(
    data, "y", "treated", "post",
    entity="city", time="year", controls=["control"],
    covariance="cluster_entity",
)
event = fit_event_study(
    data, "y", "treatment_year",
    entity="city", time="year", reference=-1,
)
staggered = fit_staggered_did(
    data, "y", "treatment_year",
    entity="city", time="year",
)
sun_abraham = fit_sun_abraham(
    data, "y", "treatment_year",
    entity="city", time="year", reference=-1,
)
```

Confirm signatures against the installed version. Treatment-cohort encoding, comparison-group
rules, event windows, covariance options, and bootstrap arguments are consequential settings.

## IV and weak-identification-robust inference

```python
from empirical_standards import (
    anderson_rubin_confidence_set,
    anderson_rubin_test,
    diagnose_iv_relevance,
    fit_iv_2sls,
    fit_panel_iv_2sls,
    summarize_first_stage,
)

iv = fit_iv_2sls(
    data, "y",
    exogenous=["control"],
    endogenous=["treatment"],
    instruments=["instrument"],
    covariance="cluster",
    cluster="region",
)
print(summarize_first_stage(iv))
relevance = diagnose_iv_relevance(
    data,
    exogenous=["control"],
    endogenous=["treatment"],
    instruments=["instrument"],
    covariance="cluster",
    cluster="region",
)
print(relevance.conditional_tests)

panel_iv = fit_panel_iv_2sls(
    data, "y",
    exogenous=["control"], endogenous=["treatment"], instruments=["instrument"],
    entity="city", time="year", entity_effects=True, time_effects=True,
    covariance="cluster", absorption="within",
)
# For homoskedastic covariance only, opt into the externally verified absorbed-DF correction:
# covariance="unadjusted", within_covariance_correction="absorbed_df"
ar = anderson_rubin_test(
    data, "y", endogenous="treatment", instruments=["instrument"],
    null=0.0, controls=["control"], entity="city", time="year",
)
confidence_set = anderson_rubin_confidence_set(
    data, "y", endogenous="treatment", instruments=["instrument"],
    grid=[-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
    controls=["control"], entity="city", time="year",
)
```

## Diagnostics and exports

```python
from empirical_standards.diagnostics import (
    adjust_pvalues,
    covariance_sensitivity,
    fit_fe_heterogeneity,
    leave_one_cluster_out_fe,
    permutation_did,
    placebo_did,
    wild_cluster_bootstrap_fe,
)
from empirical_standards.reporting import collect_models, export_model_collection

collection = collect_models({"baseline": ols, "fixed_effects": fe, "did": did})
export_model_collection(collection, "outputs", prefix="main_results")
```

Read `docs/robust_inference.md` and `docs/reporting.md` before using these utilities. Do not run
every diagnostic mechanically; select checks whose resampling unit, null, and comparison match
the design.
