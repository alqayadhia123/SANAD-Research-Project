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
        raw = json.dumps(self.payload).encode("utf-8")
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


def test_enrollment_is_explicitly_not_implemented():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.post("/api/driver/enroll-authenticator", json={
        "authenticator_id": "attacker-controlled"
    })
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
