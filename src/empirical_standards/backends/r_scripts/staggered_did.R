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

data[[spec$treatment_time]][is.na(data[[spec$treatment_time]])] <- 0
xformla <- if (length(spec$controls) == 0) NULL else {
  as.formula(paste("~", paste(spec$controls, collapse = " + ")))
}
set.seed(spec$random_state)
model <- capture_warnings(did::att_gt(
  yname = spec$outcome,
  tname = spec$time,
  idname = spec$entity,
  gname = spec$treatment_time,
  xformla = xformla,
  data = data,
  panel = TRUE,
  allow_unbalanced_panel = spec$allow_unbalanced_panel,
  control_group = spec$control_group,
  anticipation = spec$anticipation,
  alp = 1 - spec$confidence_level,
  bstrap = spec$bootstrap,
  cband = spec$simultaneous_band,
  biters = spec$bootstrap_reps,
  clustervars = spec$entity,
  est_method = spec$est_method,
  base_period = spec$base_period,
  print_details = FALSE
))

point_critical <- stats::qnorm(0.5 + spec$confidence_level / 2)
group_time <- data.frame(
  cohort = model$group,
  time = model$t,
  event_time = model$t - model$group,
  att = model$att,
  std_error = model$se
)
group_time$conf_low <- group_time$att - point_critical * group_time$std_error
group_time$conf_high <- group_time$att + point_critical * group_time$std_error
group_time$simultaneous_conf_low <- group_time$att - model$c * group_time$std_error
group_time$simultaneous_conf_high <- group_time$att + model$c * group_time$std_error
group_time$identified <- is.finite(group_time$att) & is.finite(group_time$std_error)

cohorts <- sort(unique(data[[spec$treatment_time]][data[[spec$treatment_time]] > 0]))
cohort_sizes <- vapply(cohorts, function(g) {
  length(unique(data[[spec$entity]][data[[spec$treatment_time]] == g]))
}, numeric(1))
support <- group_time[, c("cohort", "time", "event_time", "identified")]
support$treated_entities <- cohort_sizes[match(support$cohort, cohorts)]
support$control_entities <- vapply(seq_len(nrow(support)), function(i) {
  period <- support$time[[i]]
  eligible <- if (spec$control_group == "nevertreated") {
    data[[spec$treatment_time]] == 0
  } else {
    data[[spec$treatment_time]] == 0 | data[[spec$treatment_time]] > period + spec$anticipation
  }
  eligible <- eligible & data[[spec$treatment_time]] != support$cohort[[i]]
  length(unique(data[[spec$entity]][eligible & data[[spec$time]] == period]))
}, numeric(1))

aggregate_one <- function(type, key_name) {
  args <- list(
    MP = model,
    type = type,
    na.rm = TRUE,
    bstrap = spec$bootstrap,
    biters = spec$bootstrap_reps,
    cband = spec$simultaneous_band,
    alp = 1 - spec$confidence_level
  )
  if (type == "dynamic") {
    if (!is.null(spec$balance_event_time)) args$balance_e <- spec$balance_event_time
    if (!is.null(spec$min_event_time)) args$min_e <- spec$min_event_time
    if (!is.null(spec$max_event_time)) args$max_e <- spec$max_event_time
  }
  result <- capture_warnings(do.call(did::aggte, args))
  table <- data.frame(
    index = result$egt,
    att = result$att.egt,
    std_error = result$se.egt
  )
  names(table)[1] <- key_name
  table$conf_low <- table$att - point_critical * table$std_error
  table$conf_high <- table$att + point_critical * table$std_error
  table$simultaneous_conf_low <- table$att - result$crit.val.egt * table$std_error
  table$simultaneous_conf_high <- table$att + result$crit.val.egt * table$std_error
  list(result = result, table = table)
}

dynamic <- aggregate_one("dynamic", "event_time")
group <- aggregate_one("group", "cohort")
calendar <- aggregate_one("calendar", "time")
simple <- capture_warnings(did::aggte(
  model, type = "simple", na.rm = TRUE, bstrap = spec$bootstrap,
  biters = spec$bootstrap_reps, cband = spec$simultaneous_band,
  alp = 1 - spec$confidence_level
))

identified <- merge(
  group_time[group_time$identified, c("cohort", "time", "event_time")],
  data.frame(cohort = cohorts, cohort_size = cohort_sizes),
  by = "cohort"
)
event_weights <- identified
if (!is.null(spec$min_event_time)) {
  event_weights <- event_weights[event_weights$event_time >= spec$min_event_time, ]
}
if (!is.null(spec$max_event_time)) {
  event_weights <- event_weights[event_weights$event_time <= spec$max_event_time, ]
}
if (!is.null(spec$balance_event_time)) {
  maximum_exposure <- aggregate(event_time ~ cohort, identified, max)
  balanced_cohorts <- maximum_exposure$cohort[
    maximum_exposure$event_time >= spec$balance_event_time
  ]
  event_weights <- event_weights[event_weights$cohort %in% balanced_cohorts, ]
}
event_weights$weight <- ave(
  event_weights$cohort_size, event_weights$event_time,
  FUN = function(x) x / sum(x)
)
event_weights$aggregation <- "dynamic"
simple_weights <- identified[identified$event_time >= 0, ]
simple_weights$weight <- simple_weights$cohort_size / sum(simple_weights$cohort_size)
simple_weights$aggregation <- "simple"
aggregation_weights <- rbind(
  event_weights[, c("aggregation", "cohort", "time", "event_time", "cohort_size", "weight")],
  simple_weights[, c("aggregation", "cohort", "time", "event_time", "cohort_size", "weight")]
)

write.csv(group_time, file.path(output, "group_time.csv"), row.names = FALSE)
write.csv(dynamic$table, file.path(output, "event_time.csv"), row.names = FALSE)
write.csv(group$table, file.path(output, "cohort.csv"), row.names = FALSE)
write.csv(calendar$table, file.path(output, "calendar_time.csv"), row.names = FALSE)
write.csv(support, file.path(output, "support.csv"), row.names = FALSE)
write.csv(aggregation_weights, file.path(output, "aggregation_weights.csv"), row.names = FALSE)

result <- list(
  estimator = "callaway_santanna_att_gt",
  backend = "R",
  package = "did",
  nobs_input = nrow(data),
  n_entities_input = length(unique(data[[spec$entity]])),
  overall_att = unname(simple$overall.att),
  overall_std_error = unname(simple$overall.se),
  overall_conf_low = unname(simple$overall.att - point_critical * simple$overall.se),
  overall_conf_high = unname(simple$overall.att + point_critical * simple$overall.se),
  dynamic_overall_att = unname(dynamic$result$overall.att),
  dynamic_overall_std_error = unname(dynamic$result$overall.se),
  pretrend_statistic = as.numeric(model$W),
  pretrend_p_value = as.numeric(model$Wpval),
  group_time_critical_value = unname(model$c),
  dynamic_critical_value = unname(dynamic$result$crit.val.egt),
  control_group = spec$control_group,
  est_method = spec$est_method,
  base_period = spec$base_period,
  anticipation = spec$anticipation,
  confidence_level = spec$confidence_level,
  bootstrap = spec$bootstrap,
  bootstrap_reps = spec$bootstrap_reps,
  simultaneous_band = spec$simultaneous_band,
  warnings = as.list(warnings_seen)
)
jsonlite::write_json(
  result, file.path(output, "result.json"),
  auto_unbox = TRUE, pretty = TRUE, null = "null", na = "null", digits = 15
)
