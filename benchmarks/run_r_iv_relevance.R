args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", args, value = TRUE)
script_path <- normalizePath(sub("^--file=", "", script_arg))
directory <- dirname(script_path)
data <- read.csv(file.path(directory, "iv_fixture.csv"))

reduced <- lm(endogenous ~ x, data = data)
full <- lm(endogenous ~ x + z1 + z2, data = data)
rss_reduced <- sum(residuals(reduced)^2)
rss_full <- sum(residuals(full)^2)
q <- 2
denominator_df <- df.residual(full)
statistic <- ((rss_reduced - rss_full) / q) / (rss_full / denominator_df)
output <- data.frame(
  endogenous = "endogenous",
  conditional_partial_r_squared = 1 - rss_full / rss_reduced,
  conditional_f_statistic = statistic,
  numerator_df = q,
  denominator_df = denominator_df,
  p_value = pf(statistic, q, denominator_df, lower.tail = FALSE)
)
write.csv(
  output,
  file.path(directory, "r_iv_relevance_results.csv"),
  row.names = FALSE
)
