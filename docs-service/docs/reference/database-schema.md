# Database Schema Reference

Complete technical reference for the SaaS LiteLLM database schema. This system uses PostgreSQL with a multi-tenant architecture supporting organizations, teams, jobs, credits, and model group management.

## Overview

The database schema is organized into several functional areas:

- **Multi-tenancy**: Organizations and teams hierarchy
- **Job Tracking**: Jobs, LLM calls, and cost summaries
- **Credit System**: Credit allocation, usage tracking, and transactions
- **Model Groups**: Dynamic model routing with access control
- **Analytics**: Team usage summaries and webhook registrations

## Schema Diagram

```
organizations
    |
    +-- team_credits (1:N)
    |       |
    |       +-- credit_transactions (1:N)
    |
    +-- jobs (1:N)
            |
            +-- llm_calls (1:N)
            +-- job_cost_summaries (1:1)
            +-- credit_transactions (1:N)

model_groups
    |
    +-- model_group_models (1:N)
    +-- team_model_groups (N:M) -- teams
```

## Core Tables

### organizations

Represents top-level organizational entities in the multi-tenant hierarchy.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `organization_id` | VARCHAR(255) | PRIMARY KEY | Unique organization identifier |
| `name` | VARCHAR(500) | NOT NULL | Organization display name |
| `status` | VARCHAR(50) | DEFAULT 'active' | Status: active, suspended, deleted |
| `metadata` | JSONB | DEFAULT '{}' | Custom organization metadata |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp (auto-updated) |

**Indexes:**

- `idx_org_status` on `(status)`
- `idx_org_created` on `(created_at)`

**Triggers:**

- `update_organizations_updated_at` - Automatically updates `updated_at` on row modification

**Example:**

```sql
INSERT INTO organizations (organization_id, name, metadata)
VALUES ('org-acme', 'Acme Corporation', '{"industry": "technology"}');
```

---

### team_credits

Tracks credit allocation and usage for teams. Credits are the billing unit where 1 credit = 1 successfully completed job.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `team_id` | VARCHAR(255) | PRIMARY KEY | Team identifier |
| `organization_id` | VARCHAR(255) | FOREIGN KEY → organizations | Parent organization |
| `credits_allocated` | INTEGER | DEFAULT 0 | Total credits allocated to team |
| `credits_used` | INTEGER | DEFAULT 0 | Credits consumed by completed jobs |
| `credits_remaining` | INTEGER | COMPUTED STORED | Auto-calculated: allocated - used |
| `credit_limit` | INTEGER | NULLABLE | Optional hard limit (NULL = unlimited) |
| `auto_refill` | BOOLEAN | DEFAULT FALSE | Enable automatic credit refills |
| `refill_amount` | INTEGER | NULLABLE | Amount to refill when auto_refill enabled |
| `refill_period` | VARCHAR(50) | NULLABLE | Refill frequency: 'daily', 'weekly', 'monthly' |
| `last_refill_at` | TIMESTAMP | NULLABLE | Last automatic refill timestamp |
| `virtual_key` | VARCHAR(500) | NULLABLE | LiteLLM virtual API key for this team |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes:**

- `idx_team_credits_org` on `(organization_id)`
- `idx_team_credits_remaining` on `(credits_remaining)`
- `idx_team_credits_virtual_key` on `(virtual_key)`

**Computed Column:**

The `credits_remaining` column is a **generated stored column**:

```sql
credits_remaining INTEGER GENERATED ALWAYS AS (credits_allocated - credits_used) STORED
```

This ensures consistency and prevents manual manipulation.

**Triggers:**

- `update_team_credits_updated_at` - Auto-updates `updated_at` on modification

**Budget Modes:**

1. **Fixed Budget**: `credit_limit` set, `auto_refill = FALSE`
   - Team has a fixed allocation
   - Cannot use more than `credits_allocated`

2. **Unlimited Budget**: `credit_limit = NULL`
   - No hard limit on usage
   - Useful for enterprise customers

3. **Recurring Budget**: `auto_refill = TRUE`, `refill_amount` and `refill_period` set
   - Automatically refills credits on schedule
   - Useful for subscription-based billing

**Example:**

```sql
-- Create team with 1000 credits
INSERT INTO team_credits (team_id, organization_id, credits_allocated, virtual_key)
VALUES ('team-alpha', 'org-acme', 1000, 'sk-xxxxxxxxxxxxx');

-- Setup monthly auto-refill
UPDATE team_credits
SET auto_refill = TRUE,
    refill_amount = 1000,
    refill_period = 'monthly',
    last_refill_at = NOW()
WHERE team_id = 'team-alpha';
```

---

### credit_transactions

Audit log of all credit operations (allocations, deductions, refunds, adjustments).

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `transaction_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique transaction identifier |
| `team_id` | VARCHAR(255) | NOT NULL | Team the transaction applies to |
| `organization_id` | VARCHAR(255) | NULLABLE | Organization for reporting |
| `job_id` | UUID | FOREIGN KEY → jobs, NULLABLE | Associated job (for deductions) |
| `transaction_type` | VARCHAR(50) | NOT NULL | Type: 'deduction', 'allocation', 'refund', 'adjustment' |
| `credits_amount` | INTEGER | NOT NULL | Number of credits (positive for additions, negative for deductions) |
| `credits_before` | INTEGER | NOT NULL | Balance before transaction |
| `credits_after` | INTEGER | NOT NULL | Balance after transaction |
| `reason` | VARCHAR(500) | NULLABLE | Human-readable reason for transaction |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Transaction timestamp |

**Indexes:**

- `idx_credit_transactions_team` on `(team_id, created_at)`
- `idx_credit_transactions_job` on `(job_id)`
- `idx_credit_transactions_org` on `(organization_id, created_at)`
- `idx_credit_transactions_type` on `(transaction_type)`

**Transaction Types:**

- **deduction**: Credit removed for successful job completion
- **allocation**: New credits added to team
- **refund**: Credit returned (e.g., job failed after deduction)
- **adjustment**: Manual credit correction by admin

**Example:**

```sql
-- Deduction for completed job
INSERT INTO credit_transactions (
    team_id, organization_id, job_id, transaction_type,
    credits_amount, credits_before, credits_after, reason
) VALUES (
    'team-alpha', 'org-acme', 'job-uuid-123', 'deduction',
    1, 1000, 999, 'Job document_analysis completed successfully'
);
```

---

### jobs

Represents a business operation that may involve one or more LLM calls. Jobs are the core billing unit.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `job_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique job identifier |
| `team_id` | VARCHAR(255) | NOT NULL, INDEX | Team that owns this job |
| `user_id` | VARCHAR(255) | NULLABLE, INDEX | User who initiated the job |
| `job_type` | VARCHAR(100) | NOT NULL, INDEX | Job category (e.g., 'chat', 'document_analysis') |
| `status` | job_status | NOT NULL, DEFAULT 'pending', INDEX | Current status (enum) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW(), INDEX | Job creation time |
| `started_at` | TIMESTAMP | NULLABLE | When job moved to 'in_progress' |
| `completed_at` | TIMESTAMP | NULLABLE | When job finished (success or failure) |
| `job_metadata` | JSONB | DEFAULT '{}' | Custom application-specific data |
| `error_message` | VARCHAR(1000) | NULLABLE | Error description if failed |
| `organization_id` | VARCHAR(255) | FOREIGN KEY → organizations, INDEX | Parent organization |
| `external_task_id` | VARCHAR(255) | NULLABLE, INDEX | Reference to external system task ID |
| `credit_applied` | BOOLEAN | DEFAULT FALSE | Whether credit was deducted |
| `model_groups_used` | TEXT[] | DEFAULT '{}' | Array of model group names used |

**Status Enum:**

```sql
CREATE TYPE job_status AS ENUM (
    'pending',      -- Job created but not started
    'in_progress',  -- Job has started processing
    'completed',    -- Job finished successfully
    'failed',       -- Job encountered errors
    'cancelled'     -- Job was cancelled by user
);
```

**Indexes:**

- `idx_team_created` on `(team_id, created_at)`
- `idx_team_status` on `(team_id, status)`
- `idx_job_type_created` on `(job_type, created_at)`
- `idx_status` on `(status)`
- `idx_jobs_organization` on `(organization_id, created_at)`
- `idx_jobs_external_task` on `(external_task_id)`
- `idx_jobs_credit_applied` on `(credit_applied)`

**Credit Deduction Rules:**

Credits are deducted when:
1. `status = 'completed'` (not 'failed' or 'cancelled')
2. All associated LLM calls succeeded (no errors)
3. `credit_applied = FALSE` (prevents double-charging)

**Example:**

```sql
-- Create job
INSERT INTO jobs (team_id, job_type, organization_id, external_task_id, job_metadata)
VALUES (
    'team-alpha',
    'resume_analysis',
    'org-acme',
    'task-789',
    '{"resume_id": "res-456", "priority": "high"}'
);

-- Update to in_progress
UPDATE jobs
SET status = 'in_progress', started_at = NOW()
WHERE job_id = 'job-uuid-123';

-- Complete job
UPDATE jobs
SET status = 'completed',
    completed_at = NOW(),
    credit_applied = TRUE
WHERE job_id = 'job-uuid-123';
```

---

### llm_calls

Individual LLM API calls within a job. Tracks costs, performance, and usage metrics.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `call_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique call identifier |
| `job_id` | UUID | FOREIGN KEY → jobs ON DELETE CASCADE, INDEX | Parent job |
| `litellm_request_id` | VARCHAR(255) | UNIQUE, NULLABLE | LiteLLM's internal request ID |
| `model_used` | VARCHAR(100) | NULLABLE | Actual model that handled the request |
| `prompt_tokens` | INTEGER | DEFAULT 0 | Input tokens consumed |
| `completion_tokens` | INTEGER | DEFAULT 0 | Output tokens generated |
| `total_tokens` | INTEGER | DEFAULT 0 | Sum of prompt + completion tokens |
| `cost_usd` | NUMERIC(10,6) | DEFAULT 0.0 | Actual USD cost from LLM provider |
| `latency_ms` | INTEGER | NULLABLE | Request latency in milliseconds |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW(), INDEX | Call timestamp |
| `purpose` | VARCHAR(200) | NULLABLE | Description of call purpose |
| `request_data` | JSONB | NULLABLE | Full request payload (for debugging) |
| `response_data` | JSONB | NULLABLE | Full response payload (for debugging) |
| `error` | VARCHAR(1000) | NULLABLE | Error message if call failed |
| `model_group_used` | VARCHAR(100) | NULLABLE, INDEX | Model group name requested |
| `resolved_model` | VARCHAR(200) | NULLABLE, INDEX | Primary model resolved from group |

**Indexes:**

- `idx_job_id_created` on `(job_id, created_at)`
- `idx_created_at` on `(created_at)`
- `idx_llm_calls_model_group` on `(model_group_used)`
- `idx_llm_calls_resolved_model` on `(resolved_model)`

**Cost Calculation:**

The `cost_usd` field stores the actual cost charged by the LLM provider (via LiteLLM). This is separate from the credit system (1 credit per job), allowing you to track both:
- **Internal billing** (credits)
- **External costs** (actual USD from OpenAI/Anthropic/etc.)

**Example:**

```sql
INSERT INTO llm_calls (
    job_id, model_used, model_group_used, resolved_model,
    prompt_tokens, completion_tokens, total_tokens,
    cost_usd, latency_ms, purpose
) VALUES (
    'job-uuid-123',
    'gpt-4-turbo-2024-04-09',
    'ResumeAgent',
    'gpt-4-turbo',
    1250,
    450,
    1700,
    0.034000,
    2340,
    'Resume skills extraction'
);
```

---

### job_cost_summaries

Aggregated cost and performance metrics per job. Generated when job completes.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `job_id` | UUID | PRIMARY KEY, FOREIGN KEY → jobs ON DELETE CASCADE | Job identifier |
| `total_calls` | INTEGER | DEFAULT 0 | Total number of LLM calls |
| `successful_calls` | INTEGER | DEFAULT 0 | Calls that succeeded |
| `failed_calls` | INTEGER | DEFAULT 0 | Calls that failed with errors |
| `total_prompt_tokens` | INTEGER | DEFAULT 0 | Sum of all prompt tokens |
| `total_completion_tokens` | INTEGER | DEFAULT 0 | Sum of all completion tokens |
| `total_tokens` | INTEGER | DEFAULT 0 | Sum of all tokens |
| `total_cost_usd` | NUMERIC(12,6) | DEFAULT 0.0 | Total actual USD cost |
| `avg_latency_ms` | INTEGER | NULLABLE | Average latency across all calls |
| `total_duration_seconds` | INTEGER | NULLABLE | Job duration (completed_at - created_at) |
| `calculated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Summary calculation timestamp |

**Example:**

```sql
INSERT INTO job_cost_summaries (
    job_id, total_calls, successful_calls, failed_calls,
    total_prompt_tokens, total_completion_tokens, total_tokens,
    total_cost_usd, avg_latency_ms, total_duration_seconds
) VALUES (
    'job-uuid-123',
    3, 3, 0,
    3750, 1350, 5100,
    0.102000,
    2180,
    15
);
```

---

### team_usage_summaries

Aggregated team usage analytics by period (daily or monthly).

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Summary identifier |
| `team_id` | VARCHAR(255) | NOT NULL, INDEX | Team identifier |
| `period` | VARCHAR(50) | NOT NULL | Period string: "2024-10" or "2024-10-15" |
| `period_type` | VARCHAR(20) | DEFAULT 'monthly' | Type: 'daily' or 'monthly' |
| `total_jobs` | INTEGER | DEFAULT 0 | Total jobs in period |
| `successful_jobs` | INTEGER | DEFAULT 0 | Completed jobs |
| `failed_jobs` | INTEGER | DEFAULT 0 | Failed jobs |
| `cancelled_jobs` | INTEGER | DEFAULT 0 | Cancelled jobs |
| `total_cost_usd` | NUMERIC(12,2) | DEFAULT 0.0 | Total actual costs |
| `total_tokens` | INTEGER | DEFAULT 0 | Total tokens consumed |
| `job_type_breakdown` | JSONB | DEFAULT '{}' | Per-job-type statistics |
| `calculated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Calculation timestamp |

**Indexes:**

- `idx_team_period` on `(team_id, period)` UNIQUE

**Job Type Breakdown Format:**

```json
{
  "resume_analysis": {
    "count": 150,
    "cost_usd": 12.45
  },
  "document_parsing": {
    "count": 320,
    "cost_usd": 8.90
  }
}
```

**Example:**

```sql
INSERT INTO team_usage_summaries (
    team_id, period, period_type,
    total_jobs, successful_jobs, failed_jobs,
    total_cost_usd, total_tokens, job_type_breakdown
) VALUES (
    'team-alpha',
    '2024-10',
    'monthly',
    470, 455, 15,
    21.35,
    1250000,
    '{"resume_analysis": {"count": 150, "cost_usd": 12.45}, "document_parsing": {"count": 320, "cost_usd": 8.90}}'
);
```

---

## Model Group Tables

### model_groups

Defines named groups of models with primary and fallback configurations (e.g., "ResumeAgent", "ParsingAgent").

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `model_group_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique group identifier |
| `group_name` | VARCHAR(100) | UNIQUE, NOT NULL | Group name (e.g., "ResumeAgent") |
| `display_name` | VARCHAR(200) | NULLABLE | Human-readable name |
| `description` | TEXT | NULLABLE | Group description |
| `status` | VARCHAR(50) | DEFAULT 'active' | Status: active, inactive |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes:**

- `idx_model_group_name` on `(group_name)`
- `idx_model_group_status` on `(status)`

**Triggers:**

- `update_model_groups_updated_at` - Auto-updates `updated_at`

**Example:**

```sql
INSERT INTO model_groups (group_name, display_name, description)
VALUES (
    'ResumeAgent',
    'Resume Analysis Agent',
    'High-quality model for resume parsing and skills extraction'
);
```

---

### model_group_models

Maps models to groups with priority for fallback handling.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique mapping identifier |
| `model_group_id` | UUID | FOREIGN KEY → model_groups ON DELETE CASCADE, NOT NULL | Parent group |
| `model_name` | VARCHAR(200) | NOT NULL | LiteLLM model identifier |
| `priority` | INTEGER | DEFAULT 0 | 0 = primary, 1 = first fallback, 2 = second fallback |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether this model is currently enabled |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Indexes:**

- `idx_model_group_models_lookup` on `(model_group_id, priority, is_active)`
- `idx_model_group_models_group` on `(model_group_id)`

**Priority System:**

- **Priority 0**: Primary model (first choice)
- **Priority 1**: First fallback (if primary fails or unavailable)
- **Priority 2**: Second fallback
- **Priority N**: Nth fallback

**Example:**

```sql
-- Add primary model
INSERT INTO model_group_models (model_group_id, model_name, priority)
VALUES ('group-uuid-123', 'gpt-4-turbo', 0);

-- Add fallbacks
INSERT INTO model_group_models (model_group_id, model_name, priority)
VALUES
    ('group-uuid-123', 'gpt-4', 1),
    ('group-uuid-123', 'gpt-3.5-turbo', 2);
```

---

### team_model_groups

Junction table mapping teams to their assigned model groups (access control).

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique assignment identifier |
| `team_id` | VARCHAR(255) | NOT NULL | Team identifier |
| `model_group_id` | UUID | FOREIGN KEY → model_groups ON DELETE CASCADE, NOT NULL | Model group |
| `assigned_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Assignment timestamp |

**Indexes:**

- `idx_team_model_groups_team` on `(team_id)`
- `idx_team_model_groups_group` on `(model_group_id)`

**Constraints:**

- `unique_team_model_group` UNIQUE on `(team_id, model_group_id)` - Prevents duplicate assignments

**Example:**

```sql
-- Assign model group to team
INSERT INTO team_model_groups (team_id, model_group_id)
VALUES ('team-alpha', 'group-uuid-123');
```

---

## Additional Tables

### webhook_registrations

Webhook endpoints for job event notifications.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `webhook_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique webhook identifier |
| `team_id` | VARCHAR(255) | NOT NULL, INDEX | Team that owns webhook |
| `webhook_url` | VARCHAR(500) | NOT NULL | Webhook endpoint URL |
| `events` | JSONB | DEFAULT '[]' | Array of event types to trigger on |
| `is_active` | INTEGER | DEFAULT 1 | Active status (1=active, 0=inactive) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `last_triggered_at` | TIMESTAMP | NULLABLE | Last successful trigger |
| `auth_header` | VARCHAR(500) | NULLABLE | Optional authentication header |

**Indexes:**

- `idx_webhook_team_id` on `(team_id)`
- `idx_webhook_active` on `(is_active)`

**Event Types:**

- `job.created`
- `job.started`
- `job.completed`
- `job.failed`
- `job.cancelled`

**Example:**

```sql
INSERT INTO webhook_registrations (team_id, webhook_url, events, auth_header)
VALUES (
    'team-alpha',
    'https://api.acme.com/webhooks/llm-jobs',
    '["job.completed", "job.failed"]',
    'Bearer secret-webhook-token-xyz'
);
```

---

## Relationships

### Foreign Key Constraints

```sql
-- Organizations → Team Credits
ALTER TABLE team_credits
    ADD CONSTRAINT fk_team_credits_organization
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id);

-- Organizations → Jobs
ALTER TABLE jobs
    ADD CONSTRAINT fk_jobs_organization
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id);

-- Jobs → LLM Calls (cascade delete)
ALTER TABLE llm_calls
    ADD CONSTRAINT fk_llm_calls_job
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;

-- Jobs → Job Cost Summaries (cascade delete)
ALTER TABLE job_cost_summaries
    ADD CONSTRAINT fk_job_cost_summaries_job
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;

-- Jobs → Credit Transactions
ALTER TABLE credit_transactions
    ADD CONSTRAINT fk_credit_transactions_job
    FOREIGN KEY (job_id) REFERENCES jobs(job_id);

-- Model Groups → Model Group Models (cascade delete)
ALTER TABLE model_group_models
    ADD CONSTRAINT fk_model_group_models_group
    FOREIGN KEY (model_group_id) REFERENCES model_groups(model_group_id) ON DELETE CASCADE;

-- Model Groups → Team Model Groups (cascade delete)
ALTER TABLE team_model_groups
    ADD CONSTRAINT fk_team_model_groups_group
    FOREIGN KEY (model_group_id) REFERENCES model_groups(model_group_id) ON DELETE CASCADE;
```

### Cascade Behavior

- **Jobs deleted** → LLM calls and cost summaries auto-deleted (cascade)
- **Model groups deleted** → Model assignments and team mappings auto-deleted (cascade)
- **Organizations deleted** → No cascade (must manually clean up teams first)

---

## Migration Scripts

Migrations are located in `/scripts/migrations/` and should be run in order:

1. `001_create_job_tracking_tables.sql` - Core job tracking tables
2. `002_create_organizations.sql` - Organization hierarchy
3. `003_create_model_groups.sql` - Model group system
4. `004_create_team_model_groups.sql` - Team-model assignments
5. `005_create_credits_tables.sql` - Credit system
6. `006_extend_jobs_and_llm_calls.sql` - Add organization and model group fields
7. `007_add_virtual_key_to_team_credits.sql` - Add virtual key column

**Running Migrations:**

```bash
# Run all migrations
psql -U postgres -d saas_litellm -f scripts/migrations/001_create_job_tracking_tables.sql
psql -U postgres -d saas_litellm -f scripts/migrations/002_create_organizations.sql
# ... etc
```

---

## Performance Considerations

### Index Strategy

All high-traffic query patterns are covered by indexes:

- Team-based queries: `idx_team_created`, `idx_team_status`
- Time-range queries: `idx_created_at`, `idx_org_created`
- Job type analytics: `idx_job_type_created`
- Credit lookups: `idx_team_credits_remaining`, `idx_team_credits_virtual_key`
- Model group resolution: `idx_model_group_models_lookup`

### Query Optimization Tips

**Get team jobs with costs:**

```sql
SELECT
    j.*,
    jcs.total_cost_usd,
    jcs.total_tokens
FROM jobs j
LEFT JOIN job_cost_summaries jcs ON j.job_id = jcs.job_id
WHERE j.team_id = 'team-alpha'
AND j.created_at >= '2024-10-01'
ORDER BY j.created_at DESC
LIMIT 100;
```

**Get team credit balance:**

```sql
SELECT
    credits_allocated,
    credits_used,
    credits_remaining,
    virtual_key
FROM team_credits
WHERE team_id = 'team-alpha';
```

**Resolve model group:**

```sql
SELECT
    mgm.model_name,
    mgm.priority
FROM model_groups mg
JOIN model_group_models mgm ON mg.model_group_id = mgm.model_group_id
JOIN team_model_groups tmg ON mg.model_group_id = tmg.model_group_id
WHERE tmg.team_id = 'team-alpha'
AND mg.group_name = 'ResumeAgent'
AND mgm.is_active = TRUE
ORDER BY mgm.priority ASC;
```

---

## Backup and Maintenance

### Recommended Backup Strategy

```bash
# Full database backup
pg_dump -U postgres saas_litellm > backup_$(date +%Y%m%d).sql

# Backup specific tables
pg_dump -U postgres -t credit_transactions -t team_credits saas_litellm > credits_backup.sql
```

### Data Retention

Consider archiving old records:

- **llm_calls**: Archive calls older than 90 days to separate table
- **credit_transactions**: Keep all records for audit compliance
- **jobs**: Archive completed jobs older than 1 year
- **team_usage_summaries**: Keep all summaries (small table)

### Vacuum and Analyze

```sql
-- Regular maintenance
VACUUM ANALYZE jobs;
VACUUM ANALYZE llm_calls;
VACUUM ANALYZE credit_transactions;
```

---

## See Also

- [Credit System Reference](credit-system.md) - Detailed credit allocation and deduction logic
- [Model Resolution Reference](model-resolution.md) - Model group resolution flow
- [API Reference](../api-reference/overview.md) - API endpoints that use these tables
