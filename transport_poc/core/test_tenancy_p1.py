"""Focused security tests for tenant binding."""
import json
import pytest
from flask import Flask, g, jsonify, request
from transport_poc.core.tenancy import current_tenant, init_tenancy, require_tenant, TenantResolutionError

def make_app():
    app = Flask(__name__)
    init_tenancy(app)
    @app.before_request
    def mock_verified_authentication():
        raw = request.headers.get("X-Test-Claims")
        if raw:
            g.authenticated_claims = json.loads(raw)
    @app.get("/tenant")
    @require_tenant
    def tenant_endpoint():
        return jsonify(tenant=current_tenant())
    return app

def test_header_is_selector_and_requires_verified_membership():
    response = make_app().test_client().get("/tenant", headers={
        "X-Tenant-ID": "uber-riyadh", "X-Test-Claims": '{"tenant_id":"uber-riyadh"}'})
    assert response.status_code == 200
    assert response.json["tenant"] == "uber-riyadh"

def test_header_cannot_switch_tenant():
    response = make_app().test_client().get("/tenant", headers={
        "X-Tenant-ID": "careem-jeddah", "X-Test-Claims": '{"tenant_id":"uber-riyadh"}'})
    assert response.status_code == 403

def test_missing_verified_identity_fails_closed():
    response = make_app().test_client().get("/tenant", headers={"X-Tenant-ID": "uber-riyadh"})
    assert response.status_code == 401

def test_multi_tenant_principal_must_select_tenant():
    response = make_app().test_client().get("/tenant", headers={
        "X-Test-Claims": '{"tenants":["uber-riyadh","careem-jeddah"]}'})
    assert response.status_code == 400
    assert response.json["error"] == "tenant_required"

def test_context_is_reset_after_request():
    app = make_app()
    app.test_client().get("/tenant", headers={"X-Test-Claims": '{"tenant_id":"uber-riyadh"}'})
    with app.test_request_context("/"):
        with pytest.raises(TenantResolutionError):
            current_tenant()
