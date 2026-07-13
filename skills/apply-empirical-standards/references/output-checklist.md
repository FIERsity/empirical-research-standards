# Output checklist

Before presenting an empirical result, retain or report:

- data source, construction date, unit of observation, and exact estimation-sample fingerprint;
- original observations, used observations, dropped observations, entities, periods, and clusters;
- outcome, treatment or endogenous regressors, controls, instruments, fixed effects, and variable
  order;
- intercept rule, reference category or event period, sample restrictions, and missing-data rule;
- estimator, covariance method, clustering dimensions, finite-sample convention, confidence level,
  and bootstrap or permutation seed and replications;
- coefficient, standard error, test statistic, reference distribution, p-value, confidence interval,
  and fit statistics appropriate to the estimator;
- diagnostic and placebo results, including failures and unsupported cells rather than only
  favorable checks;
- package and dependency versions plus the command or script that generated the output;
- cross-software comparator, exact convention alignment, tolerance, and status: passed, failed,
  or pending.

Use the result methods `tidy()`, `glance()`, `model_spec()`, `sample_info()`, and `provenance()` as
the minimum machine-readable audit trail. Avoid screenshots or manually copied tables as the
only retained result.
