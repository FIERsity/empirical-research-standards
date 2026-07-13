# Staggered-treatment audit and backend choice

## Decision

The research-grade advanced paths are explicit R backends:

- `fit_staggered_did_r` calls `did::att_gt` and `did::aggte` for group-time, dynamic, and overall
  treatment effects. It supports doubly robust (`dr`), inverse-probability-weighted (`ipw`), and
  outcome-regression (`reg`) estimation, never-treated or not-yet-treated controls, anticipation,
  unbalanced panels, multiplier bootstrap inference, and simultaneous bands.
- `fit_sun_abraham_r` calls `fixest::sunab` inside a two-way fixed-effects regression and returns
  disaggregated cohort-event coefficients plus event-time, cohort, and overall aggregation with
  declared clustered inference.

There is no automatic fallback. Missing R or packages raises an actionable error, because silently
substituting a statistically different estimator would invalidate the research specification.

## Returned audit components

`RStaggeredDIDResult.tidy(component=...)` accepts:

- `group_time`: ATT(g,t), standard errors, point intervals, and simultaneous bands;
- `event_time`, `cohort`, and `calendar_time`: native `aggte` aggregations;
- `support`: treated and eligible comparison counts for every reported cell;
- `aggregation_weights`: cohort-size weights for dynamic and simple aggregation.

Its `glance()` output includes simple and dynamic overall effects, the native parallel-trends
pretest, critical values, estimator settings, warnings, and backend versions.

`RSunAbrahamResult.tidy(component=...)` accepts `event_time`, `cohort`, `cohort_event`, and
`support`. The support table records cohort sizes, observations, and event-specific aggregation
weights. `glance()` includes overall ATT, the joint pre-period Wald test, cluster degrees of
freedom, reference rules, collinear terms, warnings, formula, and backend versions.

Support counts and weights describe the cells supplied to the estimator. They do not establish
parallel trends, overlap conditional on covariates, or a causal interpretation.

## Status of the Python implementations

`fit_staggered_did` is an **educational unconditional reference estimator**. It computes two-period
mean changes for each cohort and post-treatment time using never-treated or not-yet-treated units,
requires a balanced panel, and optionally resamples entities. It does not implement the influence
functions, covariate adjustment, doubly robust score, or complete aggregation inference of
`did::att_gt`. Its numbers need not match `did` even on the same data.

`fit_sun_abraham` is a **limited cohort-interaction reference implementation**. It explicitly builds
cohort-by-relative-time indicators, absorbs entity and time effects, and aggregates using observed
cohort sizes. It currently requires never-treated units and bins window tails. It is useful for
inspecting the design matrix, but is not a full reproduction of `fixest::sunab` reference cohorts,
supported-cell weights, coefficient removal, and finite-sample covariance conventions.

The old functions remain available for compatibility and teaching. New empirical work with
heterogeneous staggered adoption should normally choose the explicit `_r` functions.

## Reproducibility contract

Python validates columns and panel keys, writes a temporary CSV plus a complete JSON specification,
runs a versioned package-owned R script, and reads JSON/CSV outputs. Results record the R version,
package versions, script path, and full estimator specification. R dependencies are locked in
`r/renv.lock`; restore them with `Rscript -e 'renv::restore()'` from `r/`.

The fixed regression benchmark under `benchmarks/staggered_did/` records input data, specification,
expected `did`/`fixest` tables, and backend versions. Regenerate it only after reviewing numerical
changes from a deliberate dependency or contract update.

## 中文说明

复杂交错处理研究应优先使用显式 R 后端：`fit_staggered_did_r` 对接 `did::att_gt`，
`fit_sun_abraham_r` 对接 `fixest::sunab`。Python 负责数据与设定校验、调用和标准化输出，
不会在 R 不可用时偷偷换成其他估计量。

交错 DID 输出 group-time、事件时间、cohort、日历时间、总体效应、点区间、同时区间、
支持数量、聚合权重和前趋势检验。Sun--Abraham 输出 cohort×event、事件时间、cohort、总体
ATT、置信区间、联合前趋势检验、聚类自由度、共线项和 warnings。固定基准数据用于监测升级后的
数值漂移；这些诊断不能代替平行趋势、对照组合理性和因果识别论证。

原有 `fit_staggered_did` 只是不含协变量调整的平衡面板参考实现；原有
`fit_sun_abraham` 是手工构建设计矩阵的有限参考实现。二者适合教学和核查，但不应再被理解为
成熟 R 方法的完整等价物。输出会记录 R、包版本、脚本与全部模型设定，依赖由 `r/renv.lock` 锁定。
