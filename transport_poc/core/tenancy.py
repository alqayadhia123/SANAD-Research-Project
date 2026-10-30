"""Fail-closed tenant binding for SANAD.
Authentication must run first. Only verified claims in flask.g.authenticated_claims
are authoritative; headers and hostnames are selectors, never proof of membership.
"""
from __future__ import annotations
import re
from contextvars import ContextVar, Token
from functools import wraps
from typing import Any, Callable, Mapping
from flask import Flask, g, jsonify, request

_TENANT_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_current_tenant: ContextVar[str | None] = ContextVar("sanad_current_tenant", default=None)

class TenantResolutionError(ValueError):
    pass

def validate_tenant_id(value: Any) -> str:
    if not isinstance(value, str) or not _TENANT_RE.fullmatch(value):
        raise TenantResolutionError("Invalid tenant identifier")
    return value

def current_tenant() -> str:
    tenant = _current_tenant.get()
    if tenant is None:
        raise TenantResolutionError("No tenant is bound to this execution context")
    return tenant

def _trusted_memberships(claims: Mapping[str, Any]) -> set[str]:
    memberships: set[str] = set()
    direct = claims.get("tenant_id")
    if direct is not None:
        memberships.add(validate_tenant_id(direct))
    values = claims.get("tenants", [])
    if values is not None:
        if not isinstance(values, list):
            raise TenantResolutionError("Invalid tenant membership claim")
        memberships.update(validate_tenant_id(item) for item in values)
    return memberships

def _requested_tenant() -> str | None:
    header = request.headers.get("X-Tenant-ID")
    if header:
        return validate_tenant_id(header)
    host = request.host.split(":", 1)[0].lower()
    parts = host.split(".")
    if len(parts) >= 3 and parts[0] not in {"www", "api", "app", "admin", "static", "localhost"}:
        return validate_tenant_id(parts[0])
    return None

def init_tenancy(app: Flask) -> None:
    if app.extensions.get("sanad_tenancy_initialized"):
        return
    @app.teardown_request
    def _reset_tenant_context(_error: BaseException | None) -> None:
        token: Token[str | None] | None = getattr(g, "_sanad_tenant_token", None)
        if token is not None:
            _current_tenant.reset(token)
            delattr(g, "_sanad_tenant_token")
        if hasattr(g, "tenant"):
            delattr(g, "tenant")
    app.extensions["sanad_tenancy_initialized"] = True

def require_tenant(handler: Callable):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        claims = getattr(g, "authenticated_claims", None)
        if not isinstance(claims, Mapping):
            return jsonify(error="authentication_required"), 401
        try:
            memberships = _trusted_memberships(claims)
            requested = _requested_tenant()
        except TenantResolutionError:
            return jsonify(error="invalid_tenant"), 400
        if requested is None:
            if len(memberships) != 1:
                return jsonify(error="tenant_required"), 400
            requested = next(iter(memberships))
        if requested not in memberships:
            return jsonify(error="tenant_forbidden"), 403
        token = _current_tenant.set(requested)
        g._sanad_tenant_token = token
        g.tenant = requested
        return handler(*args, **kwargs)
    return wrapped
