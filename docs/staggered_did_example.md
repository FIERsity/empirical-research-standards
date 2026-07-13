# Staggered-treatment example

## English

Run the complete audited example after restoring `r/renv.lock`:

```bash
Rscript -e 'renv::restore(project="r", prompt=FALSE)'
uv run python examples/staggered_did_r_example.py
```

The example reads the fixed panel in `benchmarks/staggered_did/panel.csv`, validates panel
structure, fits doubly robust Callaway--Sant'Anna group-time effects with not-yet-treated controls,
and fits a Sun--Abraham cohort-interacted event study with entity-clustered inference. It exports:

- group-time, event-time, cohort, calendar-time, and overall effects;
- point intervals and, when requested, simultaneous bootstrap bands;
- treated/control support and aggregation weights;
- disaggregated Sun--Abraham cohort-event coefficients;
- pre-period joint tests, warnings, exact specifications, sample fingerprints, and backend versions.

Outputs are written to `outputs/staggered_did_r/`. The example intentionally disables bootstrap
to run quickly. Final analysis should normally enable it with at least 999 repetitions and a fixed
seed, then retain the simultaneous bands.

Do not choose between estimators from significance. Their estimands, comparison groups, and
weighting differ. A small pre-period test statistic does not prove parallel trends, and support
counts do not prove conditional overlap.

## 中文

先恢复 `r/renv.lock`，再运行 `examples/staggered_did_r_example.py`。示例使用固定面板数据，
先检查面板结构，再估计以尚未处理单位为对照的 Callaway--Sant'Anna 交错 DID，并估计按实体聚类
的 Sun--Abraham 事件研究。

输出包括 group-time、事件时间、cohort、日历时间和总体效应，点置信区间、可选同时置信带、
处理组与对照组支持、聚合权重、未聚合 cohort×event 系数、前趋势联合检验、warnings、完整设定、
样本指纹和后端版本。示例为提高运行速度关闭 bootstrap；正式分析通常应使用至少 999 次重复、
固定随机种子并保存同时置信带。不能按显著性选择估计器，前置期不显著和样本支持都不能证明识别成立。
