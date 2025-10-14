# Credits

Learn how the credit system works and how to allocate credits to teams.

## How Credits Work

SaaS LiteLLM uses a **credit-based billing system** built on top of LiteLLM to simplify cost tracking:

- **1 credit = 1 completed job** (regardless of how many LLM calls the job makes)
- Credits are allocated per team
- Credits are only deducted when a job completes successfully
- Failed jobs don't consume credits

!!! info "Built on LiteLLM"
    While [LiteLLM](https://docs.litellm.ai) tracks token-based costs from providers, SaaS LiteLLM abstracts this into simple credit-based billing. This allows you to set predictable pricing for your clients while tracking actual provider costs internally.

### Why Credits Instead of Tokens?

**Traditional Token Billing:**
```
- Document analysis: 2,345 tokens = $0.0234
- Chat session: 5,123 tokens = $0.0512
- Data extraction: 1,234 tokens = $0.0123
```
❌ Complex for clients to predict costs
❌ Varies based on input/output length
❌ Hard to budget

**Credit Billing:**
```
- Document analysis: 1 credit
- Chat session: 1 credit
- Data extraction: 1 credit
```
✅ Predictable costs
✅ Easy to understand
✅ Simple budgeting

## Credit Allocation

### Initial Allocation

When creating a team, specify initial credits:

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_client",
    "team_id": "client-prod",
    "team_alias": "Production",
    "access_groups": ["gpt-models"],
    "credits_allocated": 1000
  }'
```

**Response:**
```json
{
  "team_id": "client-prod",
  "credits_allocated": 1000,
  "credits_remaining": 1000
}
```

### Adding Credits

Add credits to an existing team:

**Via Dashboard:**
1. Navigate to Teams → Select team
2. Click "Add Credits"
3. Enter amount
4. Click "Add"

**Via API:**
```bash
curl -X POST http://localhost:8003/api/credits/add \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "client-prod",
    "amount": 500,
    "description": "Monthly credit top-up - November 2024"
  }'
```

**Response:**
```json
{
  "team_id": "client-prod",
  "credits_added": 500,
  "credits_remaining": 1250,
  "transaction_id": "txn_abc123"
}
```

## Checking Credit Balance

### Via Dashboard

Navigate to Teams → Select team → See credits displayed

### Via API

```bash
curl "http://localhost:8003/api/credits/balance?team_id=client-prod"
```

**Response:**
```json
{
  "team_id": "client-prod",
  "credits_allocated": 1500,
  "credits_remaining": 750,
  "credits_used": 750,
  "percentage_used": 50.0,
  "status": "active"
}
```

## Credit Deduction Logic

### When Credits Are Deducted

Credits are deducted **only when a job completes successfully:**

```python
# Create job - No credits deducted yet
job = create_job("document_analysis")

# Make LLM calls - No credits deducted yet
llm_call(job_id, messages)
llm_call(job_id, messages)
llm_call(job_id, messages)

# Complete job - NOW 1 credit is deducted
complete_job(job_id, "completed")
```

### Failed Jobs Don't Cost Credits

```python
# Create job
job = create_job("analysis")

try:
    # Make LLM call that fails
    llm_call(job_id, messages)
except Exception as e:
    # Complete as failed
    complete_job(job_id, "failed")
    # No credits deducted! ✅
```

### Multiple Calls = One Credit

The beauty of job-based billing:

```python
# One job with 5 LLM calls = 1 credit
job = create_job("complex_analysis")

extract_text(job_id)      # Call 1
classify(job_id)          # Call 2
summarize(job_id)         # Call 3
generate_insights(job_id) # Call 4
quality_check(job_id)     # Call 5

complete_job(job_id, "completed")
# Total cost: 1 credit (not 5!)
```

## Credit Transactions

### View Transaction History

Track all credit additions and deductions:

```bash
curl "http://localhost:8003/api/credits/transactions?team_id=client-prod&limit=10"
```

**Response:**
```json
{
  "team_id": "client-prod",
  "transactions": [
    {
      "transaction_id": "txn_abc123",
      "type": "addition",
      "amount": 500,
      "description": "Monthly credit top-up",
      "timestamp": "2024-10-14T10:00:00Z",
      "balance_after": 1250
    },
    {
      "transaction_id": "txn_abc122",
      "type": "deduction",
      "amount": 1,
      "description": "Job: job_xyz123 completed",
      "job_id": "job_xyz123",
      "timestamp": "2024-10-14T09:30:00Z",
      "balance_after": 750
    }
  ]
}
```

## Low Credit Alerts

### Setting Up Alerts

Monitor teams approaching zero credits:

```python
# Check if team needs alert
def check_credit_alerts(team_id):
    balance = get_credit_balance(team_id)

    allocated = balance['credits_allocated']
    remaining = balance['credits_remaining']
    percentage = (remaining / allocated) * 100

    # Alert at 20% remaining
    if percentage <= 20 and percentage > 10:
        send_alert("low_credits", team_id, remaining)

    # Critical alert at 10%
    elif percentage <= 10:
        send_alert("critical_credits", team_id, remaining)
```

### Automated Top-ups

Set up automatic credit additions:

```python
# Auto top-up when credits hit threshold
def auto_topup_check(team_id):
    balance = get_credit_balance(team_id)

    if balance['credits_remaining'] < 100:
        # Add predefined amount
        add_credits(team_id, 1000, "Automatic monthly top-up")
        notify_client(team_id, "Credits topped up to 1000")
```

## Pricing Strategies

### Strategy 1: Credit Packages

Sell credits in packages:

```
Starter: 1,000 credits = $99/month
Professional: 5,000 credits = $399/month
Enterprise: 20,000 credits = $1,299/month
```

**Implementation:**
```bash
# Starter plan
curl -X POST http://localhost:8003/api/credits/add \
  -d '{"team_id": "client-prod", "amount": 1000}'

# Professional plan
curl -X POST http://localhost:8003/api/credits/add \
  -d '{"team_id": "client-prod", "amount": 5000}'
```

### Strategy 2: Pay-As-You-Go

Charge per credit used:

```
$0.10 per credit
Minimum purchase: 100 credits ($10)
```

**Track Actual Costs:**
```bash
# Get usage for billing
curl "http://localhost:8003/api/teams/client-prod/usage?period=2024-10"

# Response includes:
# - credits_used: 534
# - Your charge: 534 × $0.10 = $53.40
# - Actual LiteLLM cost: $45.67 (internal tracking)
# - Your profit: $7.73
```

### Strategy 3: Subscription + Overage

Base subscription with overage charges:

```
Plan: $99/month includes 1,000 credits
Overage: $0.08 per additional credit
```

### Strategy 4: Tiered Pricing

Volume discounts:

```
First 1,000 credits: $0.10 each
Next 4,000 credits: $0.08 each
Over 5,000 credits: $0.06 each
```

## Budget Modes

### Mode 1: Hard Limit (Default)

Team cannot exceed allocated credits:

```json
{
  "team_id": "client-prod",
  "budget_mode": "hard_limit",
  "credits_allocated": 1000
}
```

**Behavior:**
- Job creation succeeds
- LLM calls succeed
- Job completion **fails if credits exhausted**
- API returns 403 "Insufficient credits"

### Mode 2: Soft Limit with Alerts

Allow overage with notifications:

```json
{
  "team_id": "client-prod",
  "budget_mode": "soft_limit",
  "credits_allocated": 1000,
  "alert_at_percentage": 80
}
```

**Behavior:**
- Can exceed allocated credits
- Alerts sent at 80%, 100%, 120%
- Track overage separately for billing

### Mode 3: Unlimited (Enterprise)

No credit limits:

```json
{
  "team_id": "enterprise-prod",
  "budget_mode": "unlimited"
}
```

**Behavior:**
- No credit checks
- Track usage for billing
- Typically for enterprise contracts

## Client Communication

### Credit Allocation Email

```
Subject: Your Credits Have Been Allocated

Hi [Client],

We've allocated 1,000 credits to your account!

WHAT ARE CREDITS?
- 1 credit = 1 completed job
- Jobs can contain multiple LLM calls
- Only successful jobs consume credits

YOUR BALANCE:
- Allocated: 1,000 credits
- Remaining: 1,000 credits

ESTIMATED USAGE:
- Document analysis: ~1 credit per document
- Chat sessions: ~1 credit per conversation
- Your 1,000 credits = approximately 1,000 operations

MONITOR USAGE:
View real-time usage at: https://dashboard.yourcompany.com

Need more credits? Reply to this email or visit your dashboard.

Questions? support@yourcompany.com
```

### Low Credit Warning

```
Subject: Low Credit Alert - 20% Remaining

Hi [Client],

Your credit balance is running low:

CURRENT BALANCE: 200 credits (20% remaining)
ESTIMATED DEPLETION: 2-3 days at current usage

ACTION REQUIRED:
1. Purchase additional credits: https://dashboard.yourcompany.com/credits
2. Or contact us: support@yourcompany.com

Don't let your integration stop! Top up now.

Best regards,
Your Company Team
```

### Out of Credits Notice

```
Subject: URGENT: Credits Exhausted

Hi [Client],

Your account has run out of credits.

CURRENT BALANCE: 0 credits
STATUS: API calls suspended

TO RESTORE SERVICE:
1. Purchase credits immediately: https://dashboard.yourcompany.com/credits
2. Or contact support: support@yourcompany.com

Service will resume automatically once credits are added.

Questions? We're here to help!
```

## Monitoring & Analytics

### Team Credit Utilization

```bash
# Get utilization across all teams
curl "http://localhost:8003/api/credits/utilization"
```

**Response:**
```json
{
  "total_teams": 25,
  "summary": {
    "total_allocated": 50000,
    "total_remaining": 32000,
    "total_used": 18000,
    "avg_utilization": 36.0
  },
  "by_status": {
    "healthy": 20,      // >50% remaining
    "warning": 3,       // 20-50% remaining
    "critical": 2       // <20% remaining
  },
  "teams_needing_attention": [
    {
      "team_id": "client-a-prod",
      "credits_remaining": 50,
      "percentage": 5.0,
      "status": "critical"
    }
  ]
}
```

### Usage Trends

Track credit consumption over time:

```bash
curl "http://localhost:8003/api/credits/trends?team_id=client-prod&days=30"
```

**Use For:**
- Predicting when team will run out
- Recommending plan upgrades
- Identifying usage spikes
- Forecasting revenue

## Best Practices

### For Admins

1. **Start Conservative**
   - Begin with modest allocation (1,000 credits)
   - Monitor usage first week
   - Adjust based on actual patterns

2. **Set Up Alerts**
   - Alert at 50%, 20%, 10%, 0%
   - Proactive outreach before depletion
   - Automated top-up for trusted clients

3. **Review Monthly**
   - Check all team credit levels
   - Identify heavy users (upsell opportunity)
   - Identify low users (check satisfaction)

4. **Track Profit Margins**
   - Monitor actual LiteLLM costs vs. credits charged
   - Adjust pricing if margins too thin
   - Offer volume discounts for retention

### For Clients

Share these tips with clients:

1. **Monitor Your Balance**
   - Check dashboard regularly
   - Set up low-balance alerts
   - Don't let credits hit zero

2. **Estimate Usage**
   - 1 credit ≈ 1 business operation
   - Track your typical job types
   - Budget accordingly

3. **Complete Jobs Properly**
   - Always call `complete_job()`
   - Failed jobs don't cost credits
   - Incomplete jobs won't be billed

4. **Optimize Usage**
   - Group related calls into single jobs
   - Don't create unnecessary jobs
   - Cache responses when possible

## Common Scenarios

### Scenario 1: Client Runs Out Mid-Month

**Problem:** Client exhausted their 1,000 credits in 2 weeks

**Actions:**
1. Add immediate emergency credits (100-200)
2. Analyze usage patterns
3. Recommend plan upgrade
4. Set up automatic top-ups going forward

### Scenario 2: Client Barely Uses Credits

**Problem:** Client using <10% of allocation

**Actions:**
1. Check if they're having integration issues
2. Offer to help with implementation
3. Consider downgrading to save them money (builds trust)
4. Check if they need different features

### Scenario 3: Unexpected Usage Spike

**Problem:** Team uses 3x normal credits in one day

**Actions:**
1. Check for runaway processes
2. Contact client to verify legitimate usage
3. Temporarily increase limits if needed
4. Investigate potential security issues

## Troubleshooting

### Credits Not Deducted

**Problem:** Jobs completing but credits unchanged

**Solutions:**
1. Check job actually reached "completed" status
2. Verify credit deduction logic in code
3. Check database transaction logs
4. Ensure job_id is valid

### Can't Add Credits

**Problem:** API returns error when adding credits

**Solutions:**
1. Verify team exists and is active
2. Check team not suspended
3. Validate credit amount is positive integer
4. Check for database connection issues

### Balance Shows Negative

**Problem:** Credits_remaining is negative

**Solutions:**
1. This can happen with race conditions
2. Investigate concurrent job completions
3. Add credits to bring back to positive
4. Implement better locking in credit deduction

## Next Steps

Now that you understand credits:

1. **[Create Teams](teams.md)** - Allocate credits when creating teams
2. **[Monitor Usage](monitoring.md)** - Track credit consumption
3. **[Set Up Model Access](model-access-groups.md)** - Control which models teams can use
4. **[Review Best Practices](best-practices.md)** - Optimize credit management
