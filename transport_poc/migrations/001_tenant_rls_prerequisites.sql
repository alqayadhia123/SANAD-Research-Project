-- SANAD P1 tenant isolation prerequisite.
-- This migration intentionally FAILS if the expected tenant-scoped tables or
-- tenant_id columns do not exist. It must be applied with a migration-owner
-- role; the runtime API role must be a separate non-owner, non-superuser role
-- without BYPASSRLS. The current wallet PoC has no persistence integration,
-- so do not apply this migration until the real schema and DB role are provisioned.
BEGIN;

CREATE OR REPLACE FUNCTION sanad_set_tenant_context(p_tenant text)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_tenant IS NULL OR p_tenant !~ '^[a-z][a-z0-9-]{2,63}$' THEN
        RAISE EXCEPTION 'invalid tenant context' USING ERRCODE = '22023';
    END IF;
    -- true = transaction-local; connection-pool reuse cannot retain the tenant.
    PERFORM set_config('app.current_tenant', p_tenant, true);
END;
$$;

DO $$
DECLARE
    target_table text;
    required_tables text[] := ARRAY['drivers', 'sessions', 'audit_logs'];
BEGIN
    FOREACH target_table IN ARRAY required_tables LOOP
        IF to_regclass(format('public.%I', target_table)) IS NULL THEN
            RAISE EXCEPTION 'Required tenant table public.% does not exist; migration aborted', target_table;
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = target_table
              AND column_name = 'tenant_id'
        ) THEN
            RAISE EXCEPTION 'Required column public.%.tenant_id does not exist; migration aborted', target_table;
        END IF;
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', target_table);
        EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', target_table);
        EXECUTE format('DROP POLICY IF EXISTS sanad_tenant_isolation ON public.%I', target_table);
        EXECUTE format(
            'CREATE POLICY sanad_tenant_isolation ON public.%I
             USING (tenant_id = current_setting(''app.current_tenant'', true))
             WITH CHECK (tenant_id = current_setting(''app.current_tenant'', true))',
            target_table
        );
    END LOOP;
END;
$$;

COMMIT;
