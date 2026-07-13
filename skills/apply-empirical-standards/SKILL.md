---
name: apply-empirical-standards
description: Apply the empirical-research-standards project to auditable empirical workflows with Python APIs and declared R estimator backends. Use when an agent needs to inspect research data, validate merges or panel structure, choose among OLS, fixed effects, DID, event-study, staggered-treatment, or IV methods, run design-matched diagnostics, export reproducible results, or verify estimates across languages.
---

# Apply Empirical Standards

Use the package as a transparent set of building blocks. Keep data roles, sample rules,
estimands, fixed effects, covariance choices, clustering, and omitted categories explicit.
Never treat a successful fit or a small p-value as evidence that an identification design is
valid.
Read `docs/backend_policy.md` before developing or invoking an advanced estimator. Use the backend
declared by the selected public API, verify its locked environment, and never substitute a
statistically different estimator silently.

## Start safely

1. Locate the research repository, data sources, data dictionary, and existing specifications.
2. Run `python skills/apply-empirical-standards/scripts/check_environment.py` from this package
   checkout, or pass `--project-root PATH`. Stop if required APIs are missing.
3. Preserve source data. Write derived data and outputs to separate, reproducible paths.
4. Record the outcome, treatment or endogenous variables, controls, identifiers, time variable,
   clusters, instruments, and expected unit of observation before fitting a model.
5. Read `docs/model_selection.md` and
   [references/method-selection.md](references/method-selection.md) before choosing an
   estimator. If the user's design is ambiguous, report the ambiguity instead of silently
   selecting a causal estimator.
6. For a new panel project, use `examples/research_workflow.py` and
   `docs/research_workflow.md` as the default auditable structure before adding advanced methods.
7. Read `docs/foundational_examples.md` and start from the matching OLS, fixed-effects, or
   common-adoption DID example rather than adapting an advanced estimator first.

## Execute the workflow

### 1. Audit the estimation data

- Validate every merge with `merge_validated`; declare the expected cardinality.
- For panel work, run `diagnose_panel` before estimation. Inspect duplicate entity-time keys,
  coverage, singletons, and within variation.
- Make missing-value handling explicit. Estimators reject missing or non-finite values unless
  complete-case deletion is explicitly requested.
- Report the original and used sample sizes. Do not overwrite raw columns to manufacture a
  valid design.

### 2. Write the design statement

State, before estimating:

- unit of observation and target estimand;
- treatment assignment or instrument story and identifying assumptions;
- outcome, regressors, controls, fixed effects, reference periods, and sample restrictions;
- covariance estimator and why the clustering level follows the assignment or dependence
  structure;
- diagnostics, falsification checks, and alternative specifications chosen independently of
  statistical significance.

If these cannot be defended from the research context, provide descriptive estimates only and
label them as non-causal.

### 3. Fit the smallest adequate estimator

Use the estimator map in [references/method-selection.md](references/method-selection.md), then
read the relevant project method document linked there. Use explicit keyword arguments for all
consequential choices. Consult [references/api-patterns.md](references/api-patterns.md) for
minimal call patterns and supported diagnostics.

Do not:

- use TWFE as the default for heterogeneous staggered treatment effects;
- interpret event-study pre-period insignificance as proof of parallel trends;
- call a robust Wald statistic a conventional first-stage F or Kleibergen-Paap statistic;
- assume an Anderson-Rubin confidence set is connected;
- compare subgroup significance instead of testing the difference between effects;
- search covariance types, windows, controls, or subgroups for a preferred p-value.

### 4. Diagnose and challenge the result

Match checks to the design. Use covariance sensitivity, placebo timing, formal heterogeneity
tests, leave-one-cluster-out, permutation inference, wild cluster bootstrap, multiple-testing
adjustment, first-stage diagnostics, or Anderson-Rubin inference only where their assumptions
fit the design. Distinguish specification sensitivity from identification evidence.

For staggered treatment, read `docs/staggered_did_audit.md` and inspect every returned `support`
and `aggregation_weights` table before interpreting dynamic effects. Retain group-time and
cohort-event cells, point and simultaneous intervals, comparison-group settings, reference rules,
pretrend tests, collinear terms, and backend warnings. Do not reduce the audit to one event plot.

### 5. Export an audit trail

For every primary model retain `tidy()`, `glance()`, `model_spec()`, `sample_info()`, and
`provenance()`. Use `collect_models` and `export_model_collection` for standardized exports.
Follow [references/output-checklist.md](references/output-checklist.md) before reporting a result.

### 6. Verify

Run the relevant tests and deterministic example. For consequential or new specifications,
compare coefficients and standard errors with direct Python library calls or R using identical
samples, fixed effects, covariance conventions, and finite-sample corrections. Label any
unavailable comparison as pending; never imply it was executed.

## Work outside this package checkout

If the target research project does not depend on `empirical-standards`, add it explicitly from
a released package or a pinned repository revision. Do not copy estimator source files into the
research project. Record the installed version and lock the environment.

If a requested method is absent, state the gap and apply the backend policy. Do not approximate
an unsupported estimator under a familiar name; use a mature R backend when it is the more
reliable implementation path.
