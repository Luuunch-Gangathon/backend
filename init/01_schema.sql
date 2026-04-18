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
-- Populated by the agent via LLM reasoning. Groups raw material names that are
-- functionally interchangeable. The embedding column is reserved for semantic
-- similarity search (pgvector) so future queries can find similar raw materials
-- even when spelled differently.

CREATE TABLE IF NOT EXISTS substitution_groups (
    id                SERIAL      PRIMARY KEY,
    raw_material_name TEXT        NOT NULL UNIQUE,  -- matches raw_material_map.raw_material_name
    group_name        TEXT        NOT NULL,          -- canonical group, e.g. "vitamin-d3"
    confidence        TEXT        NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
    reasoning         TEXT,                          -- LLM explanation
    embedding         vector(1536),                  -- pgvector embedding of raw_material_name
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sg_raw_material_name ON substitution_groups(raw_material_name);
CREATE INDEX IF NOT EXISTS idx_sg_group_name        ON substitution_groups(group_name);

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
