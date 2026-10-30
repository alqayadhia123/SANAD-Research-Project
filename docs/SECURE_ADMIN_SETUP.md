# Secure Admin Setup

Status: research-only deployment instructions. Production gate remains CLOSED.

## Identity
Use Keycloak as the only OIDC/OAuth2 identity provider. Human administrators must use Authorization Code with PKCE (S256), MFA, individual named accounts, HTTPS, and a dedicated realm role named sanad-admin. Machine clients must use separate confidential clients and least-privilege service accounts.

Use short-lived access tokens (target 5 minutes for the lab), exact issuer and audience validation, narrow scopes, and server-side introspection. Do not use password grant or implicit flow. Do not store bearer tokens in localStorage, source control, logs, or audit records.

## Bootstrap
Set the bootstrap username to sanad-admin in the private hosting secret store. Generate a unique random password of at least 32 characters with a password manager and set it only in the private secret store. Never commit or share it in chat. Sign in once, enroll MFA, create named administrator accounts and the sanad-admin role, verify recovery access, then disable or rotate the bootstrap account.

Create a separate confidential API client. Keep its client secret only in the API service's private environment. Do not embed confidential secrets in browser JavaScript.

## Tamper-evident audit and ledger
Use canonical audit events, SHA-256 hash chaining, and HMAC with a key held outside the database. The application writer must have insert/select privileges only and must not own the audit table. Periodically anchor only the chain-head digest, sequence and timestamp to an independently controlled ledger or timestamping service.

Never place passwords, access or refresh tokens, personal data, wallet balances, or raw event payloads on-chain. A hash chain is not independently tamper-evident if an administrator can rewrite the entire chain; protect its head externally. Blockchain anchoring is not implemented by this setup.

## Deployment gates
Require HTTPS, persistent Keycloak storage, production-mode Keycloak (not start-dev), MFA for all administrators, secret-manager configuration, live tests for expired and revoked tokens, wrong issuer/audience, insufficient scope, audit-chain verification, backup/restore and key rotation. Do not expose admin endpoints until RBAC, CSRF protection where applicable, rate limits and integration tests are implemented.

## Current boundary
The existing Flask API delegates bearer-token validation to Keycloak introspection. This document does not provision Keycloak, create a live administrator, configure hosting secrets, implement an admin UI, or deploy blockchain anchoring. Production gate remains CLOSED.
