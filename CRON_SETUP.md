# Pricing Update Cron Service Setup

This document explains how to set up the pricing update cron service on Railway.

## Overview

The pricing update cron service runs periodically to:
1. Validate current LLM pricing for suspicious values
2. Check for models that haven't been updated in 30+ days
3. Scrape pricing from provider websites (when available)
4. Generate pricing change reports
5. Save results to timestamped JSON files

## Architecture

- **Service**: Standalone cron job (not exposed externally)
- **Dockerfile**: `Dockerfile.cron`
- **Script**: `cron/pricing_update_job.py`
- **Schedule**: Recommended weekly (every Monday at 9 AM UTC)
- **Network**: Uses Railway internal network to access shared resources

## Railway Setup

### Option 1: Railway Cron Service (Recommended)

Railway supports native cron jobs. To set up:

1. **Create a new service in Railway**:
   ```bash
   railway service create pricing-cron
   ```

2. **Configure the service**:
   - Go to your Railway project dashboard
   - Add a new service from the repo
   - Select "Cron Job" as the service type
   - Set the Dockerfile path to `Dockerfile.cron`

3. **Set the cron schedule**:
   In the Railway dashboard, set the cron expression:
   ```
   0 9 * * 1
   ```
   This runs every Monday at 9:00 AM UTC (weekly pricing check).

4. **Environment Variables**:
   The cron service doesn't need external API keys since it only validates
   and checks for stale pricing. If you implement actual web scraping, you may
   need to add provider API keys.

   No environment variables are currently required.

5. **Volume/Storage** (Optional):
   If you want to persist cron results across runs:
   - Mount a volume at `/app/data`
   - This will preserve all cron job results in `data/cron_results/`

### Option 2: Railway Scheduled Service

If native cron isn't available, use Railway's scheduled deployments:

1. **Create service**:
   ```bash
   railway service create pricing-cron
   ```

2. **Configure as scheduled**:
   - Set Dockerfile to `Dockerfile.cron`
   - Enable "Restart Policy: Never" (run once and exit)
   - Use Railway's scheduling feature to run weekly

3. **Manual scheduling**:
   You can also trigger manually via Railway CLI:
   ```bash
   railway run --service pricing-cron
   ```

### Option 3: External Cron Service

Use an external cron service (e.g., GitHub Actions, cron-job.org) to trigger:

1. **Create an API endpoint** (optional):
   Add an admin-only endpoint to trigger the cron job:
   ```python
   @app.post("/admin/pricing-update")
   async def trigger_pricing_update(current_user: User = Depends(require_admin)):
       # Run pricing update in background
       pass
   ```

2. **Configure external cron**:
   Call the endpoint weekly from your preferred cron service.

## Testing Locally

Before deploying, test the cron service locally:

```bash
# Install dependencies
pip install -e .

# Run the cron job
python3 cron/pricing_update_job.py
```

Expected output:
```
================================================================================
Starting pricing update cron job
Timestamp: 2025-10-23T12:00:00.000000Z
================================================================================

Step 1: Validating current pricing...
Validated 66 models

Step 2: Checking for stale pricing...
Found 0 models needing update

Step 3: Scraping provider pricing pages...
Scraping pricing for openai...
Scraping pricing for anthropic...
...

Step 4: Generating pricing change report...
...

Step 5: Saving cron job results...
Results saved to data/cron_results/pricing_update_20251023_120000.json

================================================================================
Pricing update cron job completed successfully
================================================================================
```

## Viewing Results

Cron job results are saved to `data/cron_results/` with timestamps:

```bash
# View latest results
cat data/cron_results/pricing_update_*.json | tail -n 1 | jq .

# View all results
ls -lt data/cron_results/
```

Each result file contains:
- Timestamp
- Validation summary (warnings, errors)
- Count of stale models
- Scraping results (success/failure by provider)
- Pricing change report summary

## Monitoring

### Railway Logs

View cron job logs in Railway:
```bash
railway logs --service pricing-cron
```

### Success Criteria

A successful cron run should:
- Complete all 5 steps without errors
- Return exit code 0
- Log "Pricing update cron job completed successfully"

### Failure Handling

If the cron job fails:
1. Check Railway logs for error messages
2. Review the last saved results file
3. Run locally to reproduce the issue
4. Check that dependencies (beautifulsoup4, lxml) are installed

## Cron Schedule Recommendations

Pricing changes are infrequent, so we recommend:

- **Weekly**: `0 9 * * 1` (Every Monday at 9 AM UTC) - Recommended
- **Bi-weekly**: `0 9 1,15 * *` (1st and 15th of month at 9 AM UTC)
- **Monthly**: `0 9 1 * *` (1st of month at 9 AM UTC)

## Manual Pricing Updates

For immediate pricing updates, use the CLI tool:

```bash
# Update a single model
python scripts/manage_pricing.py update gpt-4o --input 5.00 --output 20.00

# Check for stale pricing
python scripts/manage_pricing.py check-stale

# Generate pricing report
python scripts/manage_pricing.py report --days 30
```

## Future Enhancements

Currently, the web scraping logic is placeholder. To implement full scraping:

1. **Implement provider-specific parsers**:
   - Update `_parse_openai_pricing()` in `src/services/pricing_scraper.py`
   - Update `_parse_anthropic_pricing()`
   - Update `_parse_gemini_pricing()`
   - Update `_parse_fireworks_pricing()`

2. **Add retry logic**:
   - Implement exponential backoff for failed scrapes
   - Add timeout handling

3. **Add notifications**:
   - Send alerts when significant price changes are detected
   - Notify when scraping fails for extended periods

4. **Add data validation**:
   - Compare scraped prices against known ranges
   - Flag suspicious pricing automatically

## Troubleshooting

### Import Errors

If you get import errors:
```bash
pip install -e .
```

### Permission Denied

If you get permission errors on the cron script:
```bash
chmod +x cron/pricing_update_job.py
```

### Missing Dependencies

If BeautifulSoup is not found:
```bash
pip install beautifulsoup4 lxml
```

### Railway Build Failures

If the Docker build fails:
- Check that `Dockerfile.cron` exists
- Verify that `cron/` and `src/` directories are included in build context
- Check Railway build logs for specific errors

## Support

For issues or questions:
1. Check Railway logs: `railway logs --service pricing-cron`
2. Test locally: `python3 cron/pricing_update_job.py`
3. Review cron results: `ls -lt data/cron_results/`
4. Check pricing history: `python scripts/manage_pricing.py history`
