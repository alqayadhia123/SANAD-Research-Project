"""SANAD transport API - fail-closed research baseline.

Synthetic resources only. WebAuthn, recovery, OOB approval, and production
wallet functionality are intentionally not implemented by this prototype.
"""
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        KEYCLOAK_ISSUER=os.getenv(
            "KEYCLOAK_ISSUER",
            "http://keycloak-transport:8080/realms/sanad-lab",
        ).rstrip("/"),
        OIDC_CLIENT_ID=os.getenv("OIDC_CLIENT_ID", "driver-wallet-api"),
        OIDC_CLIENT_SECRET=os.getenv("OIDC_CLIENT_SECRET", ""),
        EXPECTED_AUDIENCE=os.getenv("EXPECTED_AUDIENCE", "driver-wallet-api"),
        REQUIRED_WALLET_SCOPE=os.getenv("REQUIRED_WALLET_SCOPE", "wallet:read"),
        HTTP_TIMEOUT_SECONDS=float(os.getenv("HTTP_TIMEOUT_SECONDS", "3")),
        INTROSPECTION_URL=os.getenv("INTROSPECTION_URL", ""),
        KEYCLOAK_INTERNAL_HOSTPORT=os.getenv("KEYCLOAK_INTERNAL_HOSTPORT", "").strip(),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    def introspect(token):
        secret = app.config["OIDC_CLIENT_SECRET"]
        if not secret or not token:
            return None, "introspection_not_configured"

        endpoint = app.config["INTROSPECTION_URL"]
        if not endpoint and app.config["KEYCLOAK_INTERNAL_HOSTPORT"]:
            endpoint = (
                f"http://{app.config['KEYCLOAK_INTERNAL_HOSTPORT']}"
                f"/realms/sanad-lab/protocol/openid-connect/token/introspect"
            )
        if not endpoint:
            endpoint = (
                f"{app.config['KEYCLOAK_ISSUER']}/protocol/openid-connect/token/introspect"
            )
        body = urlencode({"token": token, "token_type_hint": "access_token"}).encode()
        basic = base64.b64encode(
            f"{app.config['OIDC_CLIENT_ID']}:{secret}".encode()
        ).decode("ascii")
        req = Request(
            endpoint, data=body,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=app.config["HTTP_TIMEOUT_SECONDS"]) as response:
                raw_payload = response.read(65537)
            if len(raw_payload) > 65536:
                return None, "introspection_response_too_large"
            payload = json.loads(raw_payload.decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            return None, "introspection_unavailable"

        if not isinstance(payload, dict):
            return None, "invalid_introspection_response"
        if payload.get("active") is not True:
            return None, "inactive_token"

        audiences = payload.get("aud", [])
        if isinstance(audiences, str):
            audiences = [audiences]
        if not isinstance(audiences, list) or app.config["EXPECTED_AUDIENCE"] not in audiences:
            return None, "audience_mismatch_or_missing"

        issuer = payload.get("iss")
        if (
            not isinstance(issuer, str)
            or not issuer.strip()
            or issuer.rstrip("/") != app.config["KEYCLOAK_ISSUER"]
        ):
            return None, "issuer_missing_or_mismatch"

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            return None, "subject_missing"
        return payload, None

    def require_wallet_access():
        header = request.headers.get("Authorization", "")
        scheme, separator, value = header.partition(" ")
        if not separator or scheme.lower() != "bearer" or not value.strip():
            return None, (jsonify(error="bearer_token_required"), 401)
        token = value.strip()
        if len(token) > 8192:
            return None, (jsonify(error="bearer_token_too_large"), 401)
        claims, error = introspect(token)
        if error:
            status = 503 if error in {
                "introspection_not_configured",
                "introspection_unavailable",
                "introspection_response_too_large",
                "invalid_introspection_response",
            } else 401
            return None, (jsonify(error=error, access="denied"), status)
        scope = claims.get("scope")
        if not isinstance(scope, str):
            return None, (jsonify(error="invalid_scope_claim"), 403)
        required = set(app.config["REQUIRED_WALLET_SCOPE"].split())
        granted = set(scope.split())
        if not required or not required.issubset(granted):
            return None, (jsonify(error="insufficient_scope"), 403)
        return claims, None

    @app.before_request
    def enforce_request_size():
        # Flask enforces MAX_CONTENT_LENGTH when a body is read. Check the
        # declared length before route logic so even endpoints that do not
        # parse a body reject oversized requests consistently.
        if request.content_length is not None and request.content_length > app.config["MAX_CONTENT_LENGTH"]:
            return jsonify(error="request_too_large"), 413
        return None

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'",
        )
        response.headers.setdefault(
            "Cache-Control",
            "no-store" if request.path.startswith("/api/") else "no-cache",
        )
        return response

    @app.get("/health")
    def health():
        return jsonify(status="ok", component="driver-wallet-api",
                       data_classification="synthetic"), 200

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/lab/ready")
    def lab_ready():
        return jsonify(
            client_id=app.config["OIDC_CLIENT_ID"],
            expected_audience=app.config["EXPECTED_AUDIENCE"],
            client_secret_configured=bool(app.config["OIDC_CLIENT_SECRET"]),
            note="Configuration presence only; not evidence of Keycloak connectivity or security efficacy.",
        ), 200

    @app.get("/api/driver/wallet")
    def wallet():
        claims, failure = require_wallet_access()
        if failure:
            return failure
        return jsonify(
            status="success",
            driver=claims.get("preferred_username", claims["sub"]),
            wallet_balance=1450.00,
            currency="SAR",
            synthetic_data=True,
            message="Synthetic research data only; no real funds or financial APIs.",
        ), 200

    @app.get("/api/driver/route")
    def route():
        claims, failure = require_wallet_access()
        if failure:
            return failure
        return jsonify(
            status="success", driver=claims.get("preferred_username", claims["sub"]),
            route_id="SANAD-LAB-ROUTE-001",
            pickup="Synthetic pickup location", dropoff="Synthetic drop-off location",
            route_status="active", synthetic_data=True,
        ), 200

    @app.post("/api/driver/enroll-authenticator")
    def enrollment_not_implemented():
        claims, failure = require_wallet_access()
        if failure:
            return failure
        return jsonify(
            error="not_implemented",
            message="Authenticator enrollment is not implemented; no enrollment was performed.",
        ), 501

    return app


app = create_app()
