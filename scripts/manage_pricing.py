#!/usr/bin/env python3
"""
Pricing Management CLI

Command-line tool for managing LLM model pricing data.

Usage:
    # Update a single model's pricing
    python scripts/manage_pricing.py update gpt-4o --input 5.00 --output 20.00

    # Update multiple models from JSON file
    python scripts/manage_pricing.py bulk-update pricing_updates.json

    # View pricing history
    python scripts/manage_pricing.py history --model gpt-4o

    # Check for stale pricing (not updated in 30+ days)
    python scripts/manage_pricing.py check-stale

    # Generate pricing change report
    python scripts/manage_pricing.py report --days 30

    # Export current pricing
    python scripts/manage_pricing.py export --output pricing_export.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.pricing_updater import get_pricing_updater
from utils.cost_calculator import MODEL_PRICING, list_models_by_provider


def update_model_pricing(args):
    """Update pricing for a single model"""
    updater = get_pricing_updater()

    try:
        result = updater.update_model_pricing(
            model_name=args.model,
            input_price=args.input,
            output_price=args.output,
            source=args.source or "cli",
            notes=args.notes
        )

        print(f"✓ {result['status'].upper()}: {args.model}")

        if result['status'] == 'unchanged':
            print(f"  {result.get('message', 'Pricing is already up to date')}")
        else:
            print(f"  New pricing: ${result['new_pricing']['input']}/${result['new_pricing']['output']} per 1M tokens")

            if result.get('previous_pricing'):
                prev = result['previous_pricing']
                print(f"  Previous: ${prev['input']}/${prev['output']} per 1M tokens")

                change = result.get('change_info', {})
                if change.get('input_change_percent'):
                    print(f"  Input change: {change['input_change_percent']:+.2f}% ({change['input_direction']})")
                if change.get('output_change_percent'):
                    print(f"  Output change: {change['output_change_percent']:+.2f}% ({change['output_direction']})")

    except Exception as e:
        print(f"✗ ERROR: {e}", file=sys.stderr)
        return 1

    return 0


def bulk_update_pricing(args):
    """Update pricing for multiple models from JSON file"""
    updater = get_pricing_updater()

    try:
        with open(args.file, 'r') as f:
            updates = json.load(f)

        if not isinstance(updates, list):
            print("✗ ERROR: JSON file must contain a list of updates", file=sys.stderr)
            return 1

        print(f"Processing {len(updates)} pricing updates...")
        results = updater.bulk_update_pricing(updates)

        # Print summary
        print(f"\n✓ Updated: {len(results['updated'])} models")
        for item in results['updated']:
            print(f"  - {item['model']}: ${item['new_pricing']['input']}/${item['new_pricing']['output']}")

        if results['unchanged']:
            print(f"\n○ Unchanged: {len(results['unchanged'])} models")
            for item in results['unchanged']:
                print(f"  - {item['model']}")

        if results['failed']:
            print(f"\n✗ Failed: {len(results['failed'])} models", file=sys.stderr)
            for item in results['failed']:
                print(f"  - {item['model']}: {item['error']}", file=sys.stderr)
            return 1

    except FileNotFoundError:
        print(f"✗ ERROR: File not found: {args.file}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"✗ ERROR: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ ERROR: {e}", file=sys.stderr)
        return 1

    return 0


def show_pricing_history(args):
    """Show pricing history for models"""
    updater = get_pricing_updater()

    history = updater.get_pricing_history(
        model_name=args.model,
        provider=args.provider,
        limit=args.limit
    )

    if not history:
        print("No pricing history found")
        return 0

    print(f"Pricing History ({len(history)} updates)")
    print("=" * 80)

    for record in history:
        print(f"\n{record['model']} ({record['provider']})")
        print(f"  Timestamp: {record['timestamp']}")
        print(f"  New: ${record['input_price']}/${record['output_price']} per 1M tokens")

        if record.get('previous_input_price') is not None:
            print(f"  Previous: ${record['previous_input_price']}/${record['previous_output_price']} per 1M tokens")

        if record.get('source'):
            print(f"  Source: {record['source']}")

        if record.get('notes'):
            print(f"  Notes: {record['notes']}")

    return 0


def check_stale_pricing(args):
    """Check for models with stale pricing"""
    updater = get_pricing_updater()

    stale_models = updater.get_models_needing_update(days_threshold=args.days)

    if not stale_models:
        print(f"✓ All models have been validated within the last {args.days} days")
        return 0

    # Group by provider
    by_provider = {}
    for model in stale_models:
        provider = model['provider']
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(model)

    print(f"⚠ {len(stale_models)} models need pricing validation")
    print("=" * 80)

    for provider, models in sorted(by_provider.items()):
        print(f"\n{provider.upper()} ({len(models)} models)")
        for model in models:
            status = model['status']
            days = model.get('days_since_update')

            if status == "never_validated":
                print(f"  ✗ {model['model']}: Never validated")
            else:
                print(f"  ⚠ {model['model']}: {days} days since last update")

    print(f"\nTo update pricing, run:")
    print(f"  python scripts/manage_pricing.py update MODEL_NAME --input X.XX --output X.XX")

    return 0


def generate_pricing_report(args):
    """Generate a pricing change report"""
    updater = get_pricing_updater()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days) if args.days else None

    report = updater.generate_pricing_change_report(
        start_date=start_date,
        end_date=end_date
    )

    summary = report['summary']

    print(f"Pricing Change Report")
    if args.days:
        print(f"Period: Last {args.days} days")
    else:
        print(f"Period: All time")
    print("=" * 80)

    print(f"\nSummary:")
    print(f"  Total changes: {summary['total_changes']}")
    print(f"  Price increases: {summary['increases']}")
    print(f"  Price decreases: {summary['decreases']}")
    print(f"  New models: {summary['new_models']}")

    if report['price_increases']:
        print(f"\n▲ Price Increases ({len(report['price_increases'])})")
        for item in report['price_increases']:
            old_avg = (item['old_input'] + item['old_output']) / 2
            new_avg = (item['new_input'] + item['new_output']) / 2
            change_pct = ((new_avg - old_avg) / old_avg) * 100
            print(f"  {item['model']}: +{change_pct:.1f}% ({item['timestamp'][:10]})")

    if report['price_decreases']:
        print(f"\n▼ Price Decreases ({len(report['price_decreases'])})")
        for item in report['price_decreases']:
            old_avg = (item['old_input'] + item['old_output']) / 2
            new_avg = (item['new_input'] + item['new_output']) / 2
            change_pct = ((new_avg - old_avg) / old_avg) * 100
            print(f"  {item['model']}: {change_pct:.1f}% ({item['timestamp'][:10]})")

    if report['new_models']:
        print(f"\n✓ New Models ({len(report['new_models'])})")
        for item in report['new_models']:
            print(f"  {item['model']}: ${item['new_input']}/${item['new_output']} ({item['timestamp'][:10]})")

    return 0


def export_pricing(args):
    """Export current pricing to JSON"""
    updater = get_pricing_updater()

    pricing_data = updater.export_current_pricing()

    output_file = args.output or "pricing_export.json"

    try:
        with open(output_file, 'w') as f:
            json.dump(pricing_data, f, indent=2)

        print(f"✓ Exported pricing for {len(pricing_data)} models to {output_file}")

    except Exception as e:
        print(f"✗ ERROR: {e}", file=sys.stderr)
        return 1

    return 0


def list_models(args):
    """List all models, optionally filtered by provider"""
    if args.provider:
        models = list_models_by_provider(args.provider)
        print(f"{args.provider.upper()} Models ({len(models)})")
    else:
        models = [m for m in MODEL_PRICING.keys() if m != "default"]
        print(f"All Models ({len(models)})")

    print("=" * 80)

    for model in sorted(models):
        pricing = MODEL_PRICING[model]
        print(f"{model}: ${pricing['input']}/${pricing['output']} per 1M tokens")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Manage LLM model pricing data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update pricing for a model')
    update_parser.add_argument('model', help='Model name (e.g., gpt-4o)')
    update_parser.add_argument('--input', type=float, required=True, help='Input price per 1M tokens')
    update_parser.add_argument('--output', type=float, required=True, help='Output price per 1M tokens')
    update_parser.add_argument('--source', help='Source of pricing data')
    update_parser.add_argument('--notes', help='Notes about this update')

    # Bulk update command
    bulk_parser = subparsers.add_parser('bulk-update', help='Update pricing for multiple models from JSON')
    bulk_parser.add_argument('file', help='JSON file with pricing updates')

    # History command
    history_parser = subparsers.add_parser('history', help='View pricing history')
    history_parser.add_argument('--model', help='Filter by model name')
    history_parser.add_argument('--provider', help='Filter by provider')
    history_parser.add_argument('--limit', type=int, help='Limit number of results per model')

    # Check stale command
    stale_parser = subparsers.add_parser('check-stale', help='Check for stale pricing')
    stale_parser.add_argument('--days', type=int, default=30, help='Days threshold (default: 30)')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate pricing change report')
    report_parser.add_argument('--days', type=int, help='Number of days to include (omit for all time)')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export current pricing to JSON')
    export_parser.add_argument('--output', help='Output file path (default: pricing_export.json)')

    # List command
    list_parser = subparsers.add_parser('list', help='List all models')
    list_parser.add_argument('--provider', help='Filter by provider (openai, anthropic, gemini, fireworks)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to appropriate handler
    handlers = {
        'update': update_model_pricing,
        'bulk-update': bulk_update_pricing,
        'history': show_pricing_history,
        'check-stale': check_stale_pricing,
        'report': generate_pricing_report,
        'export': export_pricing,
        'list': list_models
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
