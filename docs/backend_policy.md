# Backend policy: Python-first, not Python-only

## English

The project chooses a computational backend from methodological reliability and workflow fit,
not language loyalty.

### Default to Python

Use Python for:

- data reading, cleaning, schema validation, merging, and reproducible pipelines;
- OLS, standard fixed effects, classic DID, and other methods with transparent, verified Python
  implementations;
- shared result objects, metadata, exports, Agent orchestration, and future machine learning;
- any method that can be implemented plainly, tested numerically, and maintained without
  recreating a specialist statistical package.

Python remains the user-facing entry point because its environment is widely available, its
general-purpose syntax supports complete research pipelines, and it integrates naturally with
machine learning and production systems.

### Switch to R immediately

Use an R backend instead of extending Python when any of these conditions applies:

- a mature, actively maintained R package is the accepted reference implementation;
- correct implementation requires complex influence functions, cohort aggregation, resampling,
  weak-identification theory, or software-specific finite-sample conventions;
- the Python implementation would be a reduced approximation presented under a standard method
  name;
- independent validation cannot be made transparent at reasonable maintenance cost;
- Python and the reference R implementation disagree and the discrepancy cannot be resolved from
  documented conventions.

Do not spend multiple releases reproducing a specialist R estimator merely to preserve a
single-language repository.

### Backend contract

Python orchestrates every workflow. An R backend must:

1. receive an explicit model specification and a frozen estimation dataset;
2. perform no undocumented data cleaning or sample selection;
3. use version-locked R packages, preferably through `renv`;
4. return tidy coefficients, model summary, sample counts, method settings, diagnostics, package
   versions, warnings, and errors in a documented JSON/CSV contract;
5. preserve estimator name, comparison group, aggregation weights, covariance, clustering,
   bootstrap settings, and reference periods;
6. be executable and testable independently from Python;
7. be wrapped by the same Python result and provenance interface used by native estimators.

Backend selection must never be silent. Every result records `backend`, language version,
package names and versions, executed script, input fingerprint, and output files.

### Dependency levels

- Base installation: Python only; all core data, OLS, FE, classic DID, and reporting workflows
  remain usable.
- Advanced methods: optional R installation plus a locked project R environment.
- Missing R: fail with an actionable environment message; never substitute a different Python
  estimator under the requested method name.

### Current migration priorities

The first R-backed candidates are staggered DID and cohort-interacted event studies. Audit the
current Python reference implementations against mature R packages, then retain them only as
clearly limited educational implementations or deprecate them if their behavior diverges.

## 中文

项目遵循“Python-first，不是 Python-only”。Python 继续负责数据工程、schema、基础计量、统一结果、Agent 编排和未来机器学习，因为环境更普及、语法通用、完整工作流更容易维护。

当成熟 R 包已经是方法参考实现，或 Python 需要重写复杂 influence function、cohort aggregation、bootstrap、弱识别或有限样本约定时，应立即转向 R，不为保持单一语言而提供缩水实现。若 Python 与参考 R 结果无法依据公开约定解释，也应停止扩展 Python 路径。

R 是可选后端：Python 传入冻结样本和显式模型设定；R 不得隐式清洗数据；依赖应通过 `renv` 锁定；返回统一 JSON/CSV，包含系数、样本、设定、诊断、包版本和警告；Python 再转换为统一结果协议。后端切换必须公开记录，缺少 R 时明确失败，不能偷偷换用另一个 Python 估计器。
