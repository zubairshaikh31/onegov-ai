-- OneGov AI - PostgreSQL Initialization
-- Runs automatically when the container first starts.

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- trigram index for ILIKE search
CREATE EXTENSION IF NOT EXISTS "unaccent";   -- normalize accented characters

-- Create a read-only user for analytics/reporting (principle of least privilege)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'onegov_readonly') THEN
        CREATE ROLE onegov_readonly LOGIN PASSWORD 'readonly_secret';
        GRANT CONNECT ON DATABASE onegov_ai TO onegov_readonly;
        GRANT USAGE ON SCHEMA public TO onegov_readonly;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO onegov_readonly;
    END IF;
END
$$;
