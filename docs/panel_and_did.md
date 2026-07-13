# Panel fixed effects and difference-in-differences

## Functional organization

- `panel.fit_fixed_effects`: one-way entity FE, one-way time FE, or two-way FE.
- `causal.fit_did`: treated-by-post TWFE DID with optional declared controls.
- `causal.fit_event_study`: dynamic TWFE event-time coefficients and a joint pre-trend Wald test.
- `causal.fit_staggered_did`: cohort-time ATT using never-treated or not-yet-treated controls.
- `diagnostics`: pre-specified subgroup estimation, covariance sensitivity, and placebo timing.

## Fixed effects and inference

Panel keys must be unique. Effects are absorbed by `linearmodels.PanelOLS`; they are not
silently added as reported coefficients. Covariance choices are `unadjusted`, `robust`,
`cluster_entity`, `cluster_time`, and `cluster_two_way`. Entity-clustered inference is the
default because serial dependence within a panel unit is common, but it remains explicit in
the result metadata.

## DID and event studies

`fit_did` estimates a treated-by-post interaction with entity and time fixed effects. It does
not test parallel trends by itself. `fit_event_study` omits the declared reference event time
(default -1), reports dynamic coefficients, and jointly tests the remaining pre-treatment
coefficients. Event times outside the requested window are binned into its lower or upper
endpoint so they are not silently treated as the reference category. Never-treated
observations are represented by missing `treatment_time`.

TWFE event studies can be contaminated under heterogeneous staggered treatment effects. Use
them as descriptive diagnostics in that setting, not as a substitute for cohort-time ATT.

## Staggered adoption

`fit_staggered_did` compares each treated cohort's outcome change from its last untreated
period with the same change among eligible controls. `not_yet_treated` is the default;
`never_treated` is available when a stable never-treated group exists. The estimator reports
group-time, event-time, cohort, calendar-time, and overall ATT. Setting `bootstrap_reps` to at
least 50 enables entity-cluster bootstrap standard errors, pointwise confidence intervals,
and max-studentized simultaneous confidence bands. Use substantially more replications
(normally 999 or more) for final analysis and set `random_state` for reproducibility.

The bootstrap resamples whole entities, assigns synthetic identifiers when an entity is
drawn repeatedly, and records requested and usable replication counts. A run fails rather
than silently reporting unstable inference if fewer than 30 or 80 percent of draws are
usable. The current implementation requires a balanced panel and does not yet provide
influence-function or doubly robust covariate-adjusted inference.

Because this cohort-time estimator is currently unconditional, time-varying confounders
must not simply be ignored. Either justify unconditional parallel trends, use a pre-specified
valid adjustment before estimation, or wait for the planned doubly robust covariate-adjusted
estimator.

## Heterogeneity and robustness

Subgroup estimates require a pre-specified, time-invariant entity group and retain the same
model specification in each subgroup. Differences between subgroup point estimates are not
automatically evidence that subgroup effects differ; a formal interaction test is still
needed. Covariance sensitivity changes inference, not the estimand. Placebo dates should be
chosen from genuinely untreated periods and interpreted alongside the event-study pre-trend
test.
