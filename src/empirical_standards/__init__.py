"""Transparent building blocks for empirical research."""

from empirical_standards.causal.did import DIDResult, EventStudyResult, fit_did, fit_event_study
from empirical_standards.causal.staggered import StaggeredDIDResult, fit_staggered_did
from empirical_standards.causal.sun_abraham import SunAbrahamResult, fit_sun_abraham
from empirical_standards.models.iv import IV2SLSResult, fit_iv_2sls
from empirical_standards.models.iv_diagnostics import summarize_first_stage
from empirical_standards.models.iv_inference import (
    AndersonRubinConfidenceSet,
    AndersonRubinResult,
    anderson_rubin_confidence_set,
    anderson_rubin_test,
)
from empirical_standards.models.iv_relevance import IVRelevanceDiagnostics, diagnose_iv_relevance
from empirical_standards.models.ols import OLSResult, fit_ols
from empirical_standards.panel.fixed_effects import FixedEffectsResult, fit_fixed_effects
from empirical_standards.panel.iv import PanelIV2SLSResult, fit_panel_iv_2sls

__all__ = [
    "AndersonRubinConfidenceSet",
    "AndersonRubinResult",
    "DIDResult",
    "EventStudyResult",
    "FixedEffectsResult",
    "IV2SLSResult",
    "IVRelevanceDiagnostics",
    "OLSResult",
    "PanelIV2SLSResult",
    "StaggeredDIDResult",
    "SunAbrahamResult",
    "anderson_rubin_confidence_set",
    "anderson_rubin_test",
    "diagnose_iv_relevance",
    "fit_did",
    "fit_event_study",
    "fit_fixed_effects",
    "fit_iv_2sls",
    "fit_ols",
    "fit_panel_iv_2sls",
    "fit_staggered_did",
    "fit_sun_abraham",
    "summarize_first_stage",
]
__version__ = "0.16.0"
