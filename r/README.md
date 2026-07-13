# R backends

This directory is reserved for version-locked advanced statistical backends. Python remains the
orchestrator and shared result interface. R scripts must follow `docs/backend_policy.md`; do not
add ad hoc inline R commands or duplicate raw-data cleaning here.

The first backends cover Callaway--Sant'Anna group-time effects (`did`) and Sun--Abraham
cohort-interacted event studies (`fixest`). Their single authoritative, wheel-distributed scripts
are under `src/empirical_standards/backends/r_scripts/`, so installed and checkout behavior cannot
drift apart.
