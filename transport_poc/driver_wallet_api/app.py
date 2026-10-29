"""Transport-domain protected API for an isolated research lab.
All wallet and route data are synthetic. Not production-ready.
"""
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request, render_template


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        KEYCLOAK_ISSUER=os.getenv("KEYCLOAK_ISSUER", "http://keycloak-transport:8080/realms/riyadh-transport-lab").rstrip("/"),
        KEYCLOAK_BROWSER_ISSUER=os.getenv("KEYCLOAK_BROWSER_ISSUER", "http://localhost:8080/realms/riyadh-transport-lab").rstrip("/"),
        OIDC_CLIENT_ID=os.getenv("OIDC_CLIENT_ID", "driver-wallet-api"),
        OIDC_CLIENT_SECRET=os.getenv("OIDC_CLIENT_SECRET", ""),
        EXPECTED_AUDIENCE=os.getenv("EXPECTED_AUDIENCE", "driver-wallet-api"),
        HTTP_TIMEOUT_SECONDS=float(os.getenv("HTTP_TIMEOUT_SECONDS", "3")),
    )
    if test_config:
        app.config.update(test_config)

    def introspect(token):
        """Return verified active-token metadata; unavailable introspection fails closed."""
        secret = app.config["OIDC_CLIENT_SECRET"]
        if not secret or not token:
            return None, "introspection_not_configured"
        endpoint = f"{app.config['KEYCLOAK_ISSUER']}/protocol/openid-connect/token/introspect"
        body = urlencode({"token": token, "token_type_hint": "access_token"}).encode()
        basic = base64.b64encode(f"{app.config['OIDC_CLIENT_ID']}:{secret}".encode()).decode()
        req = Request(endpoint, data=body, headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        })
        try:
            with urlopen(req, timeout=app.config["HTTP_TIMEOUT_SECONDS"]) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            return None, "introspection_unavailable"
        if not isinstance(data, dict) or data.get("active") is not True:
            return None, "inactive_token"
        # Require explicit audience binding; configure a Keycloak audience mapper for this API.
        aud = data.get("aud", [])
        if isinstance(aud, str):
            aud = [aud]
        if app.config["EXPECTED_AUDIENCE"] not in aud:
            return None, "audience_mismatch_or_missing"
        issuer = data.get("iss")
        if issuer and issuer.rstrip("/") != app.config["KEYCLOAK_ISSUER"]:
            return None, "issuer_mismatch"
        return data, None

    def authorized_subject():
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or not header[7:].strip():
            return None, (jsonify(error="bearer_token_required"), 401)
        data, error = introspect(header[7:].strip())
        if error:
            status = 503 if error in {"introspection_not_configured", "introspection_unavailable"} else 401
            return None, (jsonify(error=error, access="denied"), status)
        return data, None

    @app.get("/health")
    def health():
        return jsonify(status="ok", component="driver-wallet-api", mode="isolated-research-lab")

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
        ), 200

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
        ), 200

    @app.get("/lab/ready")
    def lab_ready():
        return jsonify(
            client_id=app.config["OIDC_CLIENT_ID"],
            expected_audience=app.config["EXPECTED_AUDIENCE"],
            client_secret_configured=bool(app.config["OIDC_CLIENT_SECRET"]),
            note="Configuration presence only; not evidence of live Keycloak connectivity or security efficacy.",
        )
@app.get("/")
def driver_app():
    return render_template("index.html")

REGISTERED_AUTHENTICATORS = {"U-001": ["AUTH-001-PRIMARY"]}
PENDING_ENROLLMENT_REQUESTS = {}

@app.post("/api/driver/enroll-authenticator")
def enroll_authenticator():
    token_data, failure = authorized_subject()
    if failure:
        return failure
    driver_id = token_data.get("preferred_username", "unknown")
    request_body = request.get_json() or {}
    new_auth_id = request_body.get("authenticator_id", "UNKNOWN")
    existing = REGISTERED_AUTHENTICATORS.get(driver_id, [])
    if new_auth_id not in existing:
        PENDING_ENROLLMENT_REQUESTS[driver_id] = {"attempted_id": new_auth_id, "status": "BLOCKED"}
        return jsonify(status="denied", error="unauthorized_enrollment_blocked", message="يتطلب موافقة خارج النطاق"), 403
    return jsonify(status="success"), 200
    return app


app = create_app()
