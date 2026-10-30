import json
from unittest.mock import MagicMock

import app as app_module


ISSUER = "http://keycloak-transport:8080/realms/riyadh-transport-lab"


def make_app():
    return app_module.create_app(
        {
            "TESTING": True,
            "KEYCLOAK_ISSUER": ISSUER,
            "OIDC_CLIENT_ID": "driver-wallet-api",
            "OIDC_CLIENT_SECRET": "test-only-secret",
            "EXPECTED_AUDIENCE": "driver-wallet-api",
            "HTTP_TIMEOUT_SECONDS": 1,
        }
    )


def mock_introspection(monkeypatch, payload):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    monkeypatch.setattr(app_module, "urlopen", lambda *args, **kwargs: response)


def test_health_is_public():
    client = make_app().test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_wallet_rejects_missing_bearer_token_even_if_demo_mode_set(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    response = make_app().test_client().get("/api/driver/wallet")
    assert response.status_code == 401
    assert response.json["error"] == "bearer_token_required"


def test_wallet_rejects_inactive_token(monkeypatch):
    mock_introspection(monkeypatch, {"active": False})
    response = make_app().test_client().get(
        "/api/driver/wallet", headers={"Authorization": "Bearer inactive"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "inactive_token"


def test_wallet_accepts_active_token_with_expected_issuer_and_audience(monkeypatch):
    mock_introspection(
        monkeypatch,
        {
            "active": True,
            "aud": ["driver-wallet-api"],
            "iss": ISSUER,
            "preferred_username": "synthetic-driver-01",
        },
    )
    response = make_app().test_client().get(
        "/api/driver/wallet", headers={"Authorization": "Bearer valid-test-token"}
    )
    assert response.status_code == 200
    assert response.json["driver"] == "synthetic-driver-01"
    assert response.json["synthetic_data"] is True


def test_wallet_rejects_wrong_audience(monkeypatch):
    mock_introspection(
        monkeypatch,
        {"active": True, "aud": ["another-api"], "iss": ISSUER},
    )
    response = make_app().test_client().get(
        "/api/driver/wallet", headers={"Authorization": "Bearer wrong-aud"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "audience_mismatch_or_missing"


def test_wallet_rejects_oversized_token():
    response = make_app().test_client().get(
        "/api/driver/wallet",
        headers={"Authorization": "Bearer " + ("x" * 8193)},
    )
    assert response.status_code == 401
    assert response.json["error"] == "bearer_token_too_large"
