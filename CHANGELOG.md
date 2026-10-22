# Changelog

## [3.4.3] - 2026-10-22

### Fixed
- Distinguish complete, partial and failed AI review outcomes.
- Report actual chunk coverage and interruption reason.
- Prevent partially analyzed pull requests from being logged as fully successful.
- Preserve publication of explicitly incomplete reviews.

### Tests
- Add regression tests for chunk limits and execution time budgets.
- Validate provider unavailability and lifecycle logging.

### Known limitations
- Reviews are not yet resumed across executions.
- Large pull requests may remain partially reviewed due to chunk and time limits.
