"""Regression tests for authentication and authorization fail-closed behavior."""
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from app import create_app


class AuthenticationFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"DEMO_MODE": "true"})
        self.env.start()
        self.app = create_app({
            "TESTING": True,
            "OIDC_CLIENT_SECRET": "",
            "KEYCLOAK_ISSUER": "http://keycloak.invalid/realms/sanad-lab",
            "OIDC_CLIENT_ID": "driver-wallet-api",
            "EXPECTED_AUDIENCE": "driver-wallet-api",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.env.stop()

    def test_demo_mode_does_not_bypass_missing_bearer_token(self):
        response = self.client.get("/api/driver/wallet")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "bearer_token_required")

    def test_demo_mode_does_not_bypass_unconfigured_introspection(self):
        response = self.client.get(
            "/api/driver/wallet",
            headers={"Authorization": "Bearer synthetic-token"},
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"], "introspection_not_configured")

    def test_route_endpoint_also_requires_authentication(self):
        response = self.client.get("/api/driver/route")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "bearer_token_required")

    def test_oversized_bearer_token_is_rejected(self):
        response = self.client.get(
            "/api/driver/wallet",
            headers={"Authorization": "Bearer " + ("x" * 8193)},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "bearer_token_too_large")

    def _configured_client(self):
        app = create_app({
            "TESTING": True,
            "OIDC_CLIENT_SECRET": "unit-test-secret",
            "KEYCLOAK_ISSUER": "https://id.example.test/realms/sanad-lab",
            "OIDC_CLIENT_ID": "driver-wallet-api",
            "EXPECTED_AUDIENCE": "driver-wallet-api",
        })
        return app.test_client()

    def _mock_introspection(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
        return patch("app.urlopen", return_value=response)

    def _valid_claims(self, **extra):
        claims = {
            "active": True,
            "aud": ["driver-wallet-api"],
            "iss": "https://id.example.test/realms/sanad-lab",
            "sub": "test-subject",
            "preferred_username": "test-driver",
        }
        claims.update(extra)
        return claims

    def test_inactive_token_is_rejected(self):
        client = self._configured_client()
        with self._mock_introspection({"active": False}):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer invalid-token"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "inactive_token")

    def test_missing_audience_is_rejected(self):
        client = self._configured_client()
        payload = {
            "active": True,
            "iss": "https://id.example.test/realms/sanad-lab",
        }
        with self._mock_introspection(payload):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer token-without-audience"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "audience_mismatch_or_missing")

    def test_wrong_issuer_is_rejected(self):
        client = self._configured_client()
        payload = self._valid_claims(
            iss="https://attacker.example.test/realms/fake",
            scope="wallet:read",
        )
        with self._mock_introspection(payload):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer wrong-issuer-token"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "issuer_mismatch_or_missing")

    def test_wallet_requires_wallet_read_scope(self):
        client = self._configured_client()
        with self._mock_introspection(self._valid_claims(scope="profile")):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer valid-but-underprivileged-token"},
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "insufficient_scope")

    def test_route_requires_route_read_scope(self):
        client = self._configured_client()
        with self._mock_introspection(self._valid_claims(scope="wallet:read")):
            response = client.get(
                "/api/driver/route",
                headers={"Authorization": "Bearer wallet-only-token"},
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "insufficient_scope")

    def test_valid_wallet_scope_allows_synthetic_wallet_read(self):
        client = self._configured_client()
        with self._mock_introspection(self._valid_claims(scope="wallet:read profile")):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer valid-wallet-token"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["driver"], "test-driver")
        self.assertTrue(response.get_json()["synthetic_data"])

    def test_valid_route_scope_allows_synthetic_route_read(self):
        client = self._configured_client()
        with self._mock_introspection(self._valid_claims(scope="route:read")):
            response = client.get(
                "/api/driver/route",
                headers={"Authorization": "Bearer valid-route-token"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["route_id"], "RT-LAB-0001")
        self.assertTrue(response.get_json()["synthetic_data"])


if __name__ == "__main__":
    unittest.main()
