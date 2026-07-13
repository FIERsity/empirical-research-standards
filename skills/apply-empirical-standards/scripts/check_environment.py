#!/usr/bin/env python3
"""Check that a checkout exposes the APIs required by the project skill."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

REQUIRED_APIS = (
    "fit_ols",
    "fit_fixed_effects",
    "fit_did",
    "fit_event_study",
    "fit_staggered_did",
    "fit_sun_abraham",
    "fit_iv_2sls",
    "fit_panel_iv_2sls",
    "anderson_rubin_test",
    "anderson_rubin_confidence_set",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Optional python-empirical-standards checkout containing src/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.project_root is not None:
        source = args.project_root.expanduser().resolve() / "src"
        if not source.is_dir():
            print(f"ERROR: source directory not found: {source}", file=sys.stderr)
            return 2
        sys.path.insert(0, str(source))

    try:
        package = importlib.import_module("empirical_standards")
    except ImportError as error:
        print(f"ERROR: cannot import empirical_standards: {error}", file=sys.stderr)
        return 1

    missing = [name for name in REQUIRED_APIS if not hasattr(package, name)]
    version = getattr(package, "__version__", "unknown")
    print(f"empirical_standards version: {version}")
    print(f"python version: {sys.version.split()[0]}")
    if missing:
        print(f"ERROR: missing required APIs: {', '.join(missing)}", file=sys.stderr)
        return 1
    print(f"required APIs: OK ({len(REQUIRED_APIS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
