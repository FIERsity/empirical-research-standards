# Capability matrix

This matrix distinguishes implemented code from methodological completeness. A passing test
means the documented numerical behavior is reproducible; it does not validate a research
design or make a limited estimator equivalent to a full reference implementation.

## Core

| Area | Implemented | Main boundary |
|---|---|---|
| Data structure | Cardinality-checked merges and panel diagnostics | No data versioning or schema registry |
| OLS | Classical, HC1, one-way cluster covariance | No formula interface or multi-way clustering |
| Panel FE | Entity, time, and two-way FE; robust and one-/two-way clustering | No general multi-way HDFE estimator |
| Classic DID | Treated-by-post TWFE with controls | Researcher must justify parallel trends and timing |
| R staggered DID | `did::att_gt` DR/IPW/regression; group-time/event/cohort/calendar aggregation; support, weights, bootstrap bands, and pretrend output | Requires explicit R environment; identification remains design-specific |
| R Sun--Abraham | `fixest::sunab` cohort-event, event, cohort, and ATT aggregation; support weights, intervals, and pretrend output | Never-treated reference cohort and declared one-way clustering |
| Results | Tidy, glance, specification, sample, provenance, CSV/Excel/LaTeX export | Not a publication-table system |

## Advanced, with explicit limits

| Area | Implemented | Main boundary |
|---|---|---|
| TWFE event study | Dynamic coefficients and joint pre-period test | Can be contaminated under heterogeneous staggered effects |
| Python cohort-time reference | Unconditional two-period changes using never/not-yet-treated controls | Educational only: balanced panel; no covariate-adjusted or doubly robust score |
| Python cohort-interaction reference | Never-treated comparison, cohort interactions, weighted aggregation | Educational only; not equivalent to `fixest::sunab` |
| IV/2SLS | Explicit roles, common covariance options, first-stage and specification diagnostics | Identification remains substantive; no LIML or Fuller estimator |
| Panel IV | Indicator or within absorption; homoskedastic absorbed-DF option | Robust/cluster absorbed-DF correction is not implemented |
| Anderson-Rubin | One endogenous coefficient, robust/cluster options, grid inversion | No multi-endogenous AR confidence region |

## Supporting diagnostics

- Pre-specified FE subgroup fits and categorical interaction tests.
- Covariance sensitivity and placebo timing.
- Leave-one-cluster-out, treatment permutation, and null-imposed wild cluster bootstrap under
  their documented restrictions.
- Bonferroni, Holm, and Benjamini-Hochberg p-value adjustment.
- Conditional IV relevance F or Wald tests and sample-rank summaries. These are not formal
  weak-identification diagnostics.

## Not implemented

- Kleibergen-Paap rank and weak-identification statistics or critical values.
- General multi-way high-dimensional fixed effects outside the panel-IV path.
- LIML, Fuller, JIVE, or weak-identification-robust multi-parameter IV regions.
- Spatial econometrics, machine-learning validation workflows, data versioning, and a complete
  publication-table framework.

## Maturity rule

Treat core functions as reusable building blocks. Treat advanced functions as constrained
reference implementations and verify consequential applications against R. Do not advertise a
named method without stating the implemented comparison group, covariance convention, sample
requirement, and missing features.
