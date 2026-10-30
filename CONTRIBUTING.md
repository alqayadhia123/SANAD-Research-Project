# Contributing to SANAD

Thank you for contributing. SANAD is a research proof of concept; contributions must preserve that scope and must not overstate security properties.

## Before changing code

1. Open or review an issue describing the problem and proposed change.
2. Keep changes focused and explain security-relevant assumptions.
3. Never commit secrets, real driver information, access tokens, production URLs, or private keys.
4. Do not claim WebAuthn support unless registration and authentication ceremonies are implemented and verified end to end.

## Development setup

Use Python 3.10 or later.

```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
```

For the API container, see `transport_poc/docker-compose.transport.yaml` and copy `env.transport.example` to a local, untracked `env.transport` file. Replace every placeholder secret with a unique local value.

## Pull request requirements

- Include tests for behavior changes, especially authentication and authorization.
- Keep the API fail-closed when identity-provider validation is unavailable.
- Preserve TLS certificate verification; do not add `verify=False` or equivalent bypasses.
- Avoid logging credentials, bearer tokens, session identifiers, or client secrets.
- Update documentation and the changelog when behavior or configuration changes.
- Run `make check` and include the actual result in the pull request.
- Clearly label unimplemented functionality and synthetic data.

## Review

A passing unit-test suite is not a security certification. Changes affecting OIDC, Keycloak, WebAuthn, secrets, or deployment configuration require focused security review.
