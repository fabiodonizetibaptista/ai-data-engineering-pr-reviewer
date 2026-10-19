# Workflow Validation - Engineering Quality Gate V3.3

## Objective

Prevent regressions in GitHub Actions workflows and
embedded shell scripts.

## Background

During PR #7, a PowerShell-generated change accidentally
placed a Bash `if` command on the same line as a comment.

Python unit tests and Ruff passed, but the GitHub Actions
security job failed during execution.

## Tools

- actionlint v1.7.12
- ShellCheck available on the GitHub-hosted Ubuntu runner
- SHA-256 verification for the downloaded actionlint artifact

## Architecture

The validation runs as a separate job inside the existing
Engineering Quality Gate workflow.

actionlint analyzes GitHub Actions workflow definitions.
Its ShellCheck integration analyzes embedded Bash scripts.

The job runs on pull requests and manual dispatch,
according to the existing workflow triggers.

## Enforcement

Any actionlint or ShellCheck finding that causes a nonzero
exit status fails the validation job.

No blanket rule suppression is introduced.

## Regression test

A temporary, deliberately malformed workflow reproduces
the failure pattern observed in PR #7.

The test succeeds only when actionlint rejects it.

The temporary file is not committed or uploaded.

## Limitations

Static validation cannot establish that external downloads,
API calls or services will succeed at runtime.

CI checks are complementary to tests and operational monitoring.

## Follow-up

- Review findings and calibrate rules if necessary.
- Add validation of executable shell behavior where warranted.
- Continue DevSecOps with dependency and container scanning.
