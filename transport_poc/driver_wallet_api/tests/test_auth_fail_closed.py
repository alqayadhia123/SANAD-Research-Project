"""Regression tests for authentication fail-closed behavior."""
import os
import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
