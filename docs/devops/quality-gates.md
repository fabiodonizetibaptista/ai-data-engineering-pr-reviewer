# Engineering Quality Gates

## Purpose

Introduce automated, reproducible quality controls for the
AI Data Engineering PR Reviewer.

These checks validate the reviewer project itself, not yet
the external repositories analyzed by the GitHub App.

## V1 - Ruff Diagnostic

Introduced in PR #5, initially in non-blocking mode.

## V2 - Coverage Measurement and Ruff Enforcement

### Static analysis

- Ruff version: 0.13.3.
- Preserve the current default rule selection.
- Lint violations now fail the Ruff job.
- Additional rule families require separate calibration.

### Test coverage

- pytest-cov version: 7.1.0.
- Coverage runs in the existing tests workflow.
- No minimum coverage threshold has been introduced.

### Local baseline

Measured on Windows with Python 3.13:

- 53 tests passed.
- 542 statements.
- 102 uncovered statements.
- 81% overall statement coverage.

This baseline has not yet been confirmed in Linux CI.

Priority modules for additional testing:

- src/providers/gemini.py: 50%.
- src/reviewer.py: 60%.
- src/providers/groq.py: 75%.
- src/providers/openrouter.py: 79%.

## Decisions

1. Reuse the existing pytest job.
2. Enforce only the already evaluated Ruff rules.
3. Measure coverage before setting a blocking threshold.
4. Preserve the existing GitHub App and Render architecture.
5. Use free tools without duplicating CI unnecessarily.
6. Treat coverage as evidence, not proof of correctness.

## Next steps

- Confirm Linux CI coverage.
- Expand provider and error-handling tests.
- Calibrate a minimum coverage threshold.
- Introduce DevSecOps tools incrementally.
