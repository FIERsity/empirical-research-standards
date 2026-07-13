# Panel IV and Anderson-Rubin inference

`fit_panel_iv_2sls` adds entity and/or time fixed effects to the explicit 2SLS interface. The
default `absorption="indicators"` backend creates reference-category indicators and includes
them in both stages. It is algebraically exact and gives transparent finite-sample degrees of
freedom. `absorption="within"` uses `pyhdfe` to residualize the outcome, exogenous variables,
endogenous variables, and instruments with the identical high-dimensional projection before
2SLS. Its structural coefficients are tested against the indicator backend.

The scalable within backend deliberately uses asymptotic covariance (`debiased=False`) because
ordinary regressor-count corrections do not account correctly for absorbed fixed-effect
degrees. Metadata records this convention and the absorbed degrees. A future release must
add and externally benchmark finite-sample corrections before offering them for this backend.

Panel keys must be complete and unique. Entity clustering is the default when clustered
covariance is selected without an explicit cluster column. Public coefficient tables hide the
internal indicator coefficients, while model metadata records the implementation and number
of absorbed indicators.

`anderson_rubin_test` tests one endogenous coefficient by subtracting its hypothesized value
from the outcome and jointly testing the excluded instruments in the resulting reduced-form
regression. It supports exogenous controls, categorical fixed effects, HC1 covariance, and
one-way clustering. Unlike the usual 2SLS t-test, its size does not rely on strong first-stage
identification under the standard AR assumptions.

`anderson_rubin_confidence_set` inverts the test over a user-supplied increasing grid. The full
accepted grid is retained because weak-identification-robust confidence sets can be
disconnected or unbounded. `lower_bound` and `upper_bound` are only the envelope of accepted
grid points; the `bounded_below` and `bounded_above` flags indicate whether the accepted set
reaches a grid edge. A wider grid and finer spacing are required before reporting endpoints.

The current AR implementation covers one endogenous regressor. The package provides sample-rank
and homoskedastic conditional relevance diagnostics for multiple endogenous regressors, but
robust conditional tests and Kleibergen-Paap procedures remain future work.

`summarize_first_stage` distinguishes conventional partial F statistics from robust excluded-
instrument Wald statistics using the stored reference distribution. It reports Wald divided
by the number of excluded instruments as a descriptive normalization but sets
`is_kleibergen_paap=False`; this quantity is not a substitute for the KP rk statistic.
