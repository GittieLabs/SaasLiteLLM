# Pricing System Deployment Strategy

## Overview
This document outlines the safe deployment strategy for the JSON-based pricing system, replacing the hardcoded MODEL_PRICING dictionary.

## Pre-Deployment Validation

### 1. Local Testing (COMPLETED)
- [x] Created comprehensive validation script: `scripts/test_pricing_system.py`
- [x] All 11 tests passing
- [x] Validated:
  - Pricing file loads correctly (37 models)
  - All pricing data has valid format
  - Critical models present (gpt-4o, gpt-4o-mini, claude-sonnet-4-5)
  - Conversion accuracy (per-token to per-1M-tokens)
  - Cost calculation works end-to-end
  - Provider detection works correctly
  - Markup application works
  - Credit deduction calculation works for all modes

### 2. Run Validation Before Each Deployment
```bash
# ALWAYS run this before deploying
python3 scripts/test_pricing_system.py

# Output should show:
# ✓ ALL TESTS PASSED - Safe to deploy!
```

## Deployment Strategy

### Phase 1: Code Deployment (READY)

**Files Changed:**
- `src/utils/pricing_loader.py` (CREATED) - Loads pricing from JSON
- `src/utils/cost_calculator.py` (MODIFIED) - Uses JSON pricing instead of hardcoded dict
- `llm_pricing_current.json` (EXISTS) - Single source of truth for pricing

**What to Deploy:**
1. Push all code changes to production
2. Ensure `llm_pricing_current.json` is deployed with the code
3. Verify file permissions allow reading the JSON file

**Deployment Commands:**
```bash
# 1. Validate locally first
python3 scripts/test_pricing_system.py

# 2. Commit and push
git add src/utils/pricing_loader.py src/utils/cost_calculator.py llm_pricing_current.json
git commit -m "feat: Switch to JSON-based pricing system

- Load pricing from llm_pricing_current.json
- Remove hardcoded MODEL_PRICING dict
- Add comprehensive validation tests
- Enables dynamic pricing updates

Tested with 11-test validation suite - all passing"

# 3. Deploy to production
git push origin main
railway up  # or your deployment method
```

### Phase 2: Smoke Testing (POST-DEPLOYMENT)

**Immediately After Deployment:**

1. **Test LLM Call Works**
   ```bash
   # Make a simple LLM call via your API
   curl -X POST https://your-api.com/api/llm/create-and-call \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-4o-mini",
       "messages": [{"role": "user", "content": "Say hello"}],
       "max_tokens": 50
     }'
   ```

   **Expected:** Response with completion, no pricing errors

2. **Verify Pricing Data in Logs**
   ```bash
   # Check logs for pricing-related messages
   railway logs | grep -i "pricing\|cost"
   ```

   **Expected:** No errors about missing pricing or file not found

3. **Test Multiple Models**
   - Test with gpt-4o (OpenAI)
   - Test with claude-sonnet-4-5 (Anthropic)
   - Test with an unknown model (should fall back to default pricing)

4. **Verify Credit Deduction**
   - Make a call that uses credits
   - Check that credits were deducted correctly
   - Verify the cost calculation matches expected pricing

### Phase 3: Monitoring (First 24-48 Hours)

**What to Monitor:**

1. **Error Rates**
   - Watch for any increase in API errors
   - Specifically watch for pricing-related errors

2. **Cost Calculations**
   - Spot-check that costs match expected values
   - Compare with previous LiteLLM proxy costs (if available)

3. **Credit Deductions**
   - Verify credits are being deducted correctly
   - Check all three budget modes work:
     - job_based
     - consumption_usd
     - consumption_tokens

4. **Log Messages to Watch For**
   ```bash
   # Bad signs:
   grep -i "pricing file not found" logs
   grep -i "fallback pricing" logs  # Should be rare
   grep -i "json decode error" logs

   # Good signs:
   grep -i "pricing data loaded" logs
   ```

## Rollback Strategy

### If Issues Occur

**Symptoms that warrant rollback:**
- LLM calls failing with pricing-related errors
- Incorrect cost calculations
- Missing pricing for commonly-used models
- JSON file not found errors

**Rollback Steps:**

1. **Quick Fix (If JSON File Issue):**
   ```bash
   # Check if JSON file exists in production
   ls -la llm_pricing_current.json

   # If missing, redeploy or manually upload
   ```

2. **Code Rollback (If Logic Issue):**
   ```bash
   # Revert to previous commit
   git revert HEAD
   git push origin main
   railway up
   ```

3. **Emergency Hardcoded Pricing (Last Resort):**
   - Edit `src/utils/cost_calculator.py`
   - Comment out `MODEL_PRICING = load_pricing_from_json()`
   - Uncomment old hardcoded `MODEL_PRICING` dict
   - Deploy immediately

## Updating Pricing Data (Future)

### How to Update Pricing Without Code Changes

1. **Edit `llm_pricing_current.json`**
   - Add new models
   - Update existing prices
   - Keep the per-token format (will auto-convert)

2. **Validate Changes**
   ```bash
   python3 scripts/test_pricing_system.py
   ```

3. **Deploy**
   ```bash
   git add llm_pricing_current.json
   git commit -m "chore: Update pricing for [model names]"
   git push origin main
   ```

4. **Reload Without Restart (Optional)**
   - The pricing is cached at module load
   - To reload without restarting, you'd need to add an admin endpoint
   - For now, just redeploy to pick up changes

### Future Enhancement: Pricing Reload Endpoint

Consider adding:
```python
# In admin API routes
@router.post("/admin/pricing/reload")
async def reload_pricing():
    """Reload pricing data without restart"""
    from utils.pricing_loader import reload_pricing
    pricing = reload_pricing()
    return {"status": "reloaded", "models": len(pricing)}
```

## Critical Points of Failure Addressed

### 1. LLM Calls Not Working

**Prevention:**
- Fallback pricing ensures calls never fail due to missing pricing
- Validation tests confirm all critical models have pricing
- Default pricing of $1/$2 per 1M tokens is reasonable fallback

**Mitigation:**
- If pricing file missing, uses hardcoded fallback pricing
- If JSON invalid, uses fallback pricing
- Logs warnings but doesn't crash

### 2. Pricing Errors Preventing Returns

**Prevention:**
- All pricing lookups have fallback logic
- Extensive error handling in pricing_loader.py
- Never raises exceptions that would break LLM calls

**Mitigation:**
- Try/except blocks around all JSON operations
- Multiple fallback layers:
  1. Exact model match
  2. Case-insensitive match
  3. Partial match
  4. Default pricing

## Success Criteria

**Deployment is successful when:**
- [x] All 11 validation tests pass
- [ ] First production LLM call completes successfully
- [ ] Costs calculated correctly (spot-check 3-5 calls)
- [ ] No pricing-related errors in logs for 1 hour
- [ ] Credits deducted correctly for all budget modes
- [ ] Multiple providers work (OpenAI, Anthropic, Gemini)

## Testing Checklist

Before marking deployment complete:

- [ ] Run `python3 scripts/test_pricing_system.py` - all pass
- [ ] Deploy to production
- [ ] Make test call with gpt-4o-mini
- [ ] Make test call with claude-sonnet-4-5
- [ ] Make test call with unknown model (verify fallback)
- [ ] Check logs for errors
- [ ] Verify credit deduction for job_based mode
- [ ] Verify credit deduction for consumption_usd mode
- [ ] Verify credit deduction for consumption_tokens mode
- [ ] Monitor for 2 hours
- [ ] No errors - mark deployment successful

## Contact

If issues arise during deployment:
1. Check this document's rollback section
2. Run validation script to identify issues
3. Check production logs for specific errors
4. Rollback if necessary

## Notes

- The pricing system is designed to never fail - it always has fallback pricing
- All tests pass locally, indicating system is production-ready
- JSON pricing file contains 37 models covering major providers
- Cost calculations have been validated with known pricing data
