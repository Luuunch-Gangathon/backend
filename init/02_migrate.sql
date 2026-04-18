-- Migration: relax NOT NULL on substitution_groups columns added in schema v1.
-- CREATE TABLE IF NOT EXISTS is idempotent and won't apply column changes to
-- existing tables, so teammates with a persistent volume need this to run.
ALTER TABLE substitution_groups ALTER COLUMN group_name DROP NOT NULL;
ALTER TABLE substitution_groups ALTER COLUMN confidence DROP NOT NULL;
ALTER TABLE substitution_groups ADD COLUMN IF NOT EXISTS spec JSONB;
