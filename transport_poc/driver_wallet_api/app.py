"""Transport-domain protected API for an isolated research lab."""
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, jsonify, render_template, request


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        KEYCLOAK_ISSUER=os.getenv("KEYCLOAK_ISSUER", "http://keycloak-transport:8080/realms/riyadh-transport-lab").rstrip("/"),
        OIDC_CLIENT_ID=os.getenv("OIDC_CLIENT_ID", "driver-wallet-api"),
        OIDC_CLIENT_SECRET=os.getenv("OIDC_CLIENT_SECRET", ""),
        EXPECTED_AUDIENCE=os.getenv("EXPECTED_AUDIENCE", "driver-wallet-api"),
        HTTP_TIMEOUT_SECONDS=float(os.getenv("HTTP_TIMEOUT_SECONDS", "3")),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    def introspect(token):
        secret = app.config["OIDC_CLIENT_SECRET"]
        if not secret or not token:
            return None, "introspection_not_configured"
        endpoint = app.config["KEYCLOAK_ISSUER"] + "/protocol/openid-connect/token/introspect"
        body = urlencode({"token": token, "token_type_hint": "access_token"}).encode("utf-8")
        credentials = (app.config["OIDC_CLIENT_ID"] + ":" + secret).encode("utf-8")
        basic = base64.b64encode(credentials).decode("ascii")
        req = Request(endpoint, data=body, headers={
            "Authorization": "Basic " + basic,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }, method="POST")
        try:
            with urlopen(req, timeout=app.config["HTTP_TIMEOUT_SECONDS"]) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            app.logger.warning("Keycloak token introspection failed")
            return None, "introspection_unavailable"
        if not isinstance(data, dict) or data.get("active") is not True:
            return None, "inactive_token"
        audience = data.get("aud", [])
        if isinstance(audience, str):
            audience = [audience]
        if not isinstance(audience, list) or app.config["EXPECTED_AUDIENCE"] not in audience:
            return None, "audience_mismatch_or_missing"
        issuer = data.get("iss")
        if not isinstance(issuer, str) or issuer.rstrip("/") != app.config["KEYCLOAK_ISSUER"]:
            return None, "issuer_mismatch_or_missing"
        return data, None

    def authorized_subject():
        header = request.headers.get("Authorization", "")
        scheme, separator, value = header.partition(" ")
        if not separator or scheme.lower() != "bearer" or not value.strip():
            return None, (jsonify(error="bearer_token_required"), 401)
        token = value.strip()
        if len(token) > 8192:
            return None, (jsonify(error="bearer_token_too_large"), 401)
        data, error = introspect(token)
        if error:
            status = 503 if error in {"introspection_not_configured", "introspection_unavailable"} else 401
            return None, (jsonify(error=error, access="denied"), status)
        return data, None

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store" if request.path.startswith("/api/") else "no-cache")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        return response

    @app.get("/")
    def driver_app():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok", component="driver-wallet-api", mode="isolated-research-lab")

    @app.get("/lab/ready")
    def lab_ready():
        return jsonify(
            client_id=app.config["OIDC_CLIENT_ID"],
            expected_audience=app.config["EXPECTED_AUDIENCE"],
            client_secret_configured=bool(app.config["OIDC_CLIENT_SECRET"]),
            note="Configuration presence only; not evidence of Keycloak connectivity or security efficacy.",
        )

    @app.get("/api/driver/wallet")
    def get_wallet():
        token_data, failure = authorized_subject()
        if failure:
            return failure
        return jsonify(
            status="success",
            driver=token_data.get("preferred_username", token_data.get("sub", "synthetic-driver")),
            wallet_balance=1450.00,
            currency="SAR",
            synthetic_data=True,
            message="Synthetic wallet data; no real funds or financial actions are connected.",
        )

    @app.get("/api/driver/route")
    def get_route():
        token_data, failure = authorized_subject()
        if failure:
            return failure
        return jsonify(
            status="success",
            driver=token_data.get("preferred_username", token_data.get("sub", "synthetic-driver")),
            route_id="RT-LAB-0001",
            pickup="Synthetic pickup location",
            dropoff="Synthetic drop-off location",
            route_status="active",
            synthetic_data=True,
        )

    @app.post("/api/driver/enroll-authenticator")
    def enroll_authenticator():
        token_data, failure = authorized_subject()
        if failure:
            return failure
        return jsonify(
            status="denied",
            error="authenticator_enrollment_not_implemented",
            message="يلزم تنفيذ WebAuthn challenge/attestation والتحقق منهما قبل التسجيل.",
        ), 501

    return app


app = create_app()
