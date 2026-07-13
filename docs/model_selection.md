# Model selection guide

## English

Select a model from the estimand, assignment process, and data structure. Do not select it from
the coefficient, p-value, or whichever specification produces the preferred result.

### Step 1: State the target

Write one sentence before opening the model API:

> For [population and period], estimate [association or causal effect] of [exposure/treatment]
> on [outcome], using variation from [cross-sectional, within-entity, treatment timing, or
> instrument-induced changes].

If the variation source cannot be stated, stop at descriptive analysis.

### Step 2: Choose the design family

| Research situation | Primary entry point | Minimum conditions | What it does not solve |
|---|---|---|---|
| Cross-sectional or pooled conditional association | `fit_ols` | Explicit outcome, predictors, sample, functional form, and dependence structure | Unobserved confounding or causal identification |
| Repeated entities; concern about stable entity differences | `fit_fixed_effects` | Within-entity variation and unique entity-time keys | Time-varying confounding or reverse causality |
| One treated group and one common post period | `fit_did` | Defensible comparison group, no anticipation, parallel trends, stable composition | Heterogeneous staggered timing or treatment endogeneity |
| Dynamic effects around a common treatment date | `fit_event_study` | DID conditions plus pre/post support and a declared reference period | Proof of parallel trends; staggered-effect contamination |
| Several adoption cohorts | `fit_staggered_did_r` (`did`) or `fit_sun_abraham_r` (`fixest`) | Cohort timing, eligible controls, support, anticipation, design-specific parallel trends | Backend maturity does not establish identification; Python reference variants are educational |
| Endogenous exposure with excluded instruments | `fit_iv_2sls` | Relevance, exclusion, independence, monotonicity when interpreting LATE | Instrument validity; weak-instrument problems |
| Instrumented exposure with panel fixed effects | `fit_panel_iv_2sls` | All IV conditions plus within variation and justified fixed effects | General high-dimensional IV inference |

### Step 3: Decide whether the claim is descriptive or causal

- Use association language when assignment or identification assumptions are not defensible.
- Fixed effects do not automatically make a coefficient causal.
- A pre-period joint test does not prove parallel trends.
- A strong first stage does not prove instrument exclusion.
- Robust standard errors change uncertainty estimates, not the identifying variation.

### Step 4: Choose fixed effects

- Add entity effects to remove stable entity-level differences only when the coefficient is
  identified by within-entity changes.
- Add time effects to remove common period shocks.
- Do not include an effect that absorbs the treatment or predictor of interest; inspect
  `diagnose_panel(...).variable_variation` first.
- Do not choose two-way effects mechanically. State which confounding path each dimension
  addresses.

### Step 5: Choose covariance and clustering

| Dependence assumption | Typical option | Required justification |
|---|---|---|
| Independent, homoskedastic errors | `unadjusted` / `nonrobust` | Rarely credible in observational panels |
| Independent observations, unknown variance | `HC1` / `robust` | No meaningful within-group dependence |
| Serial or shared dependence within entity | entity clustering | Usually the starting point for panel treatment assignment |
| Dependence within time periods | time clustering | Common shocks not fully captured by time effects |
| Both entity and time dependence | two-way clustering | Enough clusters in both dimensions |

The cluster level should follow treatment assignment or residual dependence. Do not search
cluster definitions for significance.

### Step 6: Require design-matched diagnostics

- OLS: sample rules, residual/dependence reasoning, leverage or sensitivity where relevant.
- FE: panel keys, within variation, singleton counts, covariance sensitivity.
- DID: treatment timing audit, pre-treatment support, event study, placebo dates, cluster level.
- Staggered DID: cohort support, control eligibility by period, aggregation weights, sensitivity
  to comparison-group choice, and external R verification.
- IV: first-stage diagnostics, instrument count/rank, exclusion argument, overidentification
  limits, and Anderson-Rubin inference where supported.

### Step 7: Stop conditions

Do not fit or report the planned model as causal when:

- the unit of observation or treatment timing is ambiguous;
- merge cardinality or entity-time uniqueness fails;
- the identifying variable has no usable variation after fixed effects;
- no credible comparison group exists;
- treatment occurs before the declared observation window without a defensible baseline;
- instruments overlap with controls, are rank deficient, or lack a substantive exclusion story;
- the desired method is listed as not implemented in `docs/capability_matrix.md`.

### Minimum design record

Store these fields beside every primary result:

```text
claim_type: association | causal
population_and_period:
unit_of_observation:
outcome:
exposure_or_treatment:
estimand:
identifying_variation:
comparison_group:
controls:
fixed_effects:
covariance_and_clusters:
sample_restrictions:
identification_assumptions:
diagnostics:
external_verification:
```

## 中文

模型必须由估计目标、处理分配和数据结构决定，不能由显著性决定。估计前先写清：研究对象和时期、观测单位、结果变量、处理或解释变量、目标是相关性还是因果效应，以及系数依赖哪一种变化。

选择顺序：横截面或混合相关性用 OLS；需要控制个体不变差异且存在组内变化时用固定效应；共同处理时点和明确对照组可考虑经典 DID；共同处理时点的动态效应用事件研究；多个处理批次只能在核对 cohort 支持、对照资格和当前实现限制后使用交错 DID；只有存在实质性排除理由的工具变量时才使用 IV。

固定效应不自动产生因果解释；前置期不显著不能证明平行趋势；第一阶段强不能证明工具有效；稳健标准误只改变不确定性估计，不修复识别问题。聚类层级应跟随处理分配或误差相关结构，不能为得到显著结果而搜索聚类方案。

遇到观测单位或处理时点不清、合并关系或面板键失败、固定效应后无有效变化、没有可信对照组、工具变量秩不足或缺乏排除理由、所需方法尚未实现时，应停止因果估计并报告问题。
