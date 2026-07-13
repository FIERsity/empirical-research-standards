args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", args, value = TRUE)
script_path <- normalizePath(sub("^--file=", "", script_arg))
directory <- dirname(script_path)
data <- read.csv(file.path(directory, "panel_fixture.csv"))
model <- fixest::feols(
  y ~ x + did | id + time,
  data = data,
  cluster = ~id,
  ssc = fixest::ssc(K.fixef = "full", G.adj = FALSE)
)
# fixest uses (N-1)/(N-K); linearmodels uses N/(N-K). Align that declared
# finite-sample convention rather than comparing incompatible defaults.
aligned_vcov <- vcov(model) * nrow(data) / (nrow(data) - 1)
aligned_se <- sqrt(diag(aligned_vcov))
aligned_t <- coef(model) / aligned_se
table <- data.frame(
  term = names(coef(model)),
  estimate = as.numeric(coef(model)),
  std_error = as.numeric(aligned_se),
  statistic = as.numeric(aligned_t),
  p_value = 2 * pnorm(-abs(as.numeric(aligned_t))),
  conf_low = as.numeric(coef(model) - qnorm(0.975) * aligned_se),
  conf_high = as.numeric(coef(model) + qnorm(0.975) * aligned_se)
)
write.csv(table, file.path(directory, "fixest_results.csv"), row.names = FALSE)
