"""Optional computational backends."""

from empirical_standards.backends.r import RBackendEnvironment, check_r_environment, run_r_backend

__all__ = ["RBackendEnvironment", "check_r_environment", "run_r_backend"]
