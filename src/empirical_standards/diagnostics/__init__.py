"""Heterogeneity and robustness workflows."""

from empirical_standards.diagnostics.heterogeneity import (
    HeterogeneityResult,
    InteractionHeterogeneityResult,
    fit_fe_by_group,
    fit_fe_heterogeneity,
)
from empirical_standards.diagnostics.inference import (
    LeaveOneClusterOutResult,
    PermutationResult,
    WildClusterBootstrapResult,
    adjust_pvalues,
    leave_one_cluster_out_fe,
    permutation_did,
    wild_cluster_bootstrap_fe,
)
from empirical_standards.diagnostics.robustness import covariance_sensitivity, placebo_did

__all__ = [
    "HeterogeneityResult",
    "InteractionHeterogeneityResult",
    "LeaveOneClusterOutResult",
    "PermutationResult",
    "WildClusterBootstrapResult",
    "adjust_pvalues",
    "covariance_sensitivity",
    "fit_fe_by_group",
    "fit_fe_heterogeneity",
    "leave_one_cluster_out_fe",
    "permutation_did",
    "placebo_did",
    "wild_cluster_bootstrap_fe",
]
