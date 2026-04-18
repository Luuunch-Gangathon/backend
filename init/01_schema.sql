-- ─── Extensions ──────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS vector;

-- ─── Raw tables (migrated from SQLite) ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS companies (
    id   INTEGER PRIMARY KEY,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS suppliers (
    id   INTEGER PRIMARY KEY,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id         INTEGER PRIMARY KEY,
    sku        TEXT    NOT NULL,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    type       TEXT    NOT NULL CHECK (type IN ('finished-good', 'raw-material'))
);

CREATE TABLE IF NOT EXISTS boms (
    id                  INTEGER PRIMARY KEY,
    produced_product_id INTEGER NOT NULL UNIQUE REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS bom_components (
    bom_id              INTEGER NOT NULL REFERENCES boms(id),
    consumed_product_id INTEGER NOT NULL REFERENCES products(id),
    PRIMARY KEY (bom_id, consumed_product_id)
);

CREATE TABLE IF NOT EXISTS supplier_products (
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    PRIMARY KEY (supplier_id, product_id)
);

-- ─── Derived table: raw_material_map (Step 1) ────────────────────────────────
--
-- Flattened view of who buys which raw material in which finished product
-- and who currently supplies it. One row per (raw_material, supplier) pair
-- that appears in a BOM. Rebuilt by refresh_raw_material_map().

CREATE TABLE IF NOT EXISTS raw_material_map (
    id                   SERIAL      PRIMARY KEY,
    raw_material_name    TEXT        NOT NULL,  -- e.g. "vitamin-d3-cholecalciferol"
    company_id           INTEGER     REFERENCES companies(id),
    company_name         TEXT        NOT NULL,
    finished_product_id  INTEGER     REFERENCES products(id),
    finished_product_sku TEXT        NOT NULL,
    raw_material_id      INTEGER     REFERENCES products(id),
    raw_material_sku     TEXT        NOT NULL,
    supplier_id          INTEGER     REFERENCES suppliers(id),
    supplier_name        TEXT,                  -- NULL when no supplier is mapped
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rmm_raw_material_name ON raw_material_map(raw_material_name);
CREATE INDEX IF NOT EXISTS idx_rmm_company_id        ON raw_material_map(company_id);
CREATE INDEX IF NOT EXISTS idx_rmm_supplier_id       ON raw_material_map(supplier_id);

-- ─── Derived table: substitution_groups (Step 2) ─────────────────────────────
--
-- Dual-purpose table: (a) embedding store — one row per raw material with its
-- enriched spec (JSONB) and pgvector embedding so rag.py can do semantic search;
-- (b) grouping decisions — group_name/confidence/reasoning set later by
-- SubstitutionAgent once it clusters the embedded materials.

CREATE TABLE IF NOT EXISTS substitution_groups (
    id                SERIAL      PRIMARY KEY,
    raw_material_name TEXT        NOT NULL UNIQUE,  -- matches raw_material_map.raw_material_name
    group_name        TEXT,                          -- canonical group; set by SubstitutionAgent, NULL until then
    confidence        TEXT        CHECK (confidence IS NULL OR confidence IN ('high', 'medium', 'low')),
    reasoning         TEXT,                          -- LLM explanation
    spec              JSONB,                         -- enriched properties used to build embedding text
    embedding         vector(1536),                  -- pgvector embedding of raw_material_name or full spec
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sg_raw_material_name ON substitution_groups(raw_material_name);
CREATE INDEX IF NOT EXISTS idx_sg_group_name        ON substitution_groups(group_name);

-- Idempotent migrations for existing deployments (no-op on fresh DBs):
ALTER TABLE substitution_groups ADD COLUMN IF NOT EXISTS spec JSONB;
ALTER TABLE substitution_groups ALTER COLUMN group_name DROP NOT NULL;
ALTER TABLE substitution_groups ALTER COLUMN confidence DROP NOT NULL;
ALTER TABLE substitution_groups DROP CONSTRAINT IF EXISTS substitution_groups_confidence_check;
ALTER TABLE substitution_groups ADD CONSTRAINT substitution_groups_confidence_check
    CHECK (confidence IS NULL OR confidence IN ('high', 'medium', 'low'));

-- ─── Derived table: recommendations (Step 6) ─────────────────────────────────
--
-- Written by the agent after reasoning over raw_material_map + substitution_groups
-- + external web evidence. status tracks whether a recommendation is still valid
-- as the underlying data changes.

CREATE TABLE IF NOT EXISTS recommendations (
    id                        SERIAL      PRIMARY KEY,
    raw_material_group        TEXT        NOT NULL,
    recommended_supplier_id   INTEGER     REFERENCES suppliers(id),
    recommended_supplier_name TEXT,
    companies_affected        TEXT[]      NOT NULL DEFAULT '{}',
    compliance_status         JSONB,       -- {"NOW Foods": "verified", "Solgar": "check_needed"}
    confidence                TEXT        NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
    evidence_urls             TEXT[]      NOT NULL DEFAULT '{}',
    tradeoffs                 TEXT,
    status                    TEXT        NOT NULL DEFAULT 'active'
                              CHECK (status IN ('active', 'stale', 'superseded')),
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rec_raw_material_group ON recommendations(raw_material_group);
CREATE INDEX IF NOT EXISTS idx_rec_status             ON recommendations(status);

-- ─── Refresh function for raw_material_map ───────────────────────────────────
--
-- Call this whenever the raw tables change (new products, new suppliers, etc.).
-- Rebuilds raw_material_map from scratch using a regex to extract the raw material
-- name from the SKU format: RM-C{N}-{raw-material-name}-{8hexchars}

CREATE OR REPLACE FUNCTION refresh_raw_material_map() RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    TRUNCATE raw_material_map RESTART IDENTITY;

    INSERT INTO raw_material_map (
        raw_material_name,
        company_id,
        company_name,
        finished_product_id,
        finished_product_sku,
        raw_material_id,
        raw_material_sku,
        supplier_id,
        supplier_name,
        updated_at
    )
    SELECT
        -- Strip leading 'RM-C{N}-' and trailing '-{8 hex chars}'
        regexp_replace(
            regexp_replace(p_rm.sku, '^RM-C[0-9]+-', ''),
            '-[a-f0-9]{8}$', ''
        )                   AS raw_material_name,
        c.id                AS company_id,
        c.name              AS company_name,
        p_fg.id             AS finished_product_id,
        p_fg.sku            AS finished_product_sku,
        p_rm.id             AS raw_material_id,
        p_rm.sku            AS raw_material_sku,
        sp.supplier_id      AS supplier_id,
        s.name              AS supplier_name,
        now()               AS updated_at
    FROM      bom_components  bc
    JOIN      boms             b    ON bc.bom_id              = b.id
    JOIN      products         p_fg ON b.produced_product_id  = p_fg.id
    JOIN      companies        c    ON p_fg.company_id        = c.id
    JOIN      products         p_rm ON bc.consumed_product_id = p_rm.id
    LEFT JOIN supplier_products sp  ON sp.product_id          = p_rm.id
    LEFT JOIN suppliers         s   ON sp.supplier_id         = s.id
    WHERE p_rm.type = 'raw-material';
END;
$$;

-- ─── proposals ───────────────────────────────────────────────────────────────
--
-- Written by ProposalAgent. One row per consolidation opportunity.
-- Stores the full AI-generated recommendation: headline, evidence, tradeoffs,
-- conservative vs aggressive rollout plans, compliance requirements.
-- Read by GET /proposals and GET /proposals/{id}.
-- TBD: shape may change as ProposalAgent LLM reasoning is implemented.

CREATE TABLE IF NOT EXISTS proposals (
    id                              SERIAL      PRIMARY KEY,
    kind                            TEXT        NOT NULL CHECK (kind IN ('optimization', 'substitution')),
    headline                        TEXT        NOT NULL,
    summary                         TEXT        NOT NULL,
    raw_material_name               TEXT        NOT NULL,
    proposed_action                 TEXT        NOT NULL,
    companies_involved              INTEGER[]   NOT NULL DEFAULT '{}',
    current_supplier_ids            INTEGER[]   NOT NULL DEFAULT '{}',
    proposed_supplier_id            INTEGER     REFERENCES suppliers(id),
    proposed_substitute_rm_name     TEXT,
    fragmentation_score             INTEGER     NOT NULL DEFAULT 0,
    tradeoffs_gained                TEXT[]      NOT NULL DEFAULT '{}',
    tradeoffs_at_risk               TEXT[]      NOT NULL DEFAULT '{}',
    conservative_skus               TEXT[]      NOT NULL DEFAULT '{}',
    conservative_timeline           TEXT,
    aggressive_skus                 TEXT[]      NOT NULL DEFAULT '{}',
    aggressive_timeline             TEXT,
    evidence                        JSONB       NOT NULL DEFAULT '[]',
    estimated_impact                TEXT,
    compliance_requirements         JSONB       NOT NULL DEFAULT '[]',
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_proposals_fragmentation ON proposals(fragmentation_score DESC);

-- ─── substitutions ────────────────────────────────────────────────────────────
--
-- Written by SubstitutionAgent. Each row = one raw material that can replace another.
-- from_raw_material_id → to_raw_material_id with a plain-text reason.
-- Read by GET /substitutions.
-- TBD: may add confidence score and evidence_urls columns.

CREATE TABLE IF NOT EXISTS substitutions (
    id                   SERIAL      PRIMARY KEY,
    from_raw_material_id INTEGER     NOT NULL REFERENCES products(id),
    to_raw_material_id   INTEGER     NOT NULL REFERENCES products(id),
    score                INTEGER     NOT NULL,
    reason               TEXT        NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── agnes_suggestions ───────────────────────────────────────────────────────
--
-- Written by ProposalAgent alongside each proposal. Pre-seeded questions
-- shown as chips in the Agnes chat UI to help users start a conversation.
-- Scoped per proposal (CASCADE deletes when proposal is deleted).
-- Read by GET /agnes/suggestions?proposal_id=.

CREATE TABLE IF NOT EXISTS agnes_suggestions (
    id          SERIAL  PRIMARY KEY,
    proposal_id INTEGER NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    question    TEXT    NOT NULL
);
