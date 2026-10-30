import json

import app as api


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        raw = (
            self.payload
            if isinstance(self.payload, bytes)
            else json.dumps(self.payload).encode("utf-8")
        )
        return raw if size < 0 else raw[:size]


def make_client(monkeypatch, payload=None, raises=None):
    config = {
        "TESTING": True,
        "OIDC_CLIENT_ID": "driver-wallet-api",
        "OIDC_CLIENT_SECRET": "test-secret",
        "EXPECTED_AUDIENCE": "driver-wallet-api",
        "REQUIRED_WALLET_SCOPE": "wallet:read",
        "KEYCLOAK_ISSUER": "https://idp.example/realms/sanad-lab",
    }
    client = api.create_app(config).test_client()

    def fake_urlopen(*args, **kwargs):
        if raises:
            raise raises
        return FakeResponse(payload)

    monkeypatch.setattr(api, "urlopen", fake_urlopen)
    return client


def active_payload(**overrides):
    payload = {
        "active": True,
        "sub": "synthetic-user-001",
        "preferred_username": "synthetic-driver",
        "aud": ["driver-wallet-api"],
        "scope": "openid wallet:read",
        "iss": "https://idp.example/realms/sanad-lab",
    }
    payload.update(overrides)
    return payload


def test_health_is_public_and_synthetic():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["data_classification"] == "synthetic"


def test_wallet_rejects_missing_bearer():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/api/driver/wallet")
    assert response.status_code == 401
    assert response.get_json()["error"] == "bearer_token_required"


def test_wallet_returns_503_when_introspection_not_configured():
    client = api.create_app({"TESTING": True, "OIDC_CLIENT_SECRET": ""}).test_client()
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer dummy"})
    assert response.status_code == 503


def test_wallet_accepts_valid_introspection(monkeypatch):
    client = make_client(monkeypatch, active_payload())
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    assert response.get_json()["synthetic_data"] is True


def test_wallet_rejects_inactive_token(monkeypatch):
    client = make_client(monkeypatch, active_payload(active=False))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_rejects_wrong_audience(monkeypatch):
    client = make_client(monkeypatch, active_payload(aud=["another-api"]))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_rejects_missing_audience(monkeypatch):
    client = make_client(monkeypatch, active_payload(aud=[]))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_rejects_wrong_issuer_when_present(monkeypatch):
    client = make_client(monkeypatch, active_payload(iss="https://evil.example/realm"))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_rejects_missing_subject(monkeypatch):
    client = make_client(monkeypatch, active_payload(sub=None))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_requires_scope(monkeypatch):
    client = make_client(monkeypatch, active_payload(scope="openid profile"))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403


def test_introspection_outage_fails_closed(monkeypatch):
    client = make_client(monkeypatch, raises=OSError("simulated network failure"))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 503


def test_enrollment_requires_authorization(monkeypatch):
    client = api.create_app({"TESTING": True}).test_client()
    response = client.post("/api/driver/enroll-authenticator", json={
        "authenticator_id": "attacker-controlled"
    })
    assert response.status_code == 401


def test_enrollment_is_explicitly_not_implemented_after_auth(monkeypatch):
    client = make_client(monkeypatch, active_payload())
    response = client.post(
        "/api/driver/enroll-authenticator",
        json={"authenticator_id": "attacker-controlled"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 501
    assert response.get_json()["error"] == "not_implemented"

def test_wallet_rejects_missing_issuer(monkeypatch):
    payload = active_payload()
    payload.pop("iss")
    client = make_client(monkeypatch, payload)
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_rejects_non_string_scope(monkeypatch):
    client = make_client(monkeypatch, active_payload(scope=["wallet:read"]))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403


def test_wallet_rejects_oversized_bearer_token():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer " + ("x" * 8193)})
    assert response.status_code == 401
    assert response.get_json()["error"] == "bearer_token_too_large"


def test_api_responses_are_not_cached_and_have_security_headers(monkeypatch):
    client = make_client(monkeypatch, active_payload())
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_health_has_security_headers():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_oversized_introspection_response_returns_503(monkeypatch):
    client = make_client(monkeypatch, b"x" * 65537)
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 503
    assert response.get_json()["error"] == "introspection_response_too_large"


def test_malformed_introspection_json_returns_503(monkeypatch):
    client = make_client(monkeypatch, b"{not-json")
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 503
    assert response.get_json()["error"] == "introspection_unavailable"


def test_wallet_rejects_non_list_audience(monkeypatch):
    client = make_client(monkeypatch, active_payload(aud={"driver-wallet-api": True}))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_wallet_rejects_empty_required_scope_configuration(monkeypatch):
    client = api.create_app({
        "TESTING": True,
        "OIDC_CLIENT_ID": "driver-wallet-api",
        "OIDC_CLIENT_SECRET": "test-secret",
        "EXPECTED_AUDIENCE": "driver-wallet-api",
        "REQUIRED_WALLET_SCOPE": "",
        "KEYCLOAK_ISSUER": "https://idp.example/realms/sanad-lab",
    }).test_client()
    monkeypatch.setattr(api, "urlopen", lambda *args, **kwargs: FakeResponse(active_payload()))
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403


def test_bearer_scheme_is_case_insensitive(monkeypatch):
    client = make_client(monkeypatch, active_payload())
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "bearer test-token"})
    assert response.status_code == 200


def test_lab_ready_reports_configuration_only():
    client = api.create_app({"TESTING": True, "OIDC_CLIENT_SECRET": "configured"}).test_client()
    response = client.get("/lab/ready")
    assert response.status_code == 200
    assert response.get_json()["client_secret_configured"] is True
    assert "not evidence" in response.get_json()["note"]


def test_documentation_headers_are_present():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/")
    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert response.headers["Cache-Control"] == "no-cache"

def test_route_rejects_missing_bearer():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/api/driver/route")
    assert response.status_code == 401
    assert response.get_json()["error"] == "bearer_token_required"


def test_route_accepts_authorized_synthetic_access(monkeypatch):
    client = make_client(monkeypatch, active_payload())
    response = client.get(
        "/api/driver/route",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["synthetic_data"] is True
    assert payload["route_id"] == "SANAD-LAB-ROUTE-001"


def test_oversized_request_is_rejected_before_authentication():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.post(
        "/api/driver/enroll-authenticator",
        data=b"x" * (16 * 1024 + 1),
        content_type="application/octet-stream",
    )
    assert response.status_code == 413
    assert response.get_json()["error"] == "request_too_large"


def test_active_claim_must_be_boolean_true(monkeypatch):
    client = make_client(monkeypatch, active_payload(active="true"))
    response = client.get(
        "/api/driver/wallet",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 401


def test_introspection_uses_post_and_client_authentication(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["authorization"] = req.get_header("Authorization")
        captured["content_type"] = req.get_header("Content-type")
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = timeout
        return FakeResponse(active_payload())

    monkeypatch.setattr(api, "urlopen", fake_urlopen)
    client = api.create_app({
        "TESTING": True,
        "OIDC_CLIENT_ID": "driver-wallet-api",
        "OIDC_CLIENT_SECRET": "test-secret",
        "EXPECTED_AUDIENCE": "driver-wallet-api",
        "REQUIRED_WALLET_SCOPE": "wallet:read",
        "KEYCLOAK_ISSUER": "https://idp.example/realms/sanad-lab",
        "HTTP_TIMEOUT_SECONDS": 2.5,
    }).test_client()

    response = client.get(
        "/api/driver/wallet",
        headers={"Authorization": "Bearer sample-token"},
    )

    assert response.status_code == 200
    assert captured["url"] == (
        "https://idp.example/realms/sanad-lab/protocol/openid-connect/token/introspect"
    )
    assert captured["method"] == "POST"
    assert captured["authorization"].startswith("Basic ")
    assert captured["content_type"] == "application/x-www-form-urlencoded"
    assert "token=sample-token" in captured["body"]
    assert captured["timeout"] == 2.5

