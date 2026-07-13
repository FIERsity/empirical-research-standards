# Contributing

Keep contributions small and auditable. Before adding an estimator, document its estimand,
sample rules, defaults, covariance convention, failure modes, and planned Python-R comparison.
Apply `docs/backend_policy.md` before implementation. If a mature R reference exists and a
faithful Python implementation would require substantial specialist inference code, build a
version-locked R backend instead. Python purity is not an acceptance criterion; correctness,
transparency, maintainability, and a stable cross-language result contract are.

Run the complete local check before opening a pull request:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
uv run python /Users/sanclodymm/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/apply-empirical-standards
uv run python skills/apply-empirical-standards/scripts/check_environment.py
```

New behavior requires focused tests and a runnable example. Avoid generic base classes or
configuration layers until at least two implemented modules demonstrate the same need.

Treat the Agent Skill as a versioned public interface. Update its method map and API patterns
when estimator names, arguments, limitations, or verification status change. Keep `SKILL.md`
concise and put method-specific detail in directly linked references.

Keep the root README bilingual in this fixed order: complete English first, then concise
Chinese. Every substantive English change must be reflected in Chinese in the same pull
request, including capabilities, commands, defaults, limitations, risk notes, verification
status, and roadmap changes. Chinese wording may be shorter but must not omit technical detail.
