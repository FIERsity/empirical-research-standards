args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("expected input.csv specification.json output_directory")
data <- read.csv(args[[1]], check.names = FALSE)
spec <- jsonlite::fromJSON(args[[2]], simplifyVector = TRUE)
output <- args[[3]]
never_value <- max(data[[spec$time]], na.rm=TRUE) + 10000
data[[spec$treatment_time]][is.na(data[[spec$treatment_time]])] <- never_value
rhs <- c(spec$controls, sprintf("sunab(%s, %s, ref.p=%s)", spec$treatment_time, spec$time, spec$reference_period))
formula <- as.formula(sprintf("%s ~ %s | %s + %s", spec$outcome, paste(rhs, collapse=" + "), spec$entity, spec$time))
model <- fixest::feols(formula, data=data, vcov=as.formula(paste("~", spec$cluster)))
dynamic <- summary(model, agg="period")$coeftable
keep <- grepl(paste0("^", spec$time, "::"), rownames(dynamic))
dynamic <- dynamic[keep, , drop=FALSE]
event_time <- data.frame(event_time=as.numeric(sub(".*::", "", rownames(dynamic))),
  term=rownames(dynamic), estimate=as.numeric(dynamic[, "Estimate"]),
  std_error=as.numeric(dynamic[, "Std. Error"]), statistic=as.numeric(dynamic[, "t value"]),
  p_value=as.numeric(dynamic[, "Pr(>|t|)"]))
write.csv(event_time, file.path(output, "event_time.csv"), row.names=FALSE)
jsonlite::write_json(list(estimator="sun_abraham_fixest", backend="R", package="fixest",
  nobs=stats::nobs(model), reference_period=spec$reference_period, cluster=spec$cluster,
  fixed_effects=c(spec$entity, spec$time)), file.path(output, "result.json"), auto_unbox=TRUE, pretty=TRUE)
