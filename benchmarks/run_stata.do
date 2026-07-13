clear all
import delimited "panel_fixture.csv", clear
* Requires reghdfe and ftools. Run from the benchmarks directory.
reghdfe y x did, absorb(id time) vce(cluster id)
matrix b = e(b)
matrix V = e(V)
* Export x and did coefficients/standard errors using the laboratory's approved
* Stata table exporter, then map to the schema documented in benchmark_manifest.csv.

