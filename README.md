# Python Empirical Standards

English documentation comes first. A concise, detail-equivalent Chinese version follows.

`python-empirical-standards` is a small, transparent, and testable foundation for empirical
research and econometric analysis in Python. It makes consequential data, model, sample, and
inference choices explicit instead of hiding them behind a large framework.

## Status

Version 0.19.0 provides an installable Python package and a repository-distributed Agent Skill.
Capabilities are grouped by maturity rather than presented as equally complete.

Core building blocks:

- explicit table schemas, exportable validation reports, cardinality-checked merges, and panel
  diagnostics;
- validated OLS with classical, HC1, and one-way clustered covariance;
- one-way and two-way fixed effects with robust and one-/two-way clustered covariance;
- classic treated-by-post DID;
- standardized model tables, plotting data, CSV/Excel/LaTeX exports, and reproducibility
  metadata;
- the `apply-empirical-standards` Agent Skill for auditable data-to-result workflows.

Advanced components with material restrictions:

- TWFE event studies; unconditional balanced-panel cohort-time staggered DID; and a
  never-treated, cohort-interacted Sun-Abraham-style event study;
- entity-cluster bootstrap inference and simultaneous bands for the limited staggered-DID path;
- categorical FE heterogeneity tests, placebo timing, covariance sensitivity,
  leave-one-cluster-out diagnostics, permutation inference, and restricted wild cluster bootstrap;
- explicit IV/2SLS with first-stage, Wu-Hausman, Sargan, and robust Wooldridge score tests;
- multi-endogenous-variable sample-rank and conditional relevance diagnostics;
- panel IV/2SLS with entity/time fixed effects and single-endogenous-variable Anderson-Rubin
  weak-identification-robust tests and grid-inverted confidence sets;
- scalable `pyhdfe` within-transformation for panel-IV structural coefficients, alongside the
  exact indicator backend, with asymptotic covariance explicitly recorded;
- opt-in absorbed-degrees finite-sample covariance for homoskedastic within panel IV, verified
  against both the indicator backend and independent R matrix algebra;
- Bonferroni, Holm, and Benjamini-Hochberg multiple-testing adjustments;
- deterministic Python-R numerical benchmarks for fixed effects and 2SLS.

Not implemented: Kleibergen-Paap diagnostics, doubly robust staggered DID, general multi-way
HDFE, spatial econometrics, machine-learning validation, and a complete publication-table
framework. See the [capability matrix](docs/capability_matrix.md) for exact boundaries.

This is a working methodological foundation, not a complete econometrics library.

## Principles

- Correctness and explicit specifications before convenience.
- Reproducible environments, deterministic examples, and tested outputs.
- Independent modules that can be adopted and verified separately.
- Small additions driven by concrete research workflows.
- Results that can be cross-checked against R or direct Python library calls.
- No causal or substantive interpretation without defensible research assumptions.

The project does not choose a causal design for the researcher or replace inspection of source
data, assignment mechanisms, identification assumptions, and software-specific conventions.
Use the [bilingual model-selection guide](docs/model_selection.md) before choosing an estimator.

## Install and verify

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
```

## Quick start

### OLS

```python
import pandas as pd
from empirical_standards import fit_ols

data = pd.DataFrame({
    "y": [1.0, 2.2, 2.8, 4.1, 5.2, 5.8],
    "x": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
    "region": [1, 1, 1, 2, 2, 2],
})

result = fit_ols(
    data,
    outcome="y",
    predictors=["x"],
    covariance="cluster",
    cluster="region",
)
print(result.tidy())
```

Missing values raise an error by default. Set `drop_missing=True` to explicitly request
complete-case estimation. See [the OLS specification](docs/ols.md).

### Panel fixed effects and DID

```python
from empirical_standards import fit_did, fit_fixed_effects

fe = fit_fixed_effects(
    data, "y", ["x"], entity="city", time="year",
    time_effects=True, covariance="cluster_two_way",
)
did = fit_did(
    data, "y", "treated", "post", entity="city", time="year",
    controls=["x"], covariance="cluster_entity",
)
```

The causal module also includes dynamic TWFE, cohort-time ATT with optional entity-cluster
bootstrap inference, and Sun-Abraham cohort-interacted event studies. See
[panel and DID conventions](docs/panel_and_did.md) for identification and inference limits.

### Data validation

```python
from empirical_standards.data import diagnose_panel, merge_validated

merged = merge_validated(panel, attributes, on="city", relationship="many_to_one")
diagnostics = diagnose_panel(
    merged.data, entity="city", time="year", variables=["outcome", "treatment"]
)
print(diagnostics.summary())
```

See [data-validation conventions](docs/data_validation.md).

### IV/2SLS

```python
from empirical_standards import fit_iv_2sls

iv = fit_iv_2sls(
    data,
    "outcome",
    exogenous=["control"],
    endogenous=["treatment"],
    instruments=["instrument_1", "instrument_2"],
    covariance="cluster",
    cluster="region",
)
print(iv.first_stage)
```

First-stage statistics retain their actual reference distribution; robust Wald statistics are
not mislabeled as conventional F statistics. See [the IV/2SLS specification](docs/iv.md).

Panel IV uses the same explicit variable roles and adds entity/time fixed-effect indicators.
Anderson-Rubin tests support controls, fixed effects, robust covariance, and clustering; grid
inversion retains every accepted value rather than assuming a connected interval. See
[panel IV and Anderson-Rubin inference](docs/panel_iv_and_ar.md).

Set `absorption="within"` for scalable high-dimensional panel-IV coefficient estimation. The
default covariance is asymptotic; homoskedastic models may explicitly request the externally
verified absorbed-DF correction. Robust and clustered absorbed-DF corrections are unavailable.
Conditional relevance Wald tests are supporting diagnostics, not Kleibergen-Paap statistics.

### Results and exports

Every model result provides `tidy()`, `glance()`, `model_spec()`, `sample_info()`, and
`provenance()`. The sample metadata includes a deterministic fingerprint of the exact
estimation data.

```python
from empirical_standards.reporting import collect_models, export_model_collection

collection = collect_models({"baseline": baseline, "twfe": twfe, "did": did})
export_model_collection(collection, "outputs", prefix="main_results")
```

See the [result contract](docs/results.md), [reporting specification](docs/reporting.md), and
[cross-software benchmarks](benchmarks/README.md). Python-R fixed-effects and 2SLS benchmarks
are executed and tested.

## Runnable examples

```bash
uv run python examples/ols_example.py
uv run python examples/fixed_effects_example.py
uv run python examples/did_example.py
uv run python examples/panel_did_example.py
uv run python examples/data_validation_example.py
uv run python examples/research_workflow.py
```

The OLS example writes `outputs/ols_clustered.csv`. Other examples print deterministic model
and diagnostic results. The recommended end-to-end workflow writes a design manifest, panel
audit, primary models, robustness diagnostics, and standardized result metadata to
`outputs/research_workflow`. See the [bilingual workflow guide](docs/research_workflow.md).
The three separate foundational examples and their interpretation limits are documented in
[the bilingual examples guide](docs/foundational_examples.md).

## Agent Skill

The repository includes [`apply-empirical-standards`](skills/apply-empirical-standards/SKILL.md)
as a core product for research agents. It guides an agent through data audit, a written design
statement, estimator selection, design-matched diagnostics, standardized exports, and
cross-software verification. It does not automate identification claims or choose a model from
statistical significance.

Copy or symlink `skills/apply-empirical-standards` into the skill directory used by the target
agent, then invoke `$apply-empirical-standards`. From this checkout, verify its required package
APIs with:

```bash
uv run python skills/apply-empirical-standards/scripts/check_environment.py
```

The Skill is versioned with the package so that its workflow and API patterns can evolve with
implemented methods. Its references use repository-relative `docs/` paths; give the agent
access to this checkout when detailed method specifications are required.

## Repository layout

```text
src/empirical_standards/  Installable package
  data/                   Merge validation and panel diagnostics
  models/                 OLS and IV/2SLS
  panel/                  Fixed-effects estimation
  causal/                 DID and event-study estimators
  diagnostics/            Heterogeneity, robustness, and resampling inference
  results/                Shared metadata contract
  reporting/              Tables, plotting data, and exports
tests/                    Numerical, validation, and cross-software tests
benchmarks/               Deterministic Python-R benchmark assets
examples/                 Runnable deterministic workflows
docs/                     Method specifications and limitations
skills/                   Agent workflows and progressive references
.github/workflows/        Continuous integration
```

## Roadmap

The next priorities are data schemas and validation reports, a clearer model-selection guide,
complete foundational examples for OLS/FE/DID, and a stricter audit of the limited staggered-DID
and cohort-interacted event-study implementations. Additional advanced IV, spatial, and
machine-learning methods should wait until these foundational workflows are stable.

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a method. Every estimator must document
its estimand, assumptions, sample rules, defaults, covariance convention, failure modes,
runnable example, numerical tests, and external-comparison strategy.

## License

MIT

---

# 中文说明

`python-empirical-standards` 是一套小型、透明、可测试的 Python 实证研究与计量分析基础规范。项目显式记录数据、样本、模型和推断选择，避免由大型框架隐藏关键设定。

## 当前状态

当前版本为 0.19.0，产品包括 Python 包和 Agent Skill。功能按成熟度区分：

核心功能：

- 显式表级 schema、可导出验证报告、带基数约束的数据合并与面板诊断；
- OLS，以及经典、HC1、单向聚类协方差；
- 单向/双向固定效应，以及稳健、单向/双向聚类协方差；
- 经典 DID；
- 标准结果、元数据和 CSV/Excel/LaTeX 导出；
- `apply-empirical-standards` Agent Skill。

进阶但受限：

- TWFE 事件研究；要求平衡面板且无协变量调整的 cohort-time DID；要求 never-treated 对照的 Sun-Abraham 风格实现；
- 上述交错 DID 的实体 bootstrap 与同时置信带；
- FE 分类异质性、安慰剂、协方差敏感性、LOCO、置换和受限 wild cluster bootstrap；
- 显式 IV/2SLS，以及第一阶段、Wu-Hausman、Sargan、稳健 Wooldridge score 检验；
- 多内生变量样本秩与条件相关性辅助诊断；
- 带个体/时间固定效应的面板 IV/2SLS，以及单内生变量 Anderson-Rubin 弱识别稳健检验和网格反演置信集合；
- 面板 IV 的 `pyhdfe` 高维 within 后端，并保留精确指示变量后端；within 协方差明确标为渐近；
- 同方差 within 面板 IV 可显式启用吸收自由度有限样本修正，并已与指示变量后端及 R 矩阵公式核验；
- Bonferroni、Holm、Benjamini-Hochberg 多重检验校正；
- 固定效应和 2SLS 的确定性 Python-R 数值基准。
- 尚未实现 KP、双重稳健交错 DID、通用多维 HDFE、空间计量、机器学习验证和完整论文制表。准确边界见[功能矩阵](docs/capability_matrix.md)。
- `apply-empirical-standards` Agent Skill：规范数据审计、估计器选择、设计匹配的诊断、标准输出和跨软件核验。

这仍是方法基础，不是完整计量经济学库。

## 原则与边界

- 正确性和显式设定优先；环境、示例和输出可复现并经过测试。
- 模块保持独立，按真实研究需求小步扩展，并支持 Python-R 或 Python 底层库交叉验证。
- 项目不替研究者选择因果设计，也不替代对源数据、处理分配机制、识别假设和软件约定的审查，不自动解释实质性或因果含义。
- 选择估计器前请阅读[中英文模型选择指南](docs/model_selection.md)，其中列出适用条件、最低诊断和停止条件。

## 安装与验证

安装 [uv](https://docs.astral.sh/uv/) 后运行：

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
```

## 使用方式

上方英文部分给出了完整可运行代码。核心入口如下：

- `fit_ols`：OLS；默认拒绝缺失值，仅在 `drop_missing=True` 时进行完整案例估计，详见 [OLS 规范](docs/ols.md)。
- `fit_fixed_effects`、`fit_did`：固定效应和经典 DID；因果模块还包括 TWFE 动态效应、带实体聚类 bootstrap 的 cohort-time ATT、Sun-Abraham，识别与推断限制见 [面板与 DID 规范](docs/panel_and_did.md)。
- `merge_validated`、`diagnose_panel`：约束合并关系并检查面板覆盖、重复键、singleton 和 within/between 变异，详见 [数据规范](docs/data_validation.md)。
- `fit_iv_2sls`：显式区分外生变量、内生变量和排除工具；第一阶段保留真实参考分布，不把稳健 Wald 统计量误称为传统 F，详见 [IV/2SLS 规范](docs/iv.md)。
- `fit_panel_iv_2sls`、`anderson_rubin_test`：面板 IV 加入个体/时间固定效应；AR 支持控制变量、固定效应、稳健/聚类协方差，网格反演保留全部接受值，不假设置信集合连续，详见 [面板 IV 与 AR 规范](docs/panel_iv_and_ar.md)。
- 面板 IV 设置 `absorption="within"` 可扩展到高维固定效应；默认使用渐近协方差，同方差模型可显式启用已核验的吸收自由度修正，稳健/聚类修正尚未实现。条件相关性 Wald 只是辅助诊断，不是 KP。
- `collect_models`、`export_model_collection`：统一收集并导出模型结果。

所有模型结果都提供 `tidy()`、`glance()`、`model_spec()`、`sample_info()`、`provenance()`；样本元数据包含实际估计数据的确定性指纹。详见 [结果协议](docs/results.md)和[输出规范](docs/reporting.md)。

跨软件基准见 [benchmarks](benchmarks/README.md)：Python-R 固定效应与 2SLS 已实际运行并纳入测试。

## 示例与结构

```bash
uv run python examples/ols_example.py
uv run python examples/fixed_effects_example.py
uv run python examples/did_example.py
uv run python examples/panel_did_example.py
uv run python examples/data_validation_example.py
uv run python examples/research_workflow.py
```

OLS、固定效应和经典 DID 现有独立可运行示例，均导出设计说明、标准结果和针对性诊断，详见[中英文基础示例指南](docs/foundational_examples.md)。推荐的端到端示例会在 `outputs/research_workflow` 生成完整审计链，详见[工作流指南](docs/research_workflow.md)。

## Agent Skill

仓库将 [`apply-empirical-standards`](skills/apply-empirical-standards/SKILL.md) 作为核心产品：引导 Agent 依次完成数据审计、书面设计声明、估计器选择、匹配研究设计的诊断、标准导出与跨软件核验；它不会自动宣称识别成立，也不会按显著性选模型。

将 `skills/apply-empirical-standards` 复制或链接到目标 Agent 的 Skill 目录后，以 `$apply-empirical-standards` 调用。当前仓库内可运行：

```bash
uv run python skills/apply-empirical-standards/scripts/check_environment.py
```

Skill 与 Python 包同步版本管理；其中详细方法链接相对于本仓库，因此需要深读规范时应让 Agent 访问本仓库。

## 后续方向

下一步优先补数据 schema 与验证报告、清晰的模型选择指南、完整 OLS/FE/DID 基础示例，并严格复核受限的交错 DID 和 cohort-interacted event study。高级 IV、空间计量和机器学习方法暂缓。

贡献新方法前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。每个估计器必须说明估计目标、假设、样本规则、默认值、协方差约定、失败条件、可运行示例、数值测试和外部比较策略。

## 许可证

MIT
