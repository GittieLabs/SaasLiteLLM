-- Team Model Groups Table Migration
-- Maps which model groups are assigned to which teams

-- Team Model Groups table (assignment/junction table)
CREATE TABLE IF NOT EXISTS team_model_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    model_group_id UUID NOT NULL REFERENCES model_groups(model_group_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_team_model_group UNIQUE(team_id, model_group_id)
);

CREATE INDEX idx_team_model_groups_team ON team_model_groups(team_id);
CREATE INDEX idx_team_model_groups_group ON team_model_groups(model_group_id);

-- Verify table created
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'team_model_groups';
