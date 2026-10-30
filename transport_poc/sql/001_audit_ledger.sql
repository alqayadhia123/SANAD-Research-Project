-- SANAD tamper-evident audit ledger foundation.
-- Apply only to a dedicated application database after review.
-- Never store credentials, bearer tokens, personal data, or raw secrets here.

CREATE TABLE IF NOT EXISTS sanad_audit_events (
    sequence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_subject TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    outcome TEXT NOT NULL CHECK (outcome IN ('SUCCESS', 'DENIED', 'ERROR')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    previous_hash CHAR(64) NOT NULL CHECK (previous_hash ~ '^[0-9a-f]{64}$'),
    event_hash CHAR(64) NOT NULL CHECK (event_hash ~ '^[0-9a-f]{64}$'),
    hmac CHAR(64) NOT NULL CHECK (hmac ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS idx_sanad_audit_events_time
    ON sanad_audit_events (occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_sanad_audit_events_actor
    ON sanad_audit_events (actor_subject, occurred_at DESC);

-- Create a dedicated non-owner writer role in deployment.
-- Grant it INSERT and SELECT only. Do not grant UPDATE, DELETE, TRUNCATE,
-- ALTER, or table ownership. Keep the HMAC key outside the database.
-- Protect the latest chain head independently; otherwise a privileged DBA
-- could rewrite the entire chain and recompute hashes.
