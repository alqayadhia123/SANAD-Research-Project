#!/usr/bin/env python3
"""Validate SANAD synthetic test fixtures; no network or database access."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "test_data"
FILES = ("drivers", "wallets", "routes", "security_events", "scenarios")
ALLOWED_STATUS = {"NOT_RUN", "PASS", "FAIL", "BLOCKED"}
FORBIDDEN_KEYS = {"password", "client_secret", "access_token", "refresh_token", "authorization", "national_id", "phone", "email", "iban", "card_number"}
ID_RE = re.compile(r"^[A-Z]{3}-SYN-[0-9]{3}$")


def load(name):
    path = ROOT / f"{name}.json"
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError(f"{path.name}: root must be a JSON array")
    return value


def walk_forbidden(value, location="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"Forbidden sensitive field at {location}.{key}")
            walk_forbidden(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden(child, f"{location}[{index}]")


def unique_ids(rows, field, label):
    values = [row.get(field) for row in rows]
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{label}: missing/invalid {field}")
    if len(values) != len(set(values)):
        raise ValueError(f"{label}: duplicate {field}")
    return set(values)


def main():
    data = {name: load(name) for name in FILES}
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("classification") != "SYNTHETIC_ONLY":
        raise ValueError("Manifest classification must be SYNTHETIC_ONLY")
    for name, rows in data.items():
        walk_forbidden(rows, name)
        for row in rows:
            if row.get("data_classification", "SYNTHETIC") != "SYNTHETIC":
                raise ValueError(f"{name}: non-synthetic record detected")

    driver_ids = unique_ids(data["drivers"], "driver_id", "drivers")
    unique_ids(data["wallets"], "wallet_id", "wallets")
    unique_ids(data["routes"], "route_id", "routes")
    unique_ids(data["security_events"], "event_id", "security_events")
    unique_ids(data["scenarios"], "scenario_id", "scenarios")

    for group in ("wallets", "routes", "security_events", "scenarios"):
        for row in data[group]:
            if row.get("driver_id") not in driver_ids:
                raise ValueError(f"{group}: unresolved driver_id {row.get('driver_id')}")

    for row in data["wallets"]:
        amount = row.get("balance_minor_units")
        if not isinstance(amount, int) or amount < 0:
            raise ValueError(f"wallets: invalid integer minor-unit balance in {row['wallet_id']}")
        if not re.fullmatch(r"[A-Z]{3}", str(row.get("currency", ""))):
            raise ValueError(f"wallets: invalid ISO-style currency code in {row['wallet_id']}")

    for row in data["scenarios"]:
        status = row.get("status")
        if status not in ALLOWED_STATUS:
            raise ValueError(f"scenarios: invalid status {status}")
        if status in {"PASS", "FAIL"}:
            required = ("evidence_ref", "executed_at", "tested_commit_sha")
            if any(not row.get(key) for key in required):
                raise ValueError(f"{row['scenario_id']}: {status} requires {', '.join(required)}")
        if row.get("expected_http_status") is not None and not 100 <= row["expected_http_status"] <= 599:
            raise ValueError(f"{row['scenario_id']}: invalid expected HTTP status")

    print("SANAD synthetic test data validation: PASS")
    print("Records: " + ", ".join(f"{name}={len(rows)}" for name, rows in data.items()))
    print("No network/database calls were made; this validates fixture structure only.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
