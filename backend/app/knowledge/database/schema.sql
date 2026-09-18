-- =================================================================================
-- Public Access to Digital Government Services — Knowledge Base
-- PostgreSQL DDL (versioned, normalized)
-- Target: PostgreSQL 13+
-- =================================================================================

CREATE SCHEMA IF NOT EXISTS govkb;
SET search_path TO govkb;

-- Metadata / versioning -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kb_meta (
    id              SERIAL PRIMARY KEY,
    kb_name         TEXT NOT NULL,
    kb_version      TEXT NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL,
    jurisdiction    JSONB,
    record_count    INTEGER,
    compliance      JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Reference tables ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS states (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    code        TEXT,
    level       TEXT
);

CREATE TABLE IF NOT EXISTS districts (
    id          TEXT PRIMARY KEY,
    state_id    TEXT REFERENCES states(id),
    name        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ministries (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    level       TEXT,
    state_id    TEXT REFERENCES states(id)
);

CREATE TABLE IF NOT EXISTS departments (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    ministry_id TEXT REFERENCES ministries(id)
);

CREATE TABLE IF NOT EXISTS categories (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    slug        TEXT
);

-- Services ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
    service_id          TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    category_id         TEXT REFERENCES categories(id),
    sub_category        TEXT,
    department_id       TEXT REFERENCES departments(id),
    ministry_id         TEXT REFERENCES ministries(id),
    government_level    TEXT,
    state_id            TEXT REFERENCES states(id),
    description         TEXT,
    eligibility         TEXT,
    benefits            TEXT,
    required_documents  JSONB,
    optional_documents  JSONB,
    application_mode    TEXT,
    application_steps   JSONB,
    processing_time     TEXT,
    fees                TEXT,
    validity            TEXT,
    official_portal     TEXT,
    official_apply_link TEXT,
    download_forms      TEXT,
    helpline_number     TEXT,
    email               TEXT,
    office_locator_info TEXT,
    faq                 JSONB,
    related_services    JSONB,
    keywords            JSONB,
    languages_available TEXT,
    last_updated        DATE,
    -- governance / lineage
    source_url          TEXT NOT NULL,
    collected_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    kb_version          TEXT NOT NULL,
    collection_method   TEXT,           -- api | official_portal | manual
    -- AI-ready metadata
    ai_summary          TEXT,
    ai_explanation      TEXT,
    common_questions    JSONB,
    common_mistakes     JSONB,
    search_keywords     JSONB,
    suggested_followups JSONB,
    UNIQUE (service_id, kb_version)
);

-- Child / junction tables ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    service_id  TEXT REFERENCES services(service_id),
    name        TEXT NOT NULL,
    mandatory   BOOLEAN,
    category    TEXT
);

CREATE TABLE IF NOT EXISTS application_steps (
    id            TEXT PRIMARY KEY,
    service_id    TEXT REFERENCES services(service_id),
    step_order    INTEGER,
    title         TEXT,
    description   TEXT
);

CREATE TABLE IF NOT EXISTS faqs (
    id          TEXT PRIMARY KEY,
    service_id  TEXT REFERENCES services(service_id),
    question    TEXT NOT NULL,
    answer      TEXT
);

CREATE TABLE IF NOT EXISTS helplines (
    id          TEXT PRIMARY KEY,
    service_id  TEXT REFERENCES services(service_id),
    name        TEXT,
    number      TEXT,
    email       TEXT,
    hours       TEXT
);

CREATE TABLE IF NOT EXISTS keywords (
    id          TEXT PRIMARY KEY,
    service_id  TEXT REFERENCES services(service_id),
    keyword     TEXT
);

CREATE TABLE IF NOT EXISTS related_services (
    id                  TEXT PRIMARY KEY,
    service_id          TEXT REFERENCES services(service_id),
    related_service_id  TEXT REFERENCES services(service_id)
);

CREATE TABLE IF NOT EXISTS schemes (
    id                  TEXT PRIMARY KEY,
    service_id          TEXT REFERENCES services(service_id),
    name                TEXT NOT NULL,
    category_id         TEXT REFERENCES categories(id),
    government_level    TEXT,
    official_portal     TEXT
);

-- Indexes for search --------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_services_category   ON services(category_id);
CREATE INDEX IF NOT EXISTS idx_services_level      ON services(government_level);
CREATE INDEX IF NOT EXISTS idx_services_state      ON services(state_id);
CREATE INDEX IF NOT EXISTS idx_services_name_trgm  ON services USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_keywords_kw         ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_faqs_q              ON faqs USING gin (question gin_trgm_ops);

-- Note: gin_trgm_ops requires  CREATE EXTENSION IF NOT EXISTS pg_trgm;  run once.
