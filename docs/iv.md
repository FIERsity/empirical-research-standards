# Instrumental variables and two-stage least squares

`fit_iv_2sls` requires explicit lists of exogenous regressors, endogenous regressors, and
excluded instruments. An intercept is included by default. The function rejects overlapping
variable roles, underidentification by instrument count, non-numeric or non-finite data, and
implicit missing-value deletion.

The first-stage table reports ordinary, partial, and Shea partial R-squared plus the excluded-
instrument statistic, p-value, and its actual reference distribution. With robust covariance
the statistic is commonly a chi-squared Wald statistic, not the homoskedastic first-stage F;
researchers must not apply an F=10 rule without checking that distinction. A large statistic
alone also does not settle weak-instrument concerns with multiple endogenous regressors or
nonstandard clustering.

`diagnose_iv_relevance` adds transparent multi-endogenous-variable diagnostics. For each
endogenous regressor it tests the excluded instruments after conditioning on exogenous
regressors and the other endogenous regressors. `covariance="unadjusted"` reports the
homoskedastic conditional F with its F reference degrees of freedom. `covariance="robust"`
and `covariance="cluster"` report HC1 or one-way clustered joint Wald statistics with a
chi-squared reference distribution; clustering requires an explicit column and at least two
groups. Every option reports conditional partial R-squared. It also reports the
sample rank of the residualized instrument-endogenous cross moment and normalized singular
values. These are sample relevance diagnostics: they are not Kleibergen-Paap statistics, do
not supply weak-instrument critical values, and do not establish instrument exclusion.

The result reports Wu-Hausman exogeneity, homoskedastic Sargan, and robust Wooldridge score
overidentification tests. Sargan and Wooldridge tests are unavailable in exactly identified
models and appear as invalid/NaN rather than fabricated zeros. The robust score test is named
explicitly and is not mislabeled as a Hansen J statistic.

Covariance choices are unadjusted, heteroskedasticity robust, and one-way clustered. Exclusion
validity remains a substantive identification assumption: neither first-stage strength nor an
overidentification p-value proves that an instrument affects the outcome only through the
endogenous regressor.

The deterministic benchmark compares Python `linearmodels` against R `fixest` for 2SLS
coefficients and homoskedastic standard errors. Panel IV is public but remains an advanced,
restricted component; see `docs/panel_iv_and_ar.md`.
