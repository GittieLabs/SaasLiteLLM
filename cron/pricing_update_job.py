#!/usr/bin/env python3
"""
Pricing Update Cron Job

Runs as a Railway cron job to periodically check and update LLM pricing.
This script is designed to run weekly to keep pricing data current.

The job:
1. Validates current pricing for suspicious values
2. Checks for models that haven't been updated in 30+ days
3. Generates a report and sends notifications if needed
4. Attempts to scrape pricing from provider websites (placeholder for now)

Usage:
    python cron/pricing_update_job.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.pricing_scraper import get_pricing_scraper
from services.pricing_updater import get_pricing_updater
from utils.cost_calculator import MODEL_PRICING

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main cron job execution"""
    logger.info("=" * 80)
    logger.info("Starting pricing update cron job")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 80)

    try:
        scraper = get_pricing_scraper()
        updater = get_pricing_updater()

        # Step 1: Validate current pricing
        logger.info("\nStep 1: Validating current pricing...")
        validation = await scraper.validate_current_pricing()

        logger.info(f"Validated {validation['models_validated']} models")

        if validation['warnings']:
            logger.warning(f"Found {len(validation['warnings'])} pricing warnings:")
            for warning in validation['warnings'][:10]:  # Show first 10
                logger.warning(f"  - {warning['model']}: {warning['issue']}")

        if validation['errors']:
            logger.error(f"Found {len(validation['errors'])} pricing errors:")
            for error in validation['errors']:
                logger.error(f"  - {error}")

        # Step 2: Check for stale pricing
        logger.info("\nStep 2: Checking for stale pricing...")
        stale_models = updater.get_models_needing_update(days_threshold=30)

        if stale_models:
            logger.warning(f"Found {len(stale_models)} models needing update:")

            # Group by provider
            by_provider = {}
            for model in stale_models:
                provider = model['provider']
                if provider not in by_provider:
                    by_provider[provider] = []
                by_provider[provider].append(model)

            for provider, models in sorted(by_provider.items()):
                logger.warning(f"  {provider}: {len(models)} models")
        else:
            logger.info("All models have been updated recently")

        # Step 3: Attempt to scrape pricing (currently placeholder)
        logger.info("\nStep 3: Scraping provider pricing pages...")
        scrape_results = await scraper.scrape_all_providers()

        logger.info(f"Scrape summary:")
        logger.info(f"  Successful: {scrape_results['summary']['successful']}")
        logger.info(f"  Failed: {scrape_results['summary']['failed']}")
        logger.info(f"  Models found: {scrape_results['summary']['total_scraped']}")

        # Step 4: Generate weekly report
        logger.info("\nStep 4: Generating pricing change report...")
        report = updater.generate_pricing_change_report(start_date=None)  # All time

        logger.info(f"Pricing change report:")
        logger.info(f"  Total changes: {report['summary']['total_changes']}")
        logger.info(f"  Price increases: {report['summary']['increases']}")
        logger.info(f"  Price decreases: {report['summary']['decreases']}")
        logger.info(f"  New models: {report['summary']['new_models']}")

        # Step 5: Save results
        logger.info("\nStep 5: Saving cron job results...")

        results_dir = Path(__file__).parent.parent / "data" / "cron_results"
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"pricing_update_{timestamp}.json"

        job_results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "validation": validation,
            "stale_models_count": len(stale_models),
            "scrape_results": scrape_results,
            "report_summary": report['summary']
        }

        with open(results_file, 'w') as f:
            json.dump(job_results, f, indent=2)

        logger.info(f"Results saved to {results_file}")

        # Log final summary
        logger.info("\n" + "=" * 80)
        logger.info("Pricing update cron job completed successfully")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Cron job failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
