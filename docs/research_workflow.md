# Auditable research workflow

## English

Use the package in this order:

1. Preserve raw inputs and declare the unit of observation.
2. Validate merge cardinality with `merge_validated`.
3. Diagnose duplicate keys, coverage, balance, singletons, and within variation with
   `diagnose_panel`.
4. Write the estimand, treatment timing, comparison group, controls, fixed effects, sample
   restrictions, and covariance choice before estimation.
5. Fit one primary model. Do not select the specification from significance.
6. Use event studies, placebo dates, covariance sensitivity, and heterogeneity tests as
   diagnostics matched to the design; none proves identification.
7. Export coefficients together with model settings, sample information, dependency versions,
   and the exact estimation-sample fingerprint.
8. Verify consequential results against R using identical samples and covariance conventions.

Run `uv run python examples/research_workflow.py`. The example uses simulated common-adoption
DID data because its assumptions are known by construction. Real data require a substantive
parallel-trends argument; a pre-period test cannot establish it.

## 中文

推荐顺序：保留原始数据并声明观测单位；约束合并关系；检查面板键、覆盖、平衡性和组内变异；估计前写明估计目标、处理时点、对照组、控制变量、固定效应、样本和协方差；只设一个主模型；再做事件研究、安慰剂、协方差敏感性和正式异质性检验；最后连同模型设定、样本指纹和软件版本一起导出，并对重要结果做 Python–R 核验。

可运行 `uv run python examples/research_workflow.py`。示例使用假设由生成过程保证的共同处理时点 DID；真实数据仍需研究者论证平行趋势，前置期不显著不能证明平行趋势成立。
