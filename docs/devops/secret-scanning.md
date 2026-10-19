# Secret Scanning - Engineering Quality Gate V3

## Objective

Detect potentially exposed credentials before code is merged
into the AI Data Engineering PR Reviewer repository.

## Tool

- Gitleaks CLI, version 8.24.3
- GitHub Actions
- No paid services or license keys required

## Execution

The workflow runs on pull requests, pushes to main and
manual dispatch.

The scanner inspects the checked-out repository snapshot.

This initial implementation does not scan deleted secrets
in previous Git commits. Git history scanning is planned
as a separate control.

## Security controls

- GitHub token permission limited to contents: read
- Checkout credentials are not persisted
- Scanner output is suppressed
- Findings are redacted
- Raw reports remain in temporary runner storage
- No report artifacts are uploaded
- No findings are posted as public PR comments
- Only aggregate counts are shown

## Enforcement

- Exit code 0: no findings
- Exit code 1: potential secrets detected
- Other nonzero exit codes: scanner failure

Any nonzero exit code fails the job.

## Incident response

If a potential secret is identified:

1. Do not copy the secret into logs or PR comments.
2. Review the finding privately in a controlled environment.
3. Determine whether the credential is genuine.
4. If genuine, revoke or rotate the credential immediately.
5. Investigate exposure in Git history and external systems.
6. Remove exposed material and validate the remediation.

Deleting a secret from the latest commit does not
invalidate an already exposed credential.

## Limitations

- Secret scanners can produce false positives and false negatives.
- Snapshot scanning does not cover historical deleted secrets.
- This workflow protects this repository only.
- External repository scanning remains a separate architectural
  capability planned for the central reviewer.

## Future improvements

- Calibrated Git history scanning
- Scanner binary integrity verification
- Controlled negative testing
- Centralized scanner execution for external repositories
- Correlation of deterministic evidence with AI findings
## Binary integrity

The workflow downloads both the Gitleaks release archive and
the official checksum manifest from the same pinned release.

Before extraction or execution, it:

1. Locates the SHA-256 entry for the expected Linux artifact.
2. Rejects missing, duplicate or malformed checksum entries.
3. Calculates the SHA-256 of the downloaded archive.
4. Fails installation if the checksums differ.

Only verified archives are extracted.

This verifies consistency with the upstream release manifest.
It does not independently authenticate the publisher.

## Diagnostic safety

The scanner does not publish matching secrets, source lines
or raw finding reports.

A nonzero scanner exit code fails the workflow. Public
diagnostics remain generic to avoid exposing sensitive data.

Further diagnostics should use sanitized error categories
rather than printing unfiltered scanner output.