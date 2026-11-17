# Review of supplied `fido.py` before SANAD integration

Review date: 2026-11-17
Target repository: https://github.com/alqayadhia123/SANAD-Research-Project
Decision: do not copy this module directly into the current API.

## Compatibility finding

The supplied module is a Django/DRF integration. It imports Django settings, sessions, translation, timezone, DRF `ValidationError`, a Django `Passkey` model, and application-specific `common.utils`. The repository API inspected for this patch is Flask and currently has no matching Django project, DRF stack, `Passkey` model, or migrations. Directly copying this file would create unresolved imports and an unintegrated second web stack.

## Security and correctness findings in the supplied source

1. **RP ID derived from request metadata:** `get_server_id_from_request()` prefers `HTTP_REFERER`, falls back to `request.get_host()`, and returns `localhost` when the host is not allowlisted. The RP ID should be explicit deployment configuration, and request Origin must be checked against an exact trusted-origin allowlist. A Referer value must not select the WebAuthn RP ID.
2. **Inactive credentials are included at registration start:** `get_user_credentials()` queries a user’s Passkeys without filtering `is_active=True`. Inactive credentials should not be offered in `allowCredentials`.
3. **Authenticated-user binding is not explicit at completion:** `auth_complete()` looks up an active credential globally by credential ID. When the request already has an authenticated user (for example, MFA), the code shown does not explicitly assert that `key.user_id == request.user.id` before accepting the assertion. Add this check for non-discoverable/MFA flows.
4. **User-Agent provider inference:** `get_current_platform()` maps User-Agent strings to labels such as Apple, Google, or Microsoft. This is not proof of authenticator identity and must be treated as display metadata only.
5. **Broad exception suppression:** the bare `except: pass` around `webauthn_json_mapping.enabled` hides all initialization errors. Catch the expected exception(s), log a sanitized diagnostic, and fail closed if the required serialization behavior is unavailable.
6. **Request payload assumptions:** `auth_complete()` expects `request.data["passkeys"]` to be a JSON string and calls `json.loads()` without explicit schema/type validation. Validate a structured credential object and return controlled client errors for malformed input.
7. **Credential uniqueness and lifecycle:** registration should enforce a unique credential ID, prevent accidental duplicate registration, filter revoked credentials, and define re-registration/recovery behavior. The supplied snippet does not show those controls.
8. **Counter and audit lifecycle:** the shown completion path updates `date_last_used` but does not visibly persist authenticator counter state or emit a security audit event. Verify counter handling against the exact python-fido2 version and add auditable events for registration, authentication, revocation, and recovery.
9. **Session and CSRF dependencies:** challenges are stored in the Django session. The surrounding application must use secure, HttpOnly, SameSite cookies, CSRF protection for state-changing requests, HTTPS, and bounded challenge lifetime. These controls are not demonstrated in this module.

## Recommended SANAD integration approach

- Keep the existing Flask API and Keycloak as the identity provider; do not introduce Django solely to reuse this file.
- Prefer Keycloak-native WebAuthn/Passkeys for the SANAD login flow so that registration, authentication, credential lifecycle, and OIDC issuance remain under one IAM authority.
- If a direct python-fido2 service is later justified, port the flow deliberately into Flask with a persistent credential store, explicit RP ID and Origin allowlists, one-time expiring challenges, user/session binding, credential revocation, counter policy, CSRF/session controls, and a complete browser ceremony.
- Keep authenticator enrollment unavailable until an end-to-end implementation and negative tests pass.

## Evidence boundary

This is a static review of the supplied 167-line Django-oriented `fido.py` source. No runtime, dependency-version, Django settings, model, or browser test was available from that file alone. Findings above are limited to behavior visible in the supplied source and should be reconciled with the full application before claiming exploitability.