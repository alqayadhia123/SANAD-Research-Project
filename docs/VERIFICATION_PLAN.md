# SANAD Verification Plan and Evidence Register

## Purpose

This document separates source-level tests, mocked authorization tests, live identity-provider integration, and security research experiments. These evidence classes are not interchangeable.

## Verification layers

| Layer | What it verifies | Evidence required | What it does not prove |
|---|---|---|---|
| Static | Python syntax and configuration structure | CI log and exit status | Runtime correctness |
| Unit / mocked | Authorization decisions for controlled introspection responses | Pytest report, test count, commit SHA | Real Keycloak behavior |
| Container smoke | Image builds and API process answers health check | Build log and HTTP response | Identity-provider connectivity |
| Live integration | PostgreSQL + Keycloak + API, real issued tokens and introspection | Full workflow log, realm setup, observed HTTP statuses | WebAuthn, recovery, OOB approval |
| Security experiment | Attack outcomes under a pre-registered protocol | Dataset, scripts, repetitions, denominator, analysis | Generalization beyond tested scope |

## Current automated test assertions

- Missing bearer token: HTTP 401.
- Inactive, malformed, wrong-audience, wrong-issuer, missing-issuer, or missing-subject token: deny.
- Insufficient or malformed wallet scope: HTTP 403.
- Introspection outage, missing client secret, oversized response, or malformed JSON: fail closed with HTTP 503.
- Oversized bearer token: HTTP 401.
- Oversized declared request body: HTTP 413.
- Protected route and wallet endpoints: deny unauthenticated access; allow only valid mocked claims.
- Authenticator enrollment: HTTP 401 without authorization and HTTP 501 after authorization until a real secure enrollment ceremony is implemented.
- API responses: no-store cache policy and baseline security headers.
- Introspection transport: POST, HTTP Basic client authentication, form-encoded token, and bounded timeout.

## Live integration acceptance criteria

A live integration run is accepted only when the same workflow run demonstrates all of the following:

1. PostgreSQL becomes healthy.
2. Keycloak OIDC discovery returns HTTP 200 and a valid discovery document.
3. The disposable realm, confidential client, audience mapper, wallet scope, and test user are provisioned successfully.
4. The API health endpoint responds.
5. A request without a bearer token returns 401.
6. An active token without the required scope returns 403.
7. A correctly scoped token issued by the disposable Keycloak realm returns 200 and only synthetic data.
8. An invalid token returns 401.
9. The workflow cleans up containers, volumes, and its temporary environment file even on failure.

A failed or skipped step means the downstream acceptance criteria were not tested.

## Research scenarios not yet demonstrated

| Scenario | Current evidence state | Required future evidence |
|---|---|---|
| Token/session revocation | NOT RUN | Revoke session/token at Keycloak, measure introspection decision and latency over repeated requests |
| WebAuthn registration/assertion | BLOCKED | Real browser/authenticator ceremony, server-side challenge storage, origin/RP ID validation, signature and counter checks |
| Assertion replay | BLOCKED | Re-submit consumed challenge/assertion and retain rejection evidence |
| Independent transaction approval | BLOCKED | Separate authenticated channel, transaction binding, expiry, replay protection |
| Account recovery | BLOCKED | Recovery threat model, factor replacement controls, notification, audit trail, negative tests |
| Vishing resistance | NOT EVALUATED | Ethics-approved, pre-registered controlled study with attack scripts, participant safeguards, denominator, and repeatable scoring |

## Result recording policy

For every executed scenario, record:

- Exact commit SHA and workflow/run URL.
- Test or scenario ID.
- Environment and dependency versions.
- Preconditions and test data classification.
- Exact command or request.
- Expected result and observed result.
- Exit code / HTTP status.
- Artifact or log reference.
- Tester and execution timestamp.

Use only `PASS`, `FAIL`, `NOT RUN`, or `BLOCKED`. Never infer a result from a workflow badge, file existence, or a planned test.
