"""Regression tests for authentication fail-closed behavior."""
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
        payload = {
            "active": True,
            "aud": ["driver-wallet-api"],
            "iss": "https://attacker.example.test/realms/fake",
        }
        with self._mock_introspection(payload):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer wrong-issuer-token"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "issuer_mismatch_or_missing")

    def test_valid_introspection_claims_allow_synthetic_wallet_read(self):
        client = self._configured_client()
        payload = {
            "active": True,
            "aud": ["driver-wallet-api"],
            "iss": "https://id.example.test/realms/sanad-lab",
            "sub": "test-subject",
            "preferred_username": "test-driver",
        }
        with self._mock_introspection(payload):
            response = client.get(
                "/api/driver/wallet",
                headers={"Authorization": "Bearer valid-test-token"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["driver"], "test-driver")
        self.assertTrue(response.get_json()["synthetic_data"])


if __name__ == "__main__":
    unittest.main()
