# SANAD — Secure Identity & Mobility Trust

**Project owner / maintainer:** [Aboraed Alqayadhi](https://github.com/alqayadhia123)  
**GitHub account:** [@alqayadhia123](https://github.com/alqayadhia123)  
**Repository:** [alqayadhia123/SANAD-Research-Project](https://github.com/alqayadhia123/SANAD-Research-Project)

## Project overview

SANAD is an early-stage security-focused project exploring trusted digital identity and safer operations for driver and mobility services. Its current proof of concept includes a FastAPI service, Keycloak-based token introspection and authorization checks, containerized development services, and automated security tests.

The mobility-oriented direction, branded **SANAD Mobility**, is to explore stronger driver identity assurance and protection against impersonation and social-engineering attacks in transport workflows.

## Current implementation status

- Implemented: initial API proof of concept, Keycloak token validation and scope checks, baseline HTTP security controls, request/response size limits, and automated Python tests.
- Verified in CI: Python test suite and container build/health smoke test (see the linked GitHub Actions runs in the project pull request).
- Not yet verified: successful live end-to-end integration of Keycloak, PostgreSQL, and the API. The latest integration attempt stopped while waiting for Keycloak readiness.
- Not yet implemented or demonstrated as complete: production WebAuthn enrollment, account recovery, full transport operations, AI fraud-detection model, IoT integration, and field deployment.

## Development and verification

The active hardening work is being conducted on the branch:

`fix/sanad-p0-security-baseline`

The related pull request is [PR #4](https://github.com/alqayadhia123/SANAD-Research-Project/pull/4). It remains a Draft pull request; the default branch has not been merged with this work.

**Production gate:** CLOSED. This repository currently represents a development proof of concept, not a production-ready transport security platform.

## Contact and project ownership

For project ownership and source history, refer to the GitHub account [@alqayadhia123](https://github.com/alqayadhia123) and the commit history of this repository.
