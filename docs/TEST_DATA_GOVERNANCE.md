# SANAD Test Data Governance v1.0

## Purpose
A version-controlled, synthetic-only fixture library for repeatable research and API testing. These fixtures are not real user records, production seed data, or experimental findings.

## Data model
- `drivers.json`: synthetic driver/account subjects.
- `wallets.json`: synthetic wallet states and integer minor-unit balances.
- `routes.json`: synthetic route labels; no coordinates or live location data.
- `security_events.json`: illustrative security events.
- `scenarios.json`: test cases with expected outcomes and evidence fields.
- `manifest.json`: dataset identity, classification, schema version, and rules.

## Safe editing workflow
1. Edit a copy on a feature branch; do not edit the production database or deployment environment.
2. Preserve stable IDs and create new unique IDs for new records.
3. Keep all values synthetic. Do not add names, phone numbers, emails, national identifiers, credentials, tokens, payment details, or precise location data.
4. Preserve referential integrity: every `driver_id` in dependent records must exist in `drivers.json`.
5. Keep scenario status `NOT_RUN` until the test has actually been executed.
6. A scenario may be marked `PASS` or `FAIL` only when `evidence_ref`, `executed_at`, and `tested_commit_sha` are populated with verifiable evidence.
7. Run the validator before committing.

## Validation
From repository root:

```bash
python transport_poc/scripts/validate_test_data.py
```

The validator checks JSON syntax, synthetic classification, prohibited sensitive field names, unique identifiers, driver references, integer minor-unit balances, currency-code shape, scenario states, and evidence requirements. It does not prove application behavior or security efficacy.

## Change control and auditability
- Commit dataset changes with a descriptive message and review the diff.
- Do not overwrite historical experiment evidence; create a new dataset version or append a new experiment record.
- Keep test fixtures separate from live user data and secrets.
- Import into a database-backed environment only through a separately reviewed, authenticated, transactional import path with a dry-run report and backup/rollback plan.

## Current implementation boundary
This release provides editable, version-controlled JSON fixtures and a local structural validator. It does not yet provide a runtime CRUD administration panel, database import endpoint, immutable application audit log, or production data-management service. Those capabilities must be implemented and security-tested before enabling online editing.
