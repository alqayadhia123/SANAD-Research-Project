"""Admin-only synthetic dataset API with authenticated encryption at rest."""
import csv
from contextlib import contextmanager
import hashlib
import io
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from flask import jsonify, request

ALLOWED_EXTENSIONS = {".csv", ".json"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10000


def _db_path(app):
    root = Path(app.config["SANAD_DATA_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    return root / "datasets.sqlite3"


@contextmanager
def _database(app):
    db = _connect(app)
    try:
        yield db
        db.commit()
    finally:
        db.close()


def _connect(app):
    db = sqlite3.connect(_db_path(app), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            content_type TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            encrypted_payload BLOB NOT NULL,
            uploaded_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()
    return db


def _cipher(app):
    key = app.config.get("SANAD_DATA_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("data_encryption_key_not_configured")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, TypeError, UnicodeEncodeError):
        raise RuntimeError("data_encryption_key_invalid")


def _records(filename, raw):
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("unsupported_file_type")
    text = raw.decode("utf-8-sig")
    if suffix == ".json":
        payload = json.loads(text)
        if isinstance(payload, dict):
            payload = payload.get("records")
        if not isinstance(payload, list) or not all(isinstance(x, dict) for x in payload):
            raise ValueError("json_must_be_array_of_objects_or_records_object")
        records = payload
    else:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or any(not x for x in reader.fieldnames):
            raise ValueError("csv_header_required")
        if len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("duplicate_csv_headers")
        records = list(reader)
    if not records:
        raise ValueError("dataset_empty")
    if len(records) > MAX_ROWS:
        raise ValueError("too_many_rows")
    return records


def register_admin_routes(app, authorize):
    def admin_claims():
        claims, failure = authorize()
        if failure:
            return None, failure
        realm_roles = claims.get("realm_access", {}).get("roles", [])
        resource_roles = claims.get("resource_access", {}).get(
            app.config["OIDC_CLIENT_ID"], {}
        ).get("roles", [])
        roles = set(realm_roles if isinstance(realm_roles, list) else [])
        roles.update(resource_roles if isinstance(resource_roles, list) else [])
        if "sanad-admin" not in roles and "admin" not in roles:
            return None, (jsonify(error="admin_role_required"), 403)
        # Only trust email claims returned by server-side Keycloak introspection.
        expected_email = app.config.get("ADMIN_EMAIL", "").strip().lower()
        actual_email = claims.get("email")
        if (
            not expected_email
            or not isinstance(actual_email, str)
            or actual_email.strip().lower() != expected_email
            or claims.get("email_verified") is not True
        ):
            return None, (jsonify(error="admin_identity_not_verified"), 403)
        tenant_id = claims.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            return None, (jsonify(error="verified_tenant_claim_required"), 403)
        return claims, None

    @app.get("/api/admin/datasets")
    def list_datasets():
        claims, failure = admin_claims()
        if failure:
            return failure
        try:
            with _database(app) as db:
                rows = db.execute(
                    "SELECT id,filename,content_type,row_count,sha256,uploaded_by,created_at "
                    "FROM datasets WHERE tenant_id=? ORDER BY created_at DESC",
                    (claims["tenant_id"],)
                ).fetchall()
            return jsonify(datasets=[dict(row) for row in rows], synthetic_data=True), 200
        except (OSError, sqlite3.Error):
            return jsonify(error="dataset_storage_unavailable"), 503

    @app.post("/api/admin/datasets/upload")
    def upload_dataset():
        claims, failure = admin_claims()
        if failure:
            return failure
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify(error="file_required"), 400
        filename = Path(upload.filename.replace("\\", "/")).name
        if len(filename) > 180 or re.search(r"[\x00-\x1f]", filename):
            return jsonify(error="invalid_filename"), 400
        raw = upload.read(MAX_UPLOAD_BYTES + 1)
        if len(raw) > MAX_UPLOAD_BYTES:
            return jsonify(error="file_too_large", max_bytes=MAX_UPLOAD_BYTES), 413
        try:
            records = _records(filename, raw)
            cipher = _cipher(app)
        except UnicodeDecodeError:
            return jsonify(error="file_must_be_utf8"), 400
        except (ValueError, json.JSONDecodeError) as exc:
            return jsonify(error=str(exc) or "invalid_dataset"), 400
        except RuntimeError as exc:
            return jsonify(error=str(exc)), 503

        canonical = json.dumps(records, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
        encrypted = cipher.encrypt(canonical)
        digest = hashlib.sha256(canonical).hexdigest()
        dataset_id = hashlib.sha256(os.urandom(32)).hexdigest()[:24]
        created = datetime.now(timezone.utc).isoformat()
        subject = claims.get("sub", "unknown")
        try:
            with _database(app) as db:
                db.execute(
                    "INSERT INTO datasets "
                    "(id,tenant_id,filename,content_type,row_count,sha256,encrypted_payload,uploaded_by,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (dataset_id, claims["tenant_id"], filename, Path(filename).suffix.lower()[1:],
                     len(records), digest, encrypted, subject, created),
                )
            return jsonify(status="stored_encrypted", id=dataset_id,
                           row_count=len(records), sha256=digest,
                           encryption="Fernet authenticated encryption",
                           synthetic_data=True), 201
        except (OSError, sqlite3.Error):
            return jsonify(error="dataset_storage_unavailable"), 503

    @app.post("/api/admin/datasets/seed")
    def seed_dataset():
        claims, failure = admin_claims()
        if failure:
            return failure
        samples = {
            "drivers": [
                {"driver_id":"DRV-TEST-001","display_name":"سائق تجريبي 001","status":"active","city":"Riyadh"},
                {"driver_id":"DRV-TEST-002","display_name":"سائق تجريبي 002","status":"pending","city":"Jeddah"},
                {"driver_id":"DRV-TEST-003","display_name":"سائق تجريبي 003","status":"suspended","city":"Dammam"}
            ],
            "wallets": [
                {"wallet_id":"WLT-TEST-001","driver_id":"DRV-TEST-001","balance":1450.00,"currency":"SAR","classification":"synthetic"},
                {"wallet_id":"WLT-TEST-002","driver_id":"DRV-TEST-002","balance":320.50,"currency":"SAR","classification":"synthetic"}
            ],
            "routes": [
                {"route_id":"RTE-TEST-001","driver_id":"DRV-TEST-001","pickup":"Test Point A","dropoff":"Test Point B","status":"completed"},
                {"route_id":"RTE-TEST-002","driver_id":"DRV-TEST-002","pickup":"Test Point C","dropoff":"Test Point D","status":"active"}
            ],
            "identity": [
                {"identity_id":"ID-TEST-001","driver_id":"DRV-TEST-001","verification_status":"verified","method":"lab-only"},
                {"identity_id":"ID-TEST-002","driver_id":"DRV-TEST-002","verification_status":"pending","method":"lab-only"}
            ],
            "security-events": [
                {"event_id":"EVT-TEST-001","subject":"DRV-TEST-001","event_type":"login_success","result":"synthetic"},
                {"event_id":"EVT-TEST-002","subject":"DRV-TEST-003","event_type":"access_denied","result":"synthetic"}
            ]
        }
        try:
            cipher = _cipher(app)
        except RuntimeError as exc:
            return jsonify(error=str(exc)), 503
        created = datetime.now(timezone.utc).isoformat()
        ids = []
        try:
            with _database(app) as db:
                for name, records in samples.items():
                    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":")).encode("utf-8")
                    dataset_id = hashlib.sha256(os.urandom(32)).hexdigest()[:24]
                    db.execute(
                        "INSERT INTO datasets "
                        "(id,tenant_id,filename,content_type,row_count,sha256,encrypted_payload,uploaded_by,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (dataset_id, claims["tenant_id"], f"sanad-synthetic-{name}.json", "json",
                         len(records), hashlib.sha256(canonical).hexdigest(),
                         cipher.encrypt(canonical), claims.get("sub", "unknown"), created),
                    )
                    ids.append(dataset_id)
            return jsonify(status="seeded_encrypted", id=ids[0], dataset_ids=ids,
                           dataset_groups=list(samples.keys()), count=len(ids),
                           synthetic_data=True), 201
        except (OSError, sqlite3.Error):
            return jsonify(error="dataset_storage_unavailable"), 503

    @app.get("/api/admin/datasets/<dataset_id>/preview")
    def preview_dataset(dataset_id):
        claims, failure = admin_claims()
        if failure:
            return failure
        try:
            cipher = _cipher(app)
            with _connect(app) as db:
                row = db.execute(
                    "SELECT encrypted_payload FROM datasets WHERE id=? AND tenant_id=?",
                    (dataset_id, claims["tenant_id"]),
                ).fetchone()
            if row is None:
                return jsonify(error="dataset_not_found"), 404
            try:
                records = json.loads(cipher.decrypt(row["encrypted_payload"]).decode("utf-8"))
            except (InvalidToken, ValueError):
                return jsonify(error="dataset_integrity_or_key_failure"), 503
            return jsonify(records=records, synthetic_data=True), 200
        except RuntimeError as exc:
            return jsonify(error=str(exc)), 503
        except OSError:
            return jsonify(error="dataset_storage_unavailable"), 503
