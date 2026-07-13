# Staggered-treatment audit and backend choice

## Decision

The research-grade advanced paths are explicit R backends:

- `fit_staggered_did_r` calls `did::att_gt` and `did::aggte` for group-time, dynamic, and overall
  treatment effects. It supports doubly robust (`dr`), inverse-probability-weighted (`ipw`), and
  outcome-regression (`reg`) estimation, never-treated or not-yet-treated controls, anticipation,
  unbalanced panels, multiplier bootstrap inference, and simultaneous bands.
- `fit_sun_abraham_r` calls `fixest::sunab` inside a two-way fixed-effects regression and returns
  the package's event-time aggregation with declared clustered inference.

There is no automatic fallback. Missing R or packages raises an actionable error, because silently
substituting a statistically different estimator would invalidate the research specification.

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

## 中文说明

复杂交错处理研究应优先使用显式 R 后端：`fit_staggered_did_r` 对接 `did::att_gt`，
`fit_sun_abraham_r` 对接 `fixest::sunab`。Python 负责数据与设定校验、调用和标准化输出，
不会在 R 不可用时偷偷换成其他估计量。

原有 `fit_staggered_did` 只是不含协变量调整的平衡面板参考实现；原有
`fit_sun_abraham` 是手工构建设计矩阵的有限参考实现。二者适合教学和核查，但不应再被理解为
成熟 R 方法的完整等价物。输出会记录 R、包版本、脚本与全部模型设定，依赖由 `r/renv.lock` 锁定。
