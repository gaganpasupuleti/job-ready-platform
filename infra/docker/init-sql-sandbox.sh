#!/bin/bash
# Initialize SQL sandbox roles on first boot.
# POSTGRES_USER (jobready_sql_admin) is the bootstrap owner of this isolated instance.
# jobready_sql_runner is a non-superuser read-only executor for student queries.

set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jobready_sql_runner') THEN
        CREATE ROLE jobready_sql_runner LOGIN PASSWORD 'jobready_sql_dev'
          NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
      END IF;
    END
    \$\$;

    GRANT CONNECT ON DATABASE jobready_sql_sandbox TO jobready_sql_runner;

    -- Prevent runner from creating objects in public
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    REVOKE CREATE ON SCHEMA public FROM jobready_sql_runner;
    GRANT USAGE ON SCHEMA public TO jobready_sql_runner;

    -- Runner must not be able to create schemas
    REVOKE CREATE ON DATABASE jobready_sql_sandbox FROM PUBLIC;
    REVOKE CREATE ON DATABASE jobready_sql_sandbox FROM jobready_sql_runner;
EOSQL
