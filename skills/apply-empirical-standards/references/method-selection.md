# Method selection

Choose from the research design, not from the coefficient or p-value. Read
`docs/model_selection.md` for the full decision sequence and stop conditions, then read the
linked method document before fitting the selected model.

| Research structure | Entry point | Required design checks | Method document |
|---|---|---|---|
| Cross-sectional or pooled conditional association | `fit_ols` | Functional form, leverage, dependence, covariance choice | `docs/ols.md` |
| Repeated entities with time-invariant confounding | `fit_fixed_effects` | Within variation, duplicate keys, FE dimensions, cluster level | `docs/panel_and_did.md` |
| One treatment group and common post period | `fit_did` | Treatment timing, no anticipation, parallel trends, cluster level | `docs/panel_and_did.md` |
| Dynamic effects under a TWFE design | `fit_event_study` | Reference period, support by event time, pre-period joint test, heterogeneous-timing risk | `docs/panel_and_did.md` |
| Staggered adoption with cohort-time comparisons | `fit_staggered_did_r` | Never/not-yet-treated controls, cohort support, anticipation, score method | `docs/staggered_did_audit.md` |
| Cohort-interacted staggered event study | `fit_sun_abraham_r` | Cohort support, reference periods, aggregation weights, comparison group | `docs/staggered_did_audit.md` |
| Endogenous regressor with excluded instruments | `fit_iv_2sls` | Relevance, exclusion, independence, first stage, overidentification limits | `docs/iv.md` |
| IV with entity and/or time fixed effects | `fit_panel_iv_2sls` | All IV checks plus within variation, absorbed dimensions, cluster level | `docs/panel_iv_and_ar.md` |

Use the explicit R-backed paths for consequential work. The unsuffixed Python variants are
educational references and are not numerical substitutes for `did` or `fixest`. Backend maturity
does not establish that identifying assumptions fit the data.

## Covariance selection

- Use classical covariance only when homoskedastic independent errors are defensible.
- Use heteroskedasticity-robust covariance for independent observations with unknown variance.
- Cluster at the level of treatment assignment or residual dependence justified by the design.
- Use two-way clustering only when both dimensions represent credible dependence; do not add it
  mechanically.
- Treat few-cluster settings as an inference problem. Consider wild cluster bootstrap,
  permutation inference, and sensitivity to influential clusters where supported.

## Causal-design guardrails

- Fixed effects remove only confounding constant within an absorbed group.
- A DID coefficient is causal only under its design assumptions, not because unit and time fixed
  effects are present.
- In staggered settings, report cohort and event-time support and prefer estimators designed for
  treatment-effect heterogeneity over an unexamined TWFE average.
- Instruments require a substantive exclusion argument. First-stage strength alone is
  insufficient.
- Robustness checks expose sensitivity; they do not repair invalid assignment, instruments, or
  comparisons.
