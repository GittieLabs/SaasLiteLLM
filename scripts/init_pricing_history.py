#!/usr/bin/env python3
"""
Initialize pricing history with current pricing data.

This script validates all current pricing in MODEL_PRICING by recording
it in the pricing history system. Run this once to establish a baseline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.pricing_updater import get_pricing_updater
from utils.cost_calculator import MODEL_PRICING

def main():
    updater = get_pricing_updater()

    print("Initializing pricing history with current pricing data...")
    print(f"Found {len(MODEL_PRICING) - 1} models to validate")  # -1 for 'default'
    print()

    updates = []
    for model_name, pricing in MODEL_PRICING.items():
        if model_name == "default":
            continue

        updates.append({
            "model_name": model_name,
            "input_price": pricing["input"],
            "output_price": pricing["output"],
            "source": "initial_validation",
            "notes": "Initial pricing validation from October 2025 research"
        })

    # Bulk update
    results = updater.bulk_update_pricing(updates)

    # Print summary
    print(f"✓ Validated: {len(results['updated'])} models")
    print(f"○ Already up-to-date: {len(results['unchanged'])} models")

    if results['failed']:
        print(f"✗ Failed: {len(results['failed'])} models")
        for item in results['failed']:
            print(f"  - {item['model']}: {item['error']}")
        return 1

    print("\n✓ Pricing history initialized successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
