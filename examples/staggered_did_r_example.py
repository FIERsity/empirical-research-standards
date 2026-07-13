"""Run audited staggered-treatment estimators through the declared R backends."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from empirical_standards import fit_staggered_did_r, fit_sun_abraham_r
from empirical_standards.data import diagnose_panel

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "staggered_did_r"


def main() -> None:
    data = pd.read_csv(ROOT / "benchmarks" / "staggered_did" / "panel.csv")
    diagnostics = diagnose_panel(
        data,
        entity="entity",
        time="period",
        variables=["outcome", "adoption", "x"],
    )
    callaway_santanna = fit_staggered_did_r(
        data,
        "outcome",
        entity="entity",
        time="period",
        treatment_time="adoption",
        controls=["x"],
        control_group="not_yet_treated",
        method="dr",
        bootstrap=False,
        simultaneous_band=False,
    )
    sun_abraham = fit_sun_abraham_r(
        data,
        "outcome",
        "adoption",
        entity="entity",
        time="period",
        controls=["x"],
        cluster="entity",
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    diagnostics.summary().to_csv(OUTPUT / "panel_summary.csv", header=False)
    for component in (
        "group_time",
        "event_time",
        "cohort",
        "calendar_time",
        "support",
        "aggregation_weights",
    ):
        callaway_santanna.tidy(component).to_csv(
            OUTPUT / f"callaway_santanna_{component}.csv", index=False
        )
    for component in ("event_time", "cohort", "cohort_event", "support"):
        sun_abraham.tidy(component).to_csv(
            OUTPUT / f"sun_abraham_{component}.csv", index=False
        )
    audit = {
        "callaway_santanna": {
            "glance": callaway_santanna.glance().to_dict(),
            "specification": callaway_santanna.model_spec(),
            "sample": callaway_santanna.sample_info(),
            "provenance": callaway_santanna.provenance(),
        },
        "sun_abraham": {
            "glance": sun_abraham.glance().to_dict(),
            "specification": sun_abraham.model_spec(),
            "sample": sun_abraham.sample_info(),
            "provenance": sun_abraham.provenance(),
        },
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, default=str), encoding="utf-8"
    )
    print(f"Callaway-Sant'Anna overall ATT: {callaway_santanna.overall_att:.3f}")
    print(f"Sun-Abraham overall ATT: {sun_abraham.overall_att:.3f}")
    print(f"Audit outputs: {OUTPUT}")


if __name__ == "__main__":
    main()
