# Result and metadata contract

Every public estimator returns an object with five common views:

- `tidy()`: parameter-level or group-time estimates.
- `glance()`: one-dimensional model summary.
- `model_spec()`: estimator, outcome, predictors, and consequential settings.
- `sample_info()`: original/used rows, included columns, and a SHA-256 sample fingerprint.
- `provenance()`: Python, platform, and core dependency versions.

The fingerprint covers the exact ordered estimation data, including its index, column names,
and dtypes. It detects accidental changes; it is not a privacy guarantee and should not be
used as a substitute for archiving source data. Platform metadata may differ across otherwise
numerically equivalent runs.

Model metadata is intended to travel with exported estimates. A future reporting layer will
consume this contract rather than inspect estimator-specific internals.
