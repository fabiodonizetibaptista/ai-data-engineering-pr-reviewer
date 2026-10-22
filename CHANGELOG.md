# Changelog

## [3.4.4] - 2026-10-22

### Changed
- Prioritize executable code, data pipelines and infrastructure when a large PR exceeds the configured chunk limit.
- Preserve original diff order when full coverage is possible.
- Retain explicit reporting of omitted chunks and review coverage.
- Keep the existing maximum number of LLM calls per execution.

### Tests
- Add regression tests for technical-file prioritization and original-order preservation.

### Known limitations
- Prioritization does not guarantee complete review coverage.
- Review results are not yet persisted or resumed across executions.
- Provider quotas and execution time budgets remain applicable.

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
