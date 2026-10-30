# SANAD Research Evidence Register

**Purpose:** preserve reproducible, auditable evidence for the SANAD security PoC without paid hosting.
**Current status:** template only; no experiment outcomes are implied by this document.
**Data rule:** synthetic identities and test credentials only. Never attach bearer tokens, client secrets, personal data, or unredacted environment files.

## 1. Evidence classes

| Class | Meaning | Permitted claim |
|---|---|---|
| CI_UNIT | Automated tests with mocks | Code-path behavior under controlled mocked responses |
| CI_CONTAINER | Compose parsing, image build, API health smoke test | Container/configuration and basic process health only |
| CI_LIVE_IDP | Disposable Keycloak + PostgreSQL + API integration | Only the exact live assertions shown in the run log |
| MANUAL_SECURITY | Human-executed protocol/security test | Only the documented procedure and observed outcome |
| BLOCKED | Test cannot be executed because required capability is absent | No efficacy claim |

## 2. Required evidence record

Every executed test must record:
- evidence_id and scenario_id;
- tested Git commit SHA and workflow run URL (or manual operator and environment);
- UTC start/end timestamps;
- exact preconditions, steps, expected result, actual result;
- status: PASS, FAIL, BLOCKED, or NOT_RUN;
- artifact reference and SHA-256 checksum where an artifact exists;
- limitations, deviations, and reviewer.

A green workflow badge is not a substitute for the underlying run, job, and relevant assertion logs. Do not mark an entire scenario PASS if only a subset of its assertions ran.

## 3. Evidence integrity and retention

1. Keep CI logs and downloadable artifacts attached to the corresponding GitHub Actions run.
2. Export only redacted logs and synthetic test reports. Never export .env, token values, authorization headers, client secrets, or raw database dumps.
3. Record SHA-256 for every downloaded evidence artifact and preserve the original filename.
4. Store manual evidence under a versioned evidence/ directory only after review; include a README describing provenance.
5. Do not edit a captured original. If redaction is needed, preserve the original only in a restricted local location and publish the redacted derivative with a note.
6. Link evidence to the exact tested commit; evidence from an earlier SHA must not be represented as validation of a later SHA.

## 4. Initial evidence register

| Evidence ID | Scenario / scope | Evidence class | Status | Required artifact |
|---|---|---|---|---|
| EV-CI-UNIT-001 | Flask mocked authorization suite | CI_UNIT | Await current run record | Actions job log + test summary |
| EV-CI-CONT-001 | Compose config and API image smoke test | CI_CONTAINER | Await current run record | Actions job log |
| EV-CI-LIVE-001 | Keycloak/PostgreSQL/API live integration | CI_LIVE_IDP | In progress / verify run | Full job log + assertion output |
| EV-MAN-REV-001 | Revocation propagation timing | MANUAL_SECURITY | NOT_RUN | timestamped repeated request log |
| EV-MAN-WA-001 | WebAuthn registration/assertion/replay | MANUAL_SECURITY | BLOCKED | Requires real WebAuthn implementation |
| EV-MAN-REC-001 | Secure account recovery | MANUAL_SECURITY | BLOCKED | Requires recovery protocol implementation |
| EV-MAN-TXN-001 | Transaction-bound independent approval | MANUAL_SECURITY | BLOCKED | Requires transaction authorization implementation |

Update statuses only from captured evidence. BLOCKED is not a failure rate and must not be included in denominators for efficacy calculations.

## 5. Research reporting rules

- Report counts by status separately: PASS, FAIL, BLOCKED, NOT_RUN.
- For a measured success rate, define the eligible denominator before execution and exclude BLOCKED/NOT_RUN from that denominator; disclose exclusions.
- Do not infer causal reduction in phishing, vishing, or account takeover from mocked tests, API health, or OIDC token acceptance.
- Report revocation as a distribution (median, p95, maximum, sample count) only after repeated timed trials with synchronized clocks and a defined event origin.
- Preserve negative results and failed runs; do not overwrite them with a later successful rerun.

## 6. Free workflow

Use local Docker Compose for repeatable integration and GitHub Actions for automated evidence. This avoids paid hosting but does not guarantee a public 24/7 endpoint. CI quotas and artifact-retention policies remain subject to GitHub plan and repository settings.