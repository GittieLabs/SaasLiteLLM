# Cost Transparency & Profit Margins

The Admin Dashboard provides comprehensive cost transparency features that enable you to track provider costs, client revenue, and profit margins in real-time. This guide covers how to configure and use these features effectively.

## Overview

Cost transparency features include:

- **Dual Cost Tracking**: Separate tracking of provider costs vs. client costs
- **Profit Margin Configuration**: Set markup percentages per team
- **Real-Time Metrics**: Live cost and profit calculations
- **Visual Cost Breakdown**: Color-coded displays in the dashboard
- **Job-Level Details**: Per-call cost analysis
- **Analytics Integration**: SQL queries for profitability analysis

## Understanding the Cost Model

### Cost Components

Every LLM call tracks multiple cost dimensions:

```
Provider Cost (RED) → What you pay to OpenAI/Anthropic/etc
    ↓
Client Cost (GREEN) → What your client pays you
    ↓
Profit (BLUE) → Your margin (Client Cost - Provider Cost)
```

### How Costs Are Calculated

**1. Provider Cost**
```python
provider_cost_usd = (input_tokens / 1_000_000) * model_pricing_input + \
                   (output_tokens / 1_000_000) * model_pricing_output
```

**2. Client Cost (with markup)**
```python
client_cost_usd = provider_cost_usd * (1 + cost_markup_percentage / 100)
```

**3. Profit**
```python
profit_usd = client_cost_usd - provider_cost_usd
profit_margin_percent = (profit_usd / provider_cost_usd) * 100
```

### Example Calculation

```
Input tokens: 500 (@ $0.003 / 1K tokens)
Output tokens: 200 (@ $0.015 / 1K tokens)
Markup: 50%

Provider cost: (500/1000 * 0.003) + (200/1000 * 0.015) = $0.0045
Client cost: $0.0045 * 1.5 = $0.00675
Profit: $0.00675 - $0.0045 = $0.00225 (50% margin)
```

## Configuring Profit Margins

### Via API

Use the Teams API to configure markup percentages:

```bash
curl -X PATCH http://localhost:8003/api/teams/acme-engineering/markup \
  -H "Authorization: Bearer sk-platform-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_markup_percentage": 50.00,
    "budget_mode": "consumption_usd",
    "credits_per_dollar": 10.0
  }'
```

### Via SQL (Direct Database)

```sql
-- Set 50% markup for a specific team
UPDATE team_credits
SET cost_markup_percentage = 50.00
WHERE team_id = 'acme-engineering';

-- Set different markup tiers
UPDATE team_credits
SET cost_markup_percentage = CASE
    WHEN credits_allocated >= 10000 THEN 30.00  -- Enterprise: 30%
    WHEN credits_allocated >= 1000 THEN 40.00   -- Professional: 40%
    ELSE 50.00                                   -- Standard: 50%
END;
```

### Budget Modes

Configure how credits are consumed:

**1. Job-Based (Default)**
```json
{
  "budget_mode": "job_based"
}
```
- 1 credit = 1 completed job
- Simple, predictable billing
- Recommended for fixed-price contracts

**2. Consumption-Based (USD)**
```json
{
  "budget_mode": "consumption_usd",
  "credits_per_dollar": 10.0
}
```
- Credits deducted based on client_cost_usd
- Example: $1.00 client cost = 10 credits
- Recommended for usage-based billing

**3. Consumption-Based (Tokens)**
```json
{
  "budget_mode": "consumption_tokens",
  "tokens_per_credit": 10000
}
```
- Credits deducted based on total tokens
- Example: 10,000 tokens = 1 credit
- Recommended for token-limited scenarios

## Using the Admin Dashboard

### Dashboard Color Coding

The dashboard uses consistent color coding for cost transparency:

- **RED**: Provider costs (what you pay)
- **GREEN**: Client revenue (what they pay)
- **BLUE**: Profit (your margin)

### Job Details Page

Navigate to: **Teams → [Team] → Jobs → [Job ID]**

The job details page shows:

**Cost Summary Card**
```
┌─────────────────────────────────────┐
│ Cost Summary                        │
├─────────────────────────────────────┤
│ Provider Cost:    $0.0045 (RED)     │
│ Client Cost:      $0.00675 (GREEN)  │
│ Profit:           $0.00225 (BLUE)   │
│ Markup:           50%                │
└─────────────────────────────────────┘
```

**Per-Call Breakdown**
```
Call #1: gpt-4-turbo
├─ Input tokens:      500 tokens
├─ Output tokens:     200 tokens
├─ Provider cost:     $0.0045
├─ Client cost:       $0.00675
└─ Profit:            $0.00225
```

### Teams Overview Page

Navigate to: **Teams → [Team ID]**

Shows aggregated metrics:

```
┌─────────────────────────────────────┐
│ Team: acme-engineering              │
├─────────────────────────────────────┤
│ Total Provider Cost:   $125.50      │
│ Total Client Revenue:  $188.25      │
│ Total Profit:          $62.75       │
│ Profit Margin:         50.0%        │
│ Markup Configured:     50%          │
└─────────────────────────────────────┘
```

### Accessing the Dashboard

**Prerequisites:**
- Admin credentials (owner, admin, or viewer role)
- Browser access to admin panel URL

**Steps:**
1. Navigate to admin panel (e.g., `https://your-admin-panel.railway.app`)
2. Log in with admin credentials
3. Navigate to **Teams** section
4. Select a team to view aggregated metrics
5. Click on a job to see detailed cost breakdown

## Analytics & Reporting

### SQL Queries for Profitability Analysis

**1. Team Profitability Report**
```sql
SELECT
    tc.team_id,
    tc.cost_markup_percentage,
    COUNT(DISTINCT j.job_id) as total_jobs,
    COUNT(lc.call_id) as total_calls,
    SUM(lc.provider_cost_usd) as total_provider_cost,
    SUM(lc.client_cost_usd) as total_client_revenue,
    SUM(lc.client_cost_usd - lc.provider_cost_usd) as total_profit,
    ROUND(
        (SUM(lc.client_cost_usd - lc.provider_cost_usd) /
         NULLIF(SUM(lc.provider_cost_usd), 0)) * 100,
        2
    ) as profit_margin_percent
FROM team_credits tc
JOIN jobs j ON j.team_id = tc.team_id
JOIN llm_calls lc ON lc.job_id = j.job_id
WHERE j.created_at >= NOW() - INTERVAL '30 days'
GROUP BY tc.team_id, tc.cost_markup_percentage
ORDER BY total_profit DESC;
```

**2. Model Profitability Analysis**
```sql
SELECT
    lc.model,
    COUNT(lc.call_id) as call_count,
    SUM(lc.provider_cost_usd) as provider_cost,
    SUM(lc.client_cost_usd) as client_revenue,
    SUM(lc.client_cost_usd - lc.provider_cost_usd) as profit,
    ROUND(
        (SUM(lc.client_cost_usd - lc.provider_cost_usd) /
         NULLIF(SUM(lc.provider_cost_usd), 0)) * 100,
        2
    ) as profit_margin_percent,
    ROUND(AVG(lc.client_cost_usd - lc.provider_cost_usd), 6) as avg_profit_per_call
FROM llm_calls lc
JOIN jobs j ON j.job_id = lc.job_id
WHERE j.created_at >= NOW() - INTERVAL '30 days'
    AND lc.provider_cost_usd IS NOT NULL
GROUP BY lc.model
ORDER BY profit DESC;
```

**3. Daily Profit Trends**
```sql
SELECT
    DATE(j.created_at) as date,
    COUNT(DISTINCT j.job_id) as jobs,
    SUM(lc.provider_cost_usd) as provider_cost,
    SUM(lc.client_cost_usd) as client_revenue,
    SUM(lc.client_cost_usd - lc.provider_cost_usd) as profit
FROM jobs j
JOIN llm_calls lc ON lc.job_id = j.job_id
WHERE j.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(j.created_at)
ORDER BY date DESC;
```

**4. Organization-Level Profitability**
```sql
SELECT
    o.organization_id,
    o.name,
    COUNT(DISTINCT tc.team_id) as team_count,
    COUNT(DISTINCT j.job_id) as total_jobs,
    SUM(lc.provider_cost_usd) as total_provider_cost,
    SUM(lc.client_cost_usd) as total_client_revenue,
    SUM(lc.client_cost_usd - lc.provider_cost_usd) as total_profit,
    ROUND(
        (SUM(lc.client_cost_usd - lc.provider_cost_usd) /
         NULLIF(SUM(lc.provider_cost_usd), 0)) * 100,
        2
    ) as profit_margin_percent
FROM organizations o
JOIN team_credits tc ON tc.organization_id = o.organization_id
JOIN jobs j ON j.team_id = tc.team_id
JOIN llm_calls lc ON lc.job_id = j.job_id
WHERE j.created_at >= NOW() - INTERVAL '30 days'
GROUP BY o.organization_id, o.name
ORDER BY total_profit DESC;
```

### Exporting Data

**Via psql:**
```bash
PGPASSWORD=your_password psql -h localhost -U postgres -d saas_llm_db \
  -c "COPY (SELECT...) TO STDOUT WITH CSV HEADER" > profitability_report.csv
```

**Via Python:**
```python
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host="localhost",
    database="saas_llm_db",
    user="postgres",
    password="your_password"
)

query = """
SELECT
    tc.team_id,
    SUM(lc.client_cost_usd - lc.provider_cost_usd) as total_profit
FROM team_credits tc
JOIN jobs j ON j.team_id = tc.team_id
JOIN llm_calls lc ON lc.job_id = j.job_id
GROUP BY tc.team_id
"""

df = pd.read_sql(query, conn)
df.to_csv('profitability.csv', index=False)
conn.close()
```

## Best Practices

### 1. Markup Strategy

**Volume-Based Pricing:**
```sql
-- Automatically adjust markup based on usage
UPDATE team_credits
SET cost_markup_percentage = CASE
    WHEN credits_used >= 100000 THEN 25.00  -- Heavy users: 25%
    WHEN credits_used >= 10000 THEN 35.00   -- Medium users: 35%
    WHEN credits_used >= 1000 THEN 45.00    -- Light users: 45%
    ELSE 50.00                               -- New users: 50%
END;
```

**Tiered Pricing:**
```python
# In your application logic
def calculate_markup(team_tier):
    markup_tiers = {
        'enterprise': 30.00,
        'professional': 40.00,
        'startup': 50.00,
        'free': 0.00  # No markup for free tier
    }
    return markup_tiers.get(team_tier, 50.00)
```

### 2. Cost Monitoring

**Set Up Alerts:**
```sql
-- Find teams with low profit margins
SELECT
    tc.team_id,
    tc.cost_markup_percentage,
    ROUND(
        (SUM(lc.client_cost_usd - lc.provider_cost_usd) /
         NULLIF(SUM(lc.provider_cost_usd), 0)) * 100,
        2
    ) as actual_margin
FROM team_credits tc
JOIN jobs j ON j.team_id = tc.team_id
JOIN llm_calls lc ON lc.job_id = j.job_id
GROUP BY tc.team_id, tc.cost_markup_percentage
HAVING (SUM(lc.client_cost_usd - lc.provider_cost_usd) /
        NULLIF(SUM(lc.provider_cost_usd), 0)) * 100 < 30;
```

### 3. Regular Audits

**Monthly Profitability Review:**
```sql
-- Generate monthly profitability report
SELECT
    TO_CHAR(j.created_at, 'YYYY-MM') as month,
    tc.team_id,
    SUM(lc.provider_cost_usd) as provider_cost,
    SUM(lc.client_cost_usd) as client_revenue,
    SUM(lc.client_cost_usd - lc.provider_cost_usd) as profit
FROM team_credits tc
JOIN jobs j ON j.team_id = tc.team_id
JOIN llm_calls lc ON lc.job_id = j.job_id
GROUP BY TO_CHAR(j.created_at, 'YYYY-MM'), tc.team_id
ORDER BY month DESC, profit DESC;
```

### 4. Data Integrity

**Verify Cost Calculations:**
```sql
-- Check for missing cost data
SELECT
    j.job_id,
    j.team_id,
    j.status,
    COUNT(lc.call_id) as call_count,
    COUNT(lc.provider_cost_usd) as calls_with_provider_cost,
    COUNT(lc.client_cost_usd) as calls_with_client_cost
FROM jobs j
LEFT JOIN llm_calls lc ON lc.job_id = j.job_id
WHERE j.status = 'completed'
GROUP BY j.job_id, j.team_id, j.status
HAVING COUNT(lc.call_id) != COUNT(lc.provider_cost_usd)
    OR COUNT(lc.call_id) != COUNT(lc.client_cost_usd);
```

## Troubleshooting

### Issue: Costs Not Displaying

**Symptoms:**
- Dashboard shows $0.00 for provider/client costs
- Job details missing cost information

**Solutions:**

1. **Check database migration:**
```bash
# Verify cost fields exist
psql -d saas_llm_db -c "
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'llm_calls'
        AND column_name IN (
            'provider_cost_usd',
            'client_cost_usd',
            'model_pricing_input',
            'model_pricing_output'
        );"
```

2. **Check for NULL values:**
```sql
SELECT COUNT(*) as calls_without_costs
FROM llm_calls
WHERE provider_cost_usd IS NULL
    OR client_cost_usd IS NULL;
```

3. **Verify markup configuration:**
```sql
SELECT team_id, cost_markup_percentage, budget_mode
FROM team_credits
WHERE team_id = 'your-team-id';
```

### Issue: Incorrect Profit Margins

**Symptoms:**
- Profit margin doesn't match configured markup
- Negative profit margins

**Solutions:**

1. **Recalculate client costs:**
```sql
UPDATE llm_calls lc
SET client_cost_usd = lc.provider_cost_usd *
    (1 + (
        SELECT cost_markup_percentage / 100.0
        FROM team_credits tc
        JOIN jobs j ON j.team_id = tc.team_id
        WHERE j.job_id = lc.job_id
    ))
WHERE lc.provider_cost_usd IS NOT NULL;
```

2. **Check for data inconsistencies:**
```sql
SELECT
    lc.call_id,
    lc.provider_cost_usd,
    lc.client_cost_usd,
    tc.cost_markup_percentage,
    -- Expected client cost
    lc.provider_cost_usd * (1 + tc.cost_markup_percentage / 100.0) as expected_client_cost,
    -- Difference
    lc.client_cost_usd - (lc.provider_cost_usd * (1 + tc.cost_markup_percentage / 100.0)) as diff
FROM llm_calls lc
JOIN jobs j ON j.job_id = lc.job_id
JOIN team_credits tc ON tc.team_id = j.team_id
WHERE ABS(lc.client_cost_usd -
    (lc.provider_cost_usd * (1 + tc.cost_markup_percentage / 100.0))) > 0.0001;
```

### Issue: Dashboard Not Loading Costs

**Symptoms:**
- Loading spinner indefinitely
- Network errors in browser console

**Solutions:**

1. **Check API endpoint:**
```bash
# Test job details endpoint
curl http://localhost:8003/api/jobs/your-job-id \
  -H "Authorization: Bearer your-token"
```

2. **Verify admin panel environment:**
```bash
# Check NEXT_PUBLIC_API_URL is set correctly
cat admin-panel/.env.local | grep NEXT_PUBLIC_API_URL
```

3. **Check browser console for errors:**
```javascript
// Look for null reference errors
Cannot read properties of undefined (reading 'toFixed')
```

Fix by adding null coalescing:
```typescript
const providerCost = call.provider_cost_usd ?? call.cost_usd ?? 0;
const clientCost = call.client_cost_usd ?? call.cost_usd ?? 0;
```

## Database Schema Reference

### team_credits Table

```sql
CREATE TABLE team_credits (
    team_id VARCHAR(255) PRIMARY KEY,
    organization_id VARCHAR(255),
    cost_markup_percentage NUMERIC(5, 2) DEFAULT 0.00,
    budget_mode VARCHAR(50) DEFAULT 'job_based',
    credits_per_dollar NUMERIC(10, 2) DEFAULT 10.0,
    tokens_per_credit INTEGER DEFAULT 10000,
    status VARCHAR(20) DEFAULT 'active',
    -- ... other fields
);
```

### llm_calls Table

```sql
CREATE TABLE llm_calls (
    call_id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(job_id),

    -- Token tracking
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- Pricing rates
    model_pricing_input NUMERIC(10, 6),    -- $ per 1M input tokens
    model_pricing_output NUMERIC(10, 6),   -- $ per 1M output tokens

    -- Cost breakdown
    input_cost_usd NUMERIC(10, 8),         -- Input token cost
    output_cost_usd NUMERIC(10, 8),        -- Output token cost
    provider_cost_usd NUMERIC(10, 8),      -- Total provider cost
    client_cost_usd NUMERIC(10, 8),        -- Total client cost (with markup)

    -- ... other fields
);
```

## API Integration

For API details on configuring profit margins, see:

- [Teams API - Configure Profit Margin](../api-reference/teams.md#configure-team-profit-margin)
- [Credit System Reference](../reference/credit-system.md#cost-transparency--profit-margins)

## See Also

- [Teams Management](teams.md) - Team configuration and management
- [Credits Management](credits.md) - Credit allocation and tracking
- [Monitoring Guide](monitoring.md) - System monitoring and alerts
- [Organizations](organizations.md) - Organization-level management
