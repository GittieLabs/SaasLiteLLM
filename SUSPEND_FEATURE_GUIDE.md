# Team Suspend/Pause Feature Guide

## Overview

This feature allows admins to suspend or pause teams, preventing them from making API calls. This is useful for:
- **Payment issues**: Suspend teams with unpaid invoices
- **Policy violations**: Temporarily suspend teams violating terms of service
- **Security concerns**: Immediately block suspicious activity
- **Account management**: Pause inactive teams

## How It Works

### 1. Architecture Flow

```
Client API Call → SaaS API → Authentication Check → Status Validation → LiteLLM Proxy
                                    ↓
                        If status != 'active', return 403 Forbidden
```

### 2. Team Status Values

- **`active`** (default): Team can make API calls normally
- **`suspended`**: Team is blocked from making API calls (admin action required)
- **`paused`**: Team is temporarily paused (can be used for scheduled maintenance)

### 3. Client Experience

When a suspended/paused team tries to make an API call:

```bash
POST /api/jobs/create
Authorization: Bearer sk-xxx...

Response: 403 Forbidden
{
  "detail": "Team access is suspended. Please contact support."
}
```

## How to Use (Admin Panel)

### Suspend a Team

1. Go to **Teams** page
2. Find the team you want to suspend
3. Click the **Pause** icon (⏸) in the Actions column
4. Confirm the suspension
5. Team status changes to **Suspended** (red badge)
6. Team can no longer make API calls

### Resume a Team

1. Go to **Teams** page
2. Find the suspended/paused team
3. Click the **Play** icon (▶) in the Actions column
4. Confirm the resumption
5. Team status changes to **Active** (green badge)
6. Team can make API calls again

## API Endpoints

### Suspend Team
```bash
PUT /api/teams/{team_id}/suspend

Response:
{
  "team_id": "team-alpha",
  "status": "suspended",
  "message": "Team 'team-alpha' has been suspended"
}
```

### Resume Team
```bash
PUT /api/teams/{team_id}/resume

Response:
{
  "team_id": "team-alpha",
  "status": "active",
  "message": "Team 'team-alpha' has been resumed"
}
```

### List Teams (includes status)
```bash
GET /api/teams

Response:
[
  {
    "team_id": "team-alpha",
    "organization_id": "org-1",
    "status": "active",
    "credits_allocated": 1000,
    "credits_remaining": 800,
    ...
  }
]
```

## Implementation Details

### Database Schema

**Migration:** `scripts/migrations/010_add_team_status.sql`

```sql
ALTER TABLE team_credits
ADD COLUMN status VARCHAR(20) DEFAULT 'active' NOT NULL;

CREATE INDEX idx_team_credits_status ON team_credits(status);
```

### Authentication Validation

**File:** `src/auth/dependencies.py`

```python
async def verify_virtual_key(...):
    team_creds = db.query(TeamCredits).filter(
        TeamCredits.virtual_key == virtual_key
    ).first()

    # Check team status
    if team_creds.status != "active":
        raise HTTPException(
            status_code=403,
            detail=f"Team access is {team_creds.status}. Please contact support."
        )

    return team_creds.team_id
```

This validation runs **before every API call**, ensuring suspended teams are immediately blocked.

### Status Badge Colors

- **Green**: Active (can make calls)
- **Red**: Suspended (blocked by admin)
- **Yellow**: Paused (temporarily disabled)

## Use Cases

### 1. Payment Issues
```
Scenario: Customer's payment failed
Action: Suspend team until payment is received
Result: Team cannot make API calls, sees "Team access is suspended" message
Resolution: Resume team once payment is successful
```

### 2. Security Alert
```
Scenario: Suspicious activity detected on team
Action: Immediately suspend team to prevent further issues
Result: All API calls blocked instantly
Resolution: Investigate, then resume or permanently delete
```

### 3. Policy Violation
```
Scenario: Team violates terms of service
Action: Suspend team and send notification
Result: Team access blocked, admin can review
Resolution: Resume after policy acknowledgment or delete if severe
```

### 4. Scheduled Maintenance
```
Scenario: Need to perform maintenance on team's resources
Action: Temporarily pause team
Result: Team API calls blocked during maintenance
Resolution: Resume team after maintenance complete
```

## Important Notes

1. **Immediate Effect**: Status changes take effect immediately - suspended teams are blocked on their very next API call

2. **Job Completion**: If a team is suspended mid-job:
   - In-progress jobs can complete
   - New jobs cannot be created
   - New LLM calls within existing jobs are blocked

3. **Default Teams**: Default teams (ending with `_default`) can be suspended but not deleted

4. **Credit Tracking**: Suspending a team does NOT affect their credit balance - credits remain as-is

5. **LiteLLM Integration**: Teams remain in LiteLLM - suspension is handled at the SaaS API layer

## Testing

### Test Suspension Flow

1. **Create a test team**:
   ```bash
   POST /api/teams/create
   {
     "team_id": "test-suspend",
     "organization_id": "test-org",
     "access_groups": ["TestAccessGrp1"],
     "credits_allocated": 100
   }
   ```

2. **Make successful API call** (should work):
   ```bash
   POST /api/jobs/create
   Authorization: Bearer {virtual_key}
   {
     "team_id": "test-suspend",
     "job_type": "test_job"
   }
   ```

3. **Suspend the team**:
   ```bash
   PUT /api/teams/test-suspend/suspend
   ```

4. **Try API call again** (should fail with 403):
   ```bash
   POST /api/jobs/create
   Authorization: Bearer {virtual_key}

   Response: 403 Forbidden
   "Team access is suspended. Please contact support."
   ```

5. **Resume the team**:
   ```bash
   PUT /api/teams/test-suspend/resume
   ```

6. **API call works again** (should succeed).

## Files Modified

### Backend
- `scripts/migrations/010_add_team_status.sql` - Database migration
- `src/models/credits.py` - Added `status` field to TeamCredits model
- `src/auth/dependencies.py` - Added status validation to authentication
- `src/api/teams.py` - Added suspend/resume endpoints, updated list endpoint

### Frontend
- `admin-panel/types/index.ts` - Added status to Team interface
- `admin-panel/lib/api-client.ts` - Added suspendTeam/resumeTeam methods
- `admin-panel/app/teams/page.tsx` - Added status column, suspend/resume buttons

## Migration Applied

```bash
docker exec -i litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm' < scripts/migrations/010_add_team_status.sql
```

Migration successfully added `status` column to all existing teams with default value `'active'`.

---

## Summary

The suspend/pause feature provides admins with fine-grained control over team access:

- ✅ **Instant blocking**: Suspended teams are blocked immediately
- ✅ **Reversible**: Teams can be easily resumed
- ✅ **User-friendly**: Clear status badges and toggle buttons
- ✅ **Secure**: Validation happens at authentication layer
- ✅ **Flexible**: Supports multiple suspension reasons (payment, security, policy)

This is a critical feature for SaaS operations, allowing quick response to payment issues, security threats, or policy violations.
