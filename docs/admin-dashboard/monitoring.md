# Monitoring & Analytics

Monitor system health, track usage metrics, analyze credit consumption, and set up alerts for your SaaS LiteLLM platform.

## Overview

The monitoring system provides comprehensive insights into:

- System health and performance
- Usage metrics and analytics
- Credit consumption tracking
- Cost analysis
- Team activity monitoring
- Performance metrics
- Alert notifications

## Dashboard Overview

### Access the Monitoring Dashboard

**Local Development:**
```
http://localhost:3002/monitoring
```

**Production:**
```
https://your-admin-dashboard.com/monitoring
```

### Key Metrics at a Glance

The monitoring dashboard displays:

1. **Platform Health**
   - API uptime status
   - Database connection health
   - LiteLLM proxy status
   - Average response times

2. **Usage Statistics**
   - Total jobs today/this month
   - Active teams count
   - Total API calls
   - Token consumption

3. **Financial Metrics**
   - Total costs (USD)
   - Credits allocated vs. used
   - Cost per team breakdown
   - Revenue analytics

4. **Performance Indicators**
   - Average latency
   - Success/failure rates
   - Model usage distribution
   - Error rates by type

## System Health Monitoring

### Health Check Endpoint

The SaaS API provides a health check endpoint:

```bash
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "service": "saas-llm-api"
}
```

### Component Health Checks

Monitor all system components:

```python
# health_check.py
import httpx
from sqlalchemy import create_engine, text

async def check_system_health():
    """
    Comprehensive health check for all system components
    """
    health_status = {
        "saas_api": False,
        "litellm_proxy": False,
        "database": False,
        "overall": "unhealthy"
    }

    # 1. Check SaaS API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8003/health")
            health_status["saas_api"] = response.status_code == 200
    except Exception as e:
        print(f"SaaS API check failed: {e}")

    # 2. Check LiteLLM Proxy
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8002/health")
            health_status["litellm_proxy"] = response.status_code == 200
    except Exception as e:
        print(f"LiteLLM Proxy check failed: {e}")

    # 3. Check Database
    try:
        engine = create_engine("postgresql://...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            health_status["database"] = result.fetchone()[0] == 1
    except Exception as e:
        print(f"Database check failed: {e}")

    # Overall health
    if all([health_status["saas_api"], health_status["litellm_proxy"], health_status["database"]]):
        health_status["overall"] = "healthy"
    elif any([health_status["saas_api"], health_status["litellm_proxy"], health_status["database"]]):
        health_status["overall"] = "degraded"

    return health_status

# Usage
health = await check_system_health()
print(health)
```

**Schedule health checks:**

```bash
# crontab -e
*/5 * * * * python /path/to/health_check.py >> /var/log/health.log 2>&1
```

### Real-Time Health Dashboard

```jsx
// components/HealthDashboard.jsx
import { useEffect, useState } from 'react';

export function HealthDashboard() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const checkHealth = async () => {
      const response = await fetch('/api/health-check');
      const data = await response.json();
      setHealth(data);
    };

    // Check health every 30 seconds
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="health-dashboard">
      <ServiceStatus name="SaaS API" status={health?.saas_api} />
      <ServiceStatus name="LiteLLM Proxy" status={health?.litellm_proxy} />
      <ServiceStatus name="Database" status={health?.database} />
      <OverallHealth status={health?.overall} />
    </div>
  );
}
```

## Usage Metrics & Analytics

### Team Usage Summary

Get comprehensive usage statistics for any team:

**API Endpoint:**

```bash
GET /api/teams/{team_id}/usage?period={period}
Authorization: Bearer {virtual_key}
```

**Parameters:**
- `period`: Format "YYYY-MM" (e.g., "2025-10") or "YYYY-MM-DD"

**Example Request:**

```bash
curl -X GET "http://localhost:8003/api/teams/team_abc123/usage?period=2025-10" \
  -H "Authorization: Bearer sk-team-key-abc123"
```

**Response:**

```json
{
  "team_id": "team_abc123",
  "period": "2025-10",
  "summary": {
    "total_jobs": 1234,
    "successful_jobs": 1180,
    "failed_jobs": 54,
    "total_cost_usd": 156.78,
    "total_tokens": 1250000,
    "avg_cost_per_job": 0.1270
  },
  "job_types": {
    "document_analysis": {
      "count": 456,
      "cost_usd": 67.89
    },
    "content_generation": {
      "count": 378,
      "cost_usd": 45.23
    },
    "data_extraction": {
      "count": 400,
      "cost_usd": 43.66
    }
  }
}
```

### Organization-Wide Usage

Track usage across all teams in an organization:

**API Endpoint:**

```bash
GET /api/organizations/{organization_id}/usage?period={period}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8003/api/organizations/org_xyz789/usage?period=2025-10"
```

**Response:**

```json
{
  "organization_id": "org_xyz789",
  "period": "2025-10",
  "summary": {
    "total_jobs": 5678,
    "completed_jobs": 5432,
    "failed_jobs": 246,
    "credits_used": 5432,
    "total_cost_usd": 678.90,
    "total_tokens": 5600000
  },
  "teams": {
    "team_abc123": {
      "jobs": 1234,
      "credits_used": 1180
    },
    "team_def456": {
      "jobs": 2345,
      "credits_used": 2301
    },
    "team_ghi789": {
      "jobs": 2099,
      "credits_used": 1951
    }
  }
}
```

### Database Queries for Analytics

The system uses several tables for tracking usage:

**1. Jobs Table** - Individual job tracking

```sql
-- Get job statistics for the current month
SELECT
    job_type,
    status,
    COUNT(*) as job_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration_seconds
FROM jobs
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY job_type, status
ORDER BY job_count DESC;
```

**2. LLM Calls Table** - Individual API call tracking

```sql
-- Get model usage statistics
SELECT
    model_group_used,
    resolved_model,
    COUNT(*) as call_count,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    AVG(latency_ms) as avg_latency_ms
FROM llm_calls
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY model_group_used, resolved_model
ORDER BY call_count DESC;
```

**3. Job Cost Summaries Table** - Aggregated job costs

```sql
-- Get cost summary for all jobs
SELECT
    j.team_id,
    j.organization_id,
    COUNT(DISTINCT j.job_id) as total_jobs,
    SUM(jcs.total_calls) as total_api_calls,
    SUM(jcs.total_tokens) as total_tokens,
    SUM(jcs.total_cost_usd) as total_cost_usd,
    AVG(jcs.avg_latency_ms) as avg_latency_ms
FROM jobs j
JOIN job_cost_summaries jcs ON j.job_id = jcs.job_id
WHERE j.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY j.team_id, j.organization_id
ORDER BY total_cost_usd DESC;
```

**4. Team Usage Summaries Table** - Pre-calculated analytics

```sql
-- Get monthly usage summaries for all teams
SELECT
    team_id,
    period,
    period_type,
    total_jobs,
    successful_jobs,
    failed_jobs,
    total_cost_usd,
    total_tokens,
    job_type_breakdown
FROM team_usage_summaries
WHERE period_type = 'monthly'
  AND period >= TO_CHAR(CURRENT_DATE - INTERVAL '6 months', 'YYYY-MM')
ORDER BY period DESC, total_cost_usd DESC;
```

### Usage Analytics Dashboard

```jsx
// pages/monitoring/usage.jsx
import { BarChart, LineChart } from '@/components/Charts';

export default function UsageAnalytics() {
  const [period, setPeriod] = useState('2025-10');
  const [data, setData] = useState(null);

  useEffect(() => {
    // Fetch usage data
    fetch(`/api/analytics/usage?period=${period}`)
      .then(res => res.json())
      .then(data => setData(data));
  }, [period]);

  return (
    <div className="usage-analytics">
      <h1>Usage Analytics - {period}</h1>

      <div className="stats-grid">
        <StatCard
          title="Total Jobs"
          value={data?.total_jobs}
          trend={data?.jobs_trend}
        />
        <StatCard
          title="Success Rate"
          value={`${data?.success_rate}%`}
          trend={data?.success_trend}
        />
        <StatCard
          title="Total Cost"
          value={`$${data?.total_cost}`}
          trend={data?.cost_trend}
        />
        <StatCard
          title="Avg Latency"
          value={`${data?.avg_latency}ms`}
          trend={data?.latency_trend}
        />
      </div>

      <BarChart
        title="Jobs by Type"
        data={data?.job_types}
        xAxis="job_type"
        yAxis="count"
      />

      <LineChart
        title="Daily Usage Trend"
        data={data?.daily_usage}
        xAxis="date"
        yAxis="jobs"
      />

      <TeamUsageTable teams={data?.teams} />
    </div>
  );
}
```

## Credit Consumption Tracking

### Credit Balance Monitoring

Check credit balance for any team:

**API Endpoint:**

```bash
GET /api/credits/teams/{team_id}/balance
Authorization: Bearer {virtual_key}
```

**Response:**

```json
{
  "team_id": "team_abc123",
  "organization_id": "org_xyz789",
  "credits_allocated": 1000,
  "credits_used": 245,
  "credits_remaining": 755,
  "credit_limit": 1000,
  "auto_refill": false,
  "refill_amount": null,
  "refill_period": null,
  "created_at": "2025-10-01T00:00:00Z",
  "updated_at": "2025-10-15T14:30:00Z"
}
```

### Credit Transaction History

Track all credit transactions:

**API Endpoint:**

```bash
GET /api/credits/teams/{team_id}/transactions?limit=50
Authorization: Bearer {virtual_key}
```

**Response:**

```json
{
  "team_id": "team_abc123",
  "total": 15,
  "transactions": [
    {
      "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
      "team_id": "team_abc123",
      "organization_id": "org_xyz789",
      "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "transaction_type": "deduction",
      "credits_amount": -1,
      "credits_before": 756,
      "credits_after": 755,
      "reason": "Job document_analysis completed successfully",
      "created_at": "2025-10-15T14:30:00Z"
    },
    {
      "transaction_id": "660e8400-e29b-41d4-a716-446655440001",
      "team_id": "team_abc123",
      "organization_id": "org_xyz789",
      "job_id": null,
      "transaction_type": "allocation",
      "credits_amount": 500,
      "credits_before": 256,
      "credits_after": 756,
      "reason": "Monthly credit allocation",
      "created_at": "2025-10-01T00:00:00Z"
    }
  ]
}
```

### Credit Consumption Analytics

Query credit usage patterns:

```sql
-- Daily credit consumption trend
SELECT
    DATE(created_at) as date,
    SUM(CASE WHEN transaction_type = 'deduction' THEN ABS(credits_amount) ELSE 0 END) as credits_used,
    SUM(CASE WHEN transaction_type = 'allocation' THEN credits_amount ELSE 0 END) as credits_added
FROM credit_transactions
WHERE team_id = 'team_abc123'
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

```sql
-- Top teams by credit consumption
SELECT
    tc.team_id,
    tc.organization_id,
    tc.credits_allocated,
    tc.credits_used,
    tc.credits_remaining,
    ROUND((tc.credits_used::float / NULLIF(tc.credits_allocated, 0) * 100), 2) as usage_percentage
FROM team_credits tc
WHERE tc.credits_allocated > 0
ORDER BY usage_percentage DESC
LIMIT 20;
```

### Low Credit Alerts

Monitor teams approaching credit exhaustion:

```python
# services/credit_alerts.py
from sqlalchemy import and_
from models.credits import TeamCredits
from models.organizations import Organization

def check_low_credit_teams(db: Session, threshold_percent: float = 20.0):
    """
    Find teams with credits below threshold percentage
    """
    teams = db.query(TeamCredits).filter(
        and_(
            TeamCredits.credits_allocated > 0,
            (TeamCredits.credits_remaining / TeamCredits.credits_allocated * 100) <= threshold_percent
        )
    ).all()

    alerts = []
    for team in teams:
        org = db.query(Organization).filter(
            Organization.organization_id == team.organization_id
        ).first()

        alerts.append({
            "team_id": team.team_id,
            "organization_id": team.organization_id,
            "organization_name": org.name if org else "Unknown",
            "credits_remaining": team.credits_remaining,
            "credits_allocated": team.credits_allocated,
            "usage_percent": round((team.credits_used / team.credits_allocated * 100), 2)
        })

    return alerts

# Usage
low_credit_teams = check_low_credit_teams(db, threshold_percent=10.0)
for team in low_credit_teams:
    send_alert(team)
```

## Performance Metrics

### Latency Tracking

Monitor API response times:

```sql
-- Average latency by model group
SELECT
    model_group_used,
    COUNT(*) as call_count,
    AVG(latency_ms) as avg_latency_ms,
    MIN(latency_ms) as min_latency_ms,
    MAX(latency_ms) as max_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as p50_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99_latency_ms
FROM llm_calls
WHERE created_at >= CURRENT_DATE - INTERVAL '24 hours'
  AND latency_ms IS NOT NULL
GROUP BY model_group_used
ORDER BY avg_latency_ms DESC;
```

### Error Rate Monitoring

Track failure rates:

```sql
-- Error rates by job type
SELECT
    job_type,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
    ROUND((SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 2) as error_rate
FROM jobs
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY job_type
ORDER BY error_rate DESC;
```

### Success Rate Dashboard

```jsx
// components/PerformanceMetrics.jsx
export function PerformanceMetrics({ data }) {
  return (
    <div className="performance-metrics">
      <MetricCard
        title="Success Rate"
        value={`${data.success_rate}%`}
        description="Jobs completed successfully"
        trend={data.success_trend}
      />

      <MetricCard
        title="Average Latency"
        value={`${data.avg_latency}ms`}
        description="API response time (P95)"
        trend={data.latency_trend}
      />

      <MetricCard
        title="Error Rate"
        value={`${data.error_rate}%`}
        description="Failed requests"
        trend={data.error_trend}
      />

      <MetricCard
        title="Throughput"
        value={`${data.requests_per_minute}/min`}
        description="Requests per minute"
        trend={data.throughput_trend}
      />
    </div>
  );
}
```

## Alerts & Notifications

### Alert Types

**1. System Alerts**
- Service downtime
- Database connection failures
- High error rates
- Performance degradation

**2. Usage Alerts**
- Unusual traffic spikes
- Team approaching credit limit
- Zero credit remaining
- High cost anomalies

**3. Security Alerts**
- Multiple failed authentication attempts
- Suspicious API usage patterns
- Rate limit violations
- Unauthorized access attempts

### Alert Configuration

```python
# config/alerts.py
ALERT_THRESHOLDS = {
    "credit_low": 10,  # Percentage
    "credit_critical": 0,  # Credits remaining
    "error_rate_high": 5.0,  # Percentage
    "latency_high": 5000,  # Milliseconds
    "cost_spike": 200.0,  # Percent increase
}

ALERT_CHANNELS = {
    "email": ["admin@company.com", "ops@company.com"],
    "slack": "https://hooks.slack.com/services/...",
    "webhook": "https://your-monitoring-system.com/alerts"
}
```

### Alert Implementation

```python
# services/alert_manager.py
import httpx
from typing import Dict, Any

class AlertManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def send_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """
        Send alert to configured channels
        """
        alert_data = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to email
        if "email" in self.config:
            await self._send_email(alert_data)

        # Send to Slack
        if "slack" in self.config:
            await self._send_slack(alert_data)

        # Send to webhook
        if "webhook" in self.config:
            await self._send_webhook(alert_data)

    async def _send_slack(self, alert_data: Dict[str, Any]):
        """Send alert to Slack"""
        webhook_url = self.config["slack"]

        payload = {
            "text": f"🚨 {alert_data['severity'].upper()}: {alert_data['message']}",
            "attachments": [
                {
                    "color": self._get_color(alert_data['severity']),
                    "fields": [
                        {"title": "Type", "value": alert_data['type'], "short": True},
                        {"title": "Time", "value": alert_data['timestamp'], "short": True}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload)

    def _get_color(self, severity: str) -> str:
        colors = {
            "info": "#36a64f",
            "warning": "#ff9800",
            "error": "#f44336",
            "critical": "#9c27b0"
        }
        return colors.get(severity, "#808080")

# Usage
alert_manager = AlertManager(ALERT_CHANNELS)

# Low credit alert
if team.credits_remaining <= ALERT_THRESHOLDS["credit_critical"]:
    await alert_manager.send_alert(
        alert_type="credit_critical",
        message=f"Team {team.team_id} has {team.credits_remaining} credits remaining",
        severity="critical"
    )
```

### Scheduled Alert Checks

```python
# scripts/check_alerts.py
import asyncio
from services.alert_manager import AlertManager, ALERT_THRESHOLDS

async def check_all_alerts():
    """
    Run all alert checks
    """
    alert_manager = AlertManager(ALERT_CHANNELS)

    # Check low credits
    low_credit_teams = check_low_credit_teams(db, ALERT_THRESHOLDS["credit_low"])
    for team in low_credit_teams:
        await alert_manager.send_alert(
            "credit_low",
            f"Team {team['team_id']} has {team['credits_remaining']} credits ({team['usage_percent']}% used)",
            "warning"
        )

    # Check high error rates
    error_stats = check_error_rates(db)
    for stat in error_stats:
        if stat['error_rate'] > ALERT_THRESHOLDS["error_rate_high"]:
            await alert_manager.send_alert(
                "error_rate_high",
                f"Job type {stat['job_type']} has {stat['error_rate']}% error rate",
                "error"
            )

    # Check high latency
    latency_stats = check_latency(db)
    for stat in latency_stats:
        if stat['p95_latency'] > ALERT_THRESHOLDS["latency_high"]:
            await alert_manager.send_alert(
                "latency_high",
                f"Model group {stat['model_group']} has {stat['p95_latency']}ms P95 latency",
                "warning"
            )

if __name__ == "__main__":
    asyncio.run(check_all_alerts())
```

**Schedule via cron:**

```bash
# crontab -e
*/15 * * * * python /path/to/check_alerts.py
```

## Monitoring Best Practices

### 1. Set Up Comprehensive Logging

```python
# config/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger('saas_llm')
    logger.setLevel(logging.INFO)

    # File handler with rotation
    handler = RotatingFileHandler(
        'logs/saas_llm.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

### 2. Track Key Business Metrics

```sql
-- Create a view for quick dashboard queries
CREATE VIEW monitoring_dashboard AS
SELECT
    COUNT(DISTINCT j.team_id) as active_teams,
    COUNT(j.job_id) as total_jobs_today,
    SUM(CASE WHEN j.status = 'completed' THEN 1 ELSE 0 END) as successful_jobs_today,
    SUM(CASE WHEN j.status = 'failed' THEN 1 ELSE 0 END) as failed_jobs_today,
    SUM(jcs.total_cost_usd) as total_cost_today,
    AVG(jcs.avg_latency_ms) as avg_latency_today
FROM jobs j
LEFT JOIN job_cost_summaries jcs ON j.job_id = jcs.job_id
WHERE j.created_at >= CURRENT_DATE;
```

### 3. Implement Real-Time Dashboards

Use WebSockets for live updates:

```javascript
// Real-time monitoring
const ws = new WebSocket('ws://localhost:8003/ws/monitoring');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Update dashboard in real-time
  updateMetrics(data);
};
```

### 4. Regular Performance Reviews

Schedule weekly/monthly performance reviews:

```sql
-- Weekly performance report
SELECT
    DATE_TRUNC('week', j.created_at) as week,
    COUNT(*) as total_jobs,
    AVG(jcs.total_cost_usd) as avg_cost_per_job,
    AVG(jcs.avg_latency_ms) as avg_latency,
    SUM(CASE WHEN j.status = 'failed' THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as error_rate
FROM jobs j
JOIN job_cost_summaries jcs ON j.job_id = jcs.job_id
WHERE j.created_at >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week DESC;
```

## Troubleshooting

### High Latency Issues

**Problem:** Average latency above 2000ms

**Investigation:**

```sql
-- Find slow API calls
SELECT
    call_id,
    job_id,
    model_group_used,
    resolved_model,
    latency_ms,
    total_tokens,
    created_at
FROM llm_calls
WHERE latency_ms > 5000
  AND created_at >= CURRENT_DATE - INTERVAL '24 hours'
ORDER BY latency_ms DESC
LIMIT 50;
```

**Solutions:**
1. Check LiteLLM proxy logs
2. Verify model provider status
3. Consider adding timeout configurations
4. Review model selection strategy

### Missing Usage Data

**Problem:** Usage summaries not updating

**Solution:** Manually recalculate summaries

```python
# scripts/recalculate_usage.py
from services.usage_calculator import calculate_team_usage

def recalculate_all_usage(period: str):
    teams = db.query(TeamCredits).all()

    for team in teams:
        summary = calculate_team_usage(
            db,
            team_id=team.team_id,
            period=period
        )

        # Store summary
        db.merge(summary)

    db.commit()

# Usage
recalculate_all_usage("2025-10")
```

## Next Steps

Now that you understand monitoring:

1. **[Set Up Alerts](monitoring.md#alerts--notifications)** - Configure notifications
2. **[Analyze Costs](credits.md#cost-analysis)** - Deep dive into costs
3. **[Optimize Performance](../reference/performance.md)** - Improve latency

## Additional Resources

- **[API Reference](../api-reference/monitoring.md)** - Monitoring endpoints
- **[Database Schema](../reference/database-schema.md)** - Tracking tables
- **[Performance Tuning](../reference/performance.md)** - Optimization guide
