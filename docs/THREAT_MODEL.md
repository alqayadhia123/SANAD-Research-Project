# SANAD Threat Model — Research PoC

**Version:** 0.1  
**Date:** 2026-10-30  
**System scope:** Driver identity protection baseline using Flask API and Keycloak OIDC introspection.  
**Classification:** Design analysis for a synthetic research prototype; not a security certification.

## 1. Security objectives

1. Protected API resources are not returned without a valid bearer token.
2. A token is accepted only when introspection confirms it is active and its issuer, audience, subject, and required scope meet the configured policy.
3. Authorization fails closed when the identity provider is unavailable or returns malformed data.
4. Tokens and synthetic API responses are not written to shared caches.
5. Prototype limitations are visible and cannot be mistaken for implemented WebAuthn, recovery, or vishing prevention.

## 2. Assets and security properties

| Asset | Security property | Current handling |
|---|---|---|
| Driver access token | Confidentiality, integrity, bounded input | Bearer header only; size limit; no application persistence |
| OIDC client secret | Confidentiality | Environment configuration; disposable CI values only |
| Identity-provider issuer and keys | Authenticity | Issuer claim checked against configured issuer; introspection over configured endpoint |
| Wallet and route API resources | Authorization | Synthetic responses behind bearer-token introspection and scope checks |
| Session/revocation state | Freshness | Delegated to live IdP introspection; timing and revocation semantics not yet measured |
| Audit evidence | Integrity and traceability | CI evidence retained; persistent tamper-evident application audit log not implemented |

## 3. Trust boundaries

- **Browser / driver client → Flask API:** untrusted client input and bearer token.
- **Flask API → Keycloak introspection endpoint:** authenticated service-to-service request using confidential-client credentials.
- **Keycloak → PostgreSQL:** identity-provider persistence boundary.
- **GitHub Actions → disposable lab stack:** isolated CI credentials and synthetic test identities.

The Compose network is intended for a local lab. Published API and Keycloak ports are bound to host loopback. This does not make the configuration production-ready.

## 4. Threats and current disposition

| Threat | Relevant control | Status |
|---|---|---|
| Missing or malformed bearer token | Strict Bearer parsing and HTTP 401 | Implemented; mocked tests |
| Token replay after expiry/revocation | Live introspection | Partial; live integration and revocation timing still require evidence |
| Token substitution across APIs | Exact audience check | Implemented; mocked tests; live token test pending |
| Issuer confusion | Exact issuer check | Implemented; mocked tests; live token test pending |
| Inactive token accepted | Require boolean `active == true` | Implemented; mocked tests |
| Scope escalation | Required scope subset check | Implemented; mocked tests; live no-scope test pending |
| IdP outage / malformed response | Fail-closed HTTP 503 | Implemented; mocked tests |
| Oversized token or request | Token and request size limits | Implemented; mocked tests |
| Credential or client-secret theft | Secret store, rotation, least privilege | Not established for production |
| Vishing / social engineering | No effective human verification or transaction approval implemented | Not mitigated by current API baseline |
| WebAuthn phishing / assertion replay | No real WebAuthn ceremony or challenge store | Not implemented |
| Recovery takeover | No secure recovery flow | Not implemented |
| Insider tampering / audit repudiation | No persistent tamper-evident audit store | Not implemented |

## 5. Explicit assumptions

- Keycloak is the authoritative identity provider for this PoC.
- The API's expected issuer, audience, client ID, client secret, and required scope are provisioned through a trusted deployment environment.
- Test users, wallet values, and route details are synthetic.
- The current API is not connected to real payment, transport dispatch, or production driver records.
- The current integration workflow uses a disposable confidential service client with the OAuth 2.0 Client Credentials grant. This validates service-to-service token introspection only; it does not validate an interactive driver login, passkey ceremony, or human authentication assurance.

## 6. Security acceptance criteria before expanding scope

- Complete live Keycloak/PostgreSQL/API integration on the current commit, with captured assertions for valid, missing, insufficient-scope, and invalid tokens.
- Verify missing, inactive, expired, wrong-issuer, wrong-audience, insufficient-scope, and invalid tokens against the live identity provider.
- Measure revocation propagation and document introspection cache behavior (if any).
- Implement and independently test WebAuthn registration/assertion, challenge single-use, origin/RP ID binding, signature validation, and replay rejection before claiming passkey protection.
- Design a recovery protocol with equivalent assurance, notification, rate limits, audit evidence, and factor-rotation safeguards.
- Add transaction-bound independent approval before claiming protection from vishing-assisted transaction authorization.
- Conduct independent security review and a pre-registered evaluation with reproducible scripts and retained evidence.

## 7. Research claim boundary

The current code demonstrates a fail-closed OIDC introspection authorization pattern for synthetic API resources. It does **not** demonstrate resistance to vishing, phishing, SIM swapping, account recovery attacks, or all forms of account takeover. Those are separate research hypotheses requiring implemented controls and controlled experiments.
