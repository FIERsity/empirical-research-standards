args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("expected input.csv specification.json output_directory")
data <- read.csv(args[[1]], check.names = FALSE)
spec <- jsonlite::fromJSON(args[[2]], simplifyVector = TRUE)
output <- args[[3]]
warnings_seen <- character()
capture_warnings <- function(expr) {
  withCallingHandlers(expr, warning = function(w) {
    warnings_seen <<- unique(c(warnings_seen, conditionMessage(w)))
    invokeRestart("muffleWarning")
  })
}

never_value <- max(data[[spec$time]], na.rm = TRUE) + 10000
data[[spec$treatment_time]][is.na(data[[spec$treatment_time]])] <- never_value
rhs <- c(
  spec$controls,
  sprintf("sunab(%s, %s, ref.p=%s)", spec$treatment_time, spec$time, spec$reference_period)
)
formula <- as.formula(sprintf(
  "%s ~ %s | %s + %s",
  spec$outcome, paste(rhs, collapse = " + "), spec$entity, spec$time
))
model <- capture_warnings(fixest::feols(
  formula, data = data, vcov = as.formula(paste("~", spec$cluster)), notes = FALSE
))

extract_table <- function(aggregation, term_prefix, index_pattern) {
  summary_model <- capture_warnings(summary(model, agg = aggregation))
  coefficient_table <- summary_model$coeftable
  keep <- grepl(term_prefix, rownames(coefficient_table))
  coefficient_table <- coefficient_table[keep, , drop = FALSE]
  intervals <- capture_warnings(confint(
    model, agg = aggregation, level = spec$confidence_level
  ))
  intervals <- intervals[rownames(coefficient_table), , drop = FALSE]
  result <- data.frame(
    term = rownames(coefficient_table),
    estimate = as.numeric(coefficient_table[, "Estimate"]),
    std_error = as.numeric(coefficient_table[, "Std. Error"]),
    statistic = as.numeric(coefficient_table[, "t value"]),
    p_value = as.numeric(coefficient_table[, "Pr(>|t|)"]),
    conf_low = as.numeric(intervals[, 1]),
    conf_high = as.numeric(intervals[, 2])
  )
  result$index <- as.numeric(sub(index_pattern, "", result$term))
  result
}

event_time <- extract_table("period", paste0("^", spec$time, "::"), ".*::")
names(event_time)[names(event_time) == "index"] <- "event_time"
cohort <- extract_table("cohort", "^cohort::", "cohort::")
names(cohort)[names(cohort) == "index"] <- "cohort"
overall_table <- capture_warnings(summary(model, agg = "att")$coeftable)
overall_row <- overall_table["ATT", , drop = FALSE]
overall_interval <- capture_warnings(confint(
  model, agg = "att", level = spec$confidence_level
))["ATT", ]

disaggregated <- capture_warnings(summary(model, agg = FALSE)$coeftable)
keep_disaggregated <- grepl(paste0("^", spec$time, "::.*:cohort::"), rownames(disaggregated))
disaggregated <- disaggregated[keep_disaggregated, , drop = FALSE]
disaggregated_intervals <- capture_warnings(confint(
  model, agg = FALSE, level = spec$confidence_level
))
disaggregated_intervals <- disaggregated_intervals[rownames(disaggregated), , drop = FALSE]
cohort_event <- data.frame(
  term = rownames(disaggregated),
  event_time = as.numeric(sub(paste0("^", spec$time, "::(-?[0-9]+):.*$"), "\\1", rownames(disaggregated))),
  cohort = as.numeric(sub("^.*:cohort::([0-9.]+)$", "\\1", rownames(disaggregated))),
  estimate = as.numeric(disaggregated[, "Estimate"]),
  std_error = as.numeric(disaggregated[, "Std. Error"]),
  statistic = as.numeric(disaggregated[, "t value"]),
  p_value = as.numeric(disaggregated[, "Pr(>|t|)"]),
  conf_low = as.numeric(disaggregated_intervals[, 1]),
  conf_high = as.numeric(disaggregated_intervals[, 2])
)

cohorts <- sort(unique(data[[spec$treatment_time]][data[[spec$treatment_time]] != never_value]))
cohort_sizes <- vapply(cohorts, function(g) {
  length(unique(data[[spec$entity]][data[[spec$treatment_time]] == g]))
}, numeric(1))
support <- unique(data.frame(
  cohort = data[[spec$treatment_time]][data[[spec$treatment_time]] != never_value],
  event_time = (
    data[[spec$time]][data[[spec$treatment_time]] != never_value] -
      data[[spec$treatment_time]][data[[spec$treatment_time]] != never_value]
  )
))
support <- support[support$event_time != spec$reference_period, ]
support <- merge(
  support, data.frame(cohort = cohorts, cohort_size = cohort_sizes),
  by = "cohort", all.x = TRUE
)
support$observations <- vapply(seq_len(nrow(support)), function(i) {
  sum(data[[spec$treatment_time]] == support$cohort[[i]] &
      data[[spec$time]] - data[[spec$treatment_time]] == support$event_time[[i]])
}, numeric(1))
identified_keys <- unique(cohort_event[, c("cohort", "event_time")])
identified_keys$identified <- TRUE
support <- merge(support, identified_keys, by = c("cohort", "event_time"), all.x = TRUE)
support$identified[is.na(support$identified)] <- FALSE
support$aggregation_weight <- NA_real_
for (event in unique(support$event_time)) {
  use <- support$event_time == event & support$identified
  support$aggregation_weight[use] <- support$cohort_size[use] / sum(support$cohort_size[use])
}
support$never_treated_entities <- length(unique(
  data[[spec$entity]][data[[spec$treatment_time]] == never_value]
))
support <- support[order(support$event_time, support$cohort), ]

pretrend <- capture_warnings(fixest::wald(
  model, keep = paste0("^", spec$time, "::-"), print = FALSE
))
collinear <- if (is.null(model$collin.var)) character() else model$collin.var

write.csv(event_time, file.path(output, "event_time.csv"), row.names = FALSE)
write.csv(cohort, file.path(output, "cohort.csv"), row.names = FALSE)
write.csv(cohort_event, file.path(output, "cohort_event.csv"), row.names = FALSE)
write.csv(support, file.path(output, "support.csv"), row.names = FALSE)

result <- list(
  estimator = "sun_abraham_fixest",
  backend = "R",
  package = "fixest",
  nobs_input = nrow(data),
  nobs = stats::nobs(model),
  dropped_nobs = nrow(data) - stats::nobs(model),
  overall_att = unname(overall_row[, "Estimate"]),
  overall_std_error = unname(overall_row[, "Std. Error"]),
  overall_conf_low = unname(overall_interval[[1]]),
  overall_conf_high = unname(overall_interval[[2]]),
  pretrend_statistic = unname(pretrend$stat),
  pretrend_p_value = unname(pretrend$p),
  pretrend_df_num = unname(pretrend$df1),
  inference_df = unname(fixest::degrees_freedom(model, "t")),
  reference_period = spec$reference_period,
  reference_cohort = "never_treated",
  cluster = spec$cluster,
  covariance = paste0("cluster~", spec$cluster),
  fixed_effects = c(spec$entity, spec$time),
  tail_binning = FALSE,
  collinear_terms = as.list(collinear),
  warnings = as.list(warnings_seen),
  formula = paste(deparse(formula), collapse = " ")
)
jsonlite::write_json(
  result, file.path(output, "result.json"),
  auto_unbox = TRUE, pretty = TRUE, null = "null", na = "null", digits = 15
)
