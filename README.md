# SANAD — Secure Identity & Mobility Trust

**Project owner / maintainer:** [Aboraed Alqayadhi](https://github.com/alqayadhia123)  
**GitHub account:** [@alqayadhia123](https://github.com/alqayadhia123)  
**Repository:** [alqayadhia123/SANAD-Research-Project](https://github.com/alqayadhia123/SANAD-Research-Project)

## Project overview

SANAD is an early-stage research proof of concept exploring trusted digital identity and safer operations for driver and mobility services. The current implementation is a **Flask API** with Keycloak OIDC token introspection and scope-based authorization, containerized lab services, and automated tests.

The mobility-oriented direction, branded **SANAD Mobility**, is to explore stronger driver identity assurance and protection against impersonation and social-engineering attacks in transport workflows. These are research objectives, not capabilities already demonstrated by the current prototype.

## Current implementation status

- **Implemented:** Flask application factory, fail-closed Keycloak introspection baseline, issuer/audience/subject/scope checks, request and token size limits, baseline HTTP security headers, synthetic wallet/route endpoints, and a mocked pytest suite.
- **Verified in CI:** 30 Python tests passed on commit `f57b0584dbd9329e1806e6d91293035a0e4e429f`; container build and `/health` smoke test passed on the same commit.
- **Live integration:** The revised workflow now waits for the Keycloak OIDC discovery endpoint rather than the root path. Its current run must pass before live Keycloak integration can be considered verified.
- **Not implemented or demonstrated:** real WebAuthn registration/assertion, secure account recovery, independent transaction approval, persistent tamper-evident audit logging, measured revocation latency, AI fraud detection, IoT integration, and field deployment.

## Architecture and verification documents

- [Remediation status and validation record](docs/REMEDIATION_STATUS.md)
- [Verification plan and evidence register](docs/VERIFICATION_PLAN.md)
- [Threat model and research claim boundaries](docs/THREAT_MODEL.md)
- [Transport PoC operating notes](transport_poc/README.md)

## Development and verification

The active hardening work is being conducted on:

`fix/sanad-p0-security-baseline`

The related pull request is [PR #4](https://github.com/alqayadhia123/SANAD-Research-Project). It remains a Draft pull request; the default branch has not been merged with this work.

**Production gate: CLOSED.** This repository currently represents a research development proof of concept, not a production-ready transport security platform. A passing unit suite or container health check is not evidence of resistance to vishing or account takeover.

## Contact and project ownership

For project ownership and source history, refer to [@alqayadhia123](https://github.com/alqayadhia123) and the repository commit history.
