# R backends

This directory is reserved for version-locked advanced statistical backends. Python remains the
orchestrator and shared result interface. R scripts must follow `docs/backend_policy.md`; do not
add ad hoc inline R commands or duplicate raw-data cleaning here.

The first planned backend audit covers staggered DID and cohort-interacted event studies. No R
estimator is advertised as available until its environment, input/output contract, tests, and
provenance capture are committed.
