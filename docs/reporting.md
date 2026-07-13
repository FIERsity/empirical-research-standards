# Standardized reporting

`collect_models` consumes only the shared result contract and combines heterogeneous models
into coefficient, model-summary, specification, sample, and provenance tables. Model names
are supplied explicitly by the analyst and preserved in every output.

`export_model_collection` writes five CSV files, one Excel workbook with five sheets, and a
LaTeX coefficient table. These are analysis artifacts rather than publication-style tables:
formatting should occur after the underlying values and metadata are frozen.

`event_study_plot_data` normalizes event time, estimate, and confidence interval columns for
plotting. It intentionally does not impose colors, fonts, labels, or a graphical style.

The `benchmarks` directory contains a deterministic panel fixture and reproducible Python and
R scripts. Python and R coefficients and cluster-robust standard errors are compared only
after aligning their finite-sample covariance conventions. Stata remains marked pending until
run in a licensed environment; the repository never treats an unexecuted script as validation.
