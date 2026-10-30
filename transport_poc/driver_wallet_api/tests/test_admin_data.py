import io
import json

from cryptography.fernet import Fernet

import app as api


def admin_client(monkeypatch, tmp_path, roles=None):
    claims = {
        "active": True, "client_id": "sanad-driver-web", "sub": "admin-test-001",
        "aud": ["driver-wallet-api"], "scope": "openid wallet:read",
        "iss": "https://idp.example/realms/sanad-lab", "tenant_id": "tenant-test-001", "email": "alqayadhia@gmail.com", "email_verified": True,
        "realm_access": {"roles": roles or ["sanad-admin"]},
    }
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size=-1): return json.dumps(claims).encode()[:size]
    monkeypatch.setattr(api, "urlopen", lambda *a, **k: Response())
    client = api.create_app({
        "TESTING": True,
        "OIDC_CLIENT_ID": "driver-wallet-api",
        "OIDC_CLIENT_SECRET": "test-secret",
        "EXPECTED_AUDIENCE": "driver-wallet-api",
        "REQUIRED_WALLET_SCOPE": "wallet:read",
        "KEYCLOAK_ISSUER": "https://idp.example/realms/sanad-lab",
        "SANAD_DATA_DIR": str(tmp_path),
        "SANAD_DATA_ENCRYPTION_KEY": Fernet.generate_key().decode(),
    }).test_client()
    return client


def test_admin_seed_requires_admin_role(monkeypatch, tmp_path):
    client = admin_client(monkeypatch, tmp_path, roles=["driver"])
    response = client.post("/api/admin/datasets/seed",
                           headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403
    assert response.get_json()["error"] == "admin_role_required"


def test_admin_seed_creates_encrypted_synthetic_dataset(monkeypatch, tmp_path):
    client = admin_client(monkeypatch, tmp_path)
    response = client.post("/api/admin/datasets/seed",
                           headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 201
    assert response.get_json()["synthetic_data"] is True
    dataset_id = response.get_json()["id"]
    preview = client.get(f"/api/admin/datasets/{dataset_id}/preview",
                         headers={"Authorization": "Bearer test-token"})
    assert preview.status_code == 200
    assert len(preview.get_json()["records"]) == 3


def test_admin_upload_csv_and_list(monkeypatch, tmp_path):
    client = admin_client(monkeypatch, tmp_path)
    response = client.post(
        "/api/admin/datasets/upload",
        data={"file": (io.BytesIO(b"driver_id,status\nDRV-001,active\n"), "drivers.csv")},
        content_type="multipart/form-data",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 201
    assert response.get_json()["row_count"] == 1
    listing = client.get("/api/admin/datasets",
                         headers={"Authorization": "Bearer test-token"})
    assert listing.status_code == 200
    assert listing.get_json()["datasets"][0]["filename"] == "drivers.csv"


def test_admin_upload_rejects_unsupported_extension(monkeypatch, tmp_path):
    client = admin_client(monkeypatch, tmp_path)
    response = client.post(
        "/api/admin/datasets/upload",
        data={"file": (io.BytesIO(b"hello"), "payload.exe")},
        content_type="multipart/form-data",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "unsupported_file_type"


def test_admin_routes_require_authentication(tmp_path):
    client = api.create_app({"TESTING": True, "SANAD_DATA_DIR": str(tmp_path)}).test_client()
    response = client.post("/api/admin/datasets/seed")
    assert response.status_code == 401



def test_dataset_isolation_between_tenants(monkeypatch, tmp_path):
    owner = admin_client(monkeypatch, tmp_path)
    seeded = owner.post("/api/admin/datasets/seed",
                        headers={"Authorization": "Bearer test-token"})
    dataset_id = seeded.get_json()["id"]

    other_claims = {
        "active": True, "client_id": "sanad-driver-web", "sub": "other-admin", "aud": ["driver-wallet-api"],
        "scope": "openid wallet:read", "iss": "https://idp.example/realms/sanad-lab",
        "tenant_id": "tenant-other", "email": "other-admin@example.com", "email_verified": True, "realm_access": {"roles": ["sanad-admin"]},
    }
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size=-1): return json.dumps(other_claims).encode()[:size]
    monkeypatch.setattr(api, "urlopen", lambda *a, **k: Response())
    other = api.create_app({
        "TESTING": True, "OIDC_CLIENT_ID": "driver-wallet-api",
        "OIDC_CLIENT_SECRET": "test-secret", "EXPECTED_AUDIENCE": "driver-wallet-api",
        "REQUIRED_WALLET_SCOPE": "wallet:read",
        "KEYCLOAK_ISSUER": "https://idp.example/realms/sanad-lab",
        "ADMIN_EMAIL": "other-admin@example.com",
        "SANAD_DATA_DIR": str(tmp_path),
        "SANAD_DATA_ENCRYPTION_KEY": owner.application.config["SANAD_DATA_ENCRYPTION_KEY"],
    }).test_client()
    headers = {"Authorization": "Bearer test-token"}
    assert other.get("/api/admin/datasets", headers=headers).get_json()["datasets"] == []
    assert other.get(f"/api/admin/datasets/{dataset_id}/preview",
                     headers=headers).status_code == 404


def test_admin_routes_require_allowlisted_verified_email(monkeypatch, tmp_path):
    client = admin_client(monkeypatch, tmp_path)
    claims = {
        "active": True, "client_id": "sanad-driver-web", "sub": "other-user",
        "aud": ["driver-wallet-api"], "scope": "openid wallet:read",
        "iss": "https://idp.example/realms/sanad-lab", "tenant_id": "tenant-test-001",
        "email": "attacker@example.com", "email_verified": True,
        "realm_access": {"roles": ["sanad-admin"]},
    }
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size=-1): return json.dumps(claims).encode()[:size]
    monkeypatch.setattr(api, "urlopen", lambda *a, **k: Response())
    response = client.get("/api/admin/datasets", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403
    assert response.get_json()["error"] == "admin_identity_not_verified"


def test_admin_routes_require_verified_email_claim(monkeypatch, tmp_path):
    client = admin_client(monkeypatch, tmp_path)
    claims = {
        "active": True, "client_id": "sanad-driver-web", "sub": "admin-test-001",
        "aud": ["driver-wallet-api"], "scope": "openid wallet:read",
        "iss": "https://idp.example/realms/sanad-lab", "tenant_id": "tenant-test-001",
        "email": "alqayadhia@gmail.com", "email_verified": False,
        "realm_access": {"roles": ["sanad-admin"]},
    }
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size=-1): return json.dumps(claims).encode()[:size]
    monkeypatch.setattr(api, "urlopen", lambda *a, **k: Response())
    response = client.get("/api/admin/datasets", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403
    assert response.get_json()["error"] == "admin_identity_not_verified"


def test_public_oidc_config_does_not_disclose_admin_email():
    client = api.create_app({"TESTING": True}).test_client()
    response = client.get("/lab/config")
    assert response.status_code == 200
    payload = response.get_json()
    assert "admin_email" not in payload
    assert "alqayadhia@gmail.com" not in response.get_data(as_text=True)
