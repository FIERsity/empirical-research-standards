# Robust inference and multiple testing

## Wild cluster bootstrap

`wild_cluster_bootstrap_fe` performs a null-imposed bootstrap-t test for one declared fixed-
effects coefficient. It fits a restricted model without that coefficient, applies one random
weight per entity or time cluster to the restricted residuals, reconstructs the outcome under
the null, and re-estimates the full model. Rademacher and six-point Webb weights are supported.
For final work, use at least 999 replications; Webb weights are often preferable with few
clusters. This implementation currently restricts the bootstrap cluster to the entity or time
dimension and requires at least one other predictor in the restricted model.

## Permutation inference

`permutation_did` preserves the number of treated entities while randomly reallocating the
time-invariant treatment assignment across entities. It is valid only when that assignment is
exchangeable under the null or when the permutation scheme matches the actual assignment
mechanism. Statistical significance from an invalid randomization design is not causal
evidence.

## Influence diagnostics

`leave_one_cluster_out_fe` removes each declared cluster and re-estimates the same model. It
reports the full-sample estimate, each deletion estimate, and the largest absolute change.
This is a sensitivity diagnostic, not an automatic rule for deleting influential clusters.

## Multiple testing

`adjust_pvalues` adjusts one explicitly declared family of tests using Bonferroni, Holm, or
Benjamini-Hochberg FDR. The researcher remains responsible for defining the family before
looking at results; splitting one family after inspection defeats the correction.
