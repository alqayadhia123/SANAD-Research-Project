"""Integration-boundary tests: Keycloak introspection must precede tenant authorization."""
import json
from io import BytesIO
import importlib

import pytest

app_module = importlib.import_module("transport_poc.driver_wallet_api.app")

class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self):
        return self.payload

@pytest.fixture
def client(monkeypatch):
    payload = {
        "active": True,
        "aud": ["driver-wallet-api"],
        "iss": "https://id.example.test/realms/sanad",
        "sub": "driver-123",
        "tenant_id": "fleet-riyadh",
    }
    monkeypatch.setattr(app_module, "urlopen", lambda *_a, **_kw: FakeResponse(payload))
    app = app_module.create_app({
        "TESTING": True,
        "KEYCLOAK_ISSUER": "https://id.example.test/realms/sanad",
        "OIDC_CLIENT_ID": "driver-wallet-api",
        "OIDC_CLIENT_SECRET": "test-only-secret",
        "EXPECTED_AUDIENCE": "driver-wallet-api",
    })
    return app.test_client()

def test_valid_identity_and_matching_tenant_allowed(client):
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer valid-token",
                                   "X-Tenant-ID": "fleet-riyadh"})
    assert response.status_code == 200
    assert response.get_json()["synthetic_data"] is True

def test_tenant_header_cannot_claim_another_tenant(client):
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer valid-token",
                                   "X-Tenant-ID": "fleet-jeddah"})
    assert response.status_code == 403

def test_missing_tenant_selector_uses_single_verified_membership(client):
    response = client.get("/api/driver/wallet",
                          headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 200

def test_unverified_request_cannot_reach_tenant_handler(client):
    response = client.get("/api/driver/wallet",
                          headers={"X-Tenant-ID": "fleet-riyadh"})
    assert response.status_code == 401

def test_enrollment_stays_unimplemented_after_tenant_auth(client):
    response = client.post("/api/driver/enroll-authenticator",
                           headers={"Authorization": "Bearer valid-token",
                                    "X-Tenant-ID": "fleet-riyadh"})
    assert response.status_code == 501
