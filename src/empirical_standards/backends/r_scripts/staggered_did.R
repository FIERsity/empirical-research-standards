args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("expected input.csv specification.json output_directory")
data <- read.csv(args[[1]], check.names = FALSE)
spec <- jsonlite::fromJSON(args[[2]], simplifyVector = TRUE)
output <- args[[3]]
data[[spec$treatment_time]][is.na(data[[spec$treatment_time]])] <- 0
xformla <- if (length(spec$controls) == 0) NULL else as.formula(paste("~", paste(spec$controls, collapse = " + ")))
set.seed(spec$random_state)
model <- did::att_gt(yname=spec$outcome, tname=spec$time, idname=spec$entity,
  gname=spec$treatment_time, xformla=xformla, data=data, panel=TRUE,
  allow_unbalanced_panel=spec$allow_unbalanced_panel, control_group=spec$control_group,
  anticipation=spec$anticipation, bstrap=spec$bootstrap, cband=spec$simultaneous_band,
  biters=spec$bootstrap_reps, clustervars=spec$entity, est_method=spec$est_method,
  base_period=spec$base_period, print_details=FALSE)
group_time <- data.frame(cohort=model$group, time=model$t, att=model$att, std_error=model$se)
dynamic <- did::aggte(model, type="dynamic", na.rm=TRUE)
event_time <- data.frame(event_time=dynamic$egt, att=dynamic$att.egt, std_error=dynamic$se.egt)
simple <- did::aggte(model, type="simple", na.rm=TRUE)
write.csv(group_time, file.path(output, "group_time.csv"), row.names=FALSE)
write.csv(event_time, file.path(output, "event_time.csv"), row.names=FALSE)
jsonlite::write_json(list(estimator="callaway_santanna_att_gt", backend="R", package="did",
  nobs=nrow(data), overall_att=unname(simple$overall.att), overall_std_error=unname(simple$overall.se),
  control_group=spec$control_group, est_method=spec$est_method, base_period=spec$base_period,
  anticipation=spec$anticipation, bootstrap=spec$bootstrap, bootstrap_reps=spec$bootstrap_reps,
  simultaneous_band=spec$simultaneous_band), file.path(output, "result.json"), auto_unbox=TRUE, pretty=TRUE)
