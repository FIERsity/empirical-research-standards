# Foundational examples

## English

- `examples/ols_example.py` estimates one association under classical, HC1, and group-clustered
  covariance. The coefficient is unchanged because covariance choice changes inference, not the
  OLS estimand. The example does not make a causal claim.
- `examples/fixed_effects_example.py` verifies within-entity exposure variation, compares entity
  and two-way fixed effects, and exports covariance sensitivity. Fixed effects remove stable
  entity differences but not time-varying confounding.
- `examples/did_example.py` uses a simulated common adoption date, never-treated comparisons,
  entity clustering, an event study, and pre-treatment placebo dates. Its causal interpretation
  relies on parallel trends, no anticipation, and stable composition; diagnostics do not prove
  those assumptions.

Each script accepts `--output PATH` and exports `design.json`, tidy results, model settings,
sample information, provenance, and method-specific diagnostics.

## 中文

OLS 示例比较经典、HC1 和组聚类标准误，只解释条件相关性；固定效应示例先检查组内变化，再比较个体和双向固定效应，并强调固定效应不能消除时变混杂；经典 DID 示例使用共同处理时点和从未处理组，加入事件研究与处理前安慰剂，但因果解释仍依赖平行趋势、无预期效应和样本构成稳定。

三个脚本均支持 `--output PATH`，并导出设计说明、系数、模型设定、样本、软件来源和针对性诊断。
