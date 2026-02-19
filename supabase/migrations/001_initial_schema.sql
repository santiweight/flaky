-- Flaky Cloud Schema
-- Run this in your Supabase SQL editor to set up the database

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    api_key_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Runs table (one per flaky run command)
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project TEXT NOT NULL,
    branch TEXT NOT NULL,
    branch_type TEXT NOT NULL CHECK (branch_type IN ('origin', 'local')),
    commit_sha TEXT,
    case_name TEXT NOT NULL,
    num_generations INTEGER NOT NULL,
    total_tests INTEGER NOT NULL,
    total_passed INTEGER NOT NULL,
    success_rate NUMERIC(5, 2) NOT NULL,
    total_duration_ms NUMERIC NOT NULL,
    raw_report JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test results table (one per test per run, aggregated across generations)
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    test_name TEXT NOT NULL,
    passed INTEGER NOT NULL,
    total INTEGER NOT NULL,
    pass_rate NUMERIC(5, 2) NOT NULL,
    avg_duration_ms NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project);
CREATE INDEX IF NOT EXISTS idx_runs_project_branch ON runs(project, branch_type, branch);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_test_results_run_id ON test_results(run_id);

-- Row Level Security (RLS)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_results ENABLE ROW LEVEL SECURITY;

-- Policy: Allow inserts with valid API key (via service role or anon with apikey header)
-- For now, allow all authenticated requests. Tighten this based on your auth strategy.
CREATE POLICY "Allow insert runs" ON runs
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow select runs" ON runs
    FOR SELECT
    USING (true);

CREATE POLICY "Allow insert test_results" ON test_results
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow select test_results" ON test_results
    FOR SELECT
    USING (true);

-- Function to automatically populate test_results after a run is inserted
CREATE OR REPLACE FUNCTION populate_test_results()
RETURNS TRIGGER AS $$
DECLARE
    test_data JSONB;
    test_name TEXT;
    test_stats JSONB;
BEGIN
    FOR test_name, test_stats IN
        SELECT key, value FROM jsonb_each(NEW.raw_report->'per_test_breakdown')
    LOOP
        INSERT INTO test_results (run_id, test_name, passed, total, pass_rate, avg_duration_ms)
        VALUES (
            NEW.id,
            test_name,
            (test_stats->>'passed')::INTEGER,
            (test_stats->>'total')::INTEGER,
            (test_stats->>'rate')::NUMERIC,
            (NEW.raw_report->'per_test_timing'->test_name->>'avg_ms')::NUMERIC
        );
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-populate test_results
DROP TRIGGER IF EXISTS trigger_populate_test_results ON runs;
CREATE TRIGGER trigger_populate_test_results
    AFTER INSERT ON runs
    FOR EACH ROW
    EXECUTE FUNCTION populate_test_results();

-- Useful views for dashboards

-- Latest run per branch
CREATE OR REPLACE VIEW latest_runs_per_branch AS
SELECT DISTINCT ON (project, branch_type, branch)
    id,
    project,
    branch,
    branch_type,
    commit_sha,
    case_name,
    success_rate,
    total_tests,
    total_passed,
    created_at
FROM runs
ORDER BY project, branch_type, branch, created_at DESC;

-- Test reliability over time (for a specific project/branch)
CREATE OR REPLACE VIEW test_reliability_trend AS
SELECT
    r.project,
    r.branch_type,
    r.branch,
    r.created_at::DATE as run_date,
    AVG(r.success_rate) as avg_success_rate,
    COUNT(*) as run_count
FROM runs r
GROUP BY r.project, r.branch_type, r.branch, r.created_at::DATE
ORDER BY r.project, r.branch_type, r.branch, run_date DESC;
