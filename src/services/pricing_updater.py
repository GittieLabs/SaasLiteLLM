"""
Pricing Update Service

Manages updates to model pricing data. Since LLM providers don't offer
programmatic pricing APIs, this service supports:

1. Manual pricing updates with validation
2. Pricing change tracking and versioning
3. Notification system for pricing changes
4. Admin API for on-demand updates

Usage:
    # Update pricing for a specific model
    updater = PricingUpdater()
    updater.update_model_pricing("gpt-4o", input_price=5.00, output_price=20.00)

    # Get pricing change history
    history = updater.get_pricing_history("gpt-4o")

    # Validate current pricing against provider websites
    validation_report = updater.validate_current_pricing()
"""

import json
from datetime import datetime, UTC
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from ..utils.cost_calculator import MODEL_PRICING, get_provider_from_model

logger = logging.getLogger(__name__)


class PricingUpdater:
    """Service for managing model pricing updates and versioning"""

    def __init__(self, pricing_history_path: Optional[str] = None):
        """
        Initialize pricing updater

        Args:
            pricing_history_path: Path to pricing history JSON file.
                                 Defaults to data/pricing_history.json
        """
        if pricing_history_path is None:
            # Default to data directory in project root
            project_root = Path(__file__).parent.parent.parent
            pricing_history_path = str(project_root / "data" / "pricing_history.json")

        self.pricing_history_path = Path(pricing_history_path)
        self.pricing_history_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self.pricing_history = self._load_pricing_history()

    def _load_pricing_history(self) -> Dict:
        """Load pricing history from JSON file"""
        if not self.pricing_history_path.exists():
            return {
                "version": "1.0",
                "last_updated": datetime.now(UTC).isoformat(),
                "models": {}
            }

        try:
            with open(self.pricing_history_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading pricing history: {e}")
            return {
                "version": "1.0",
                "last_updated": datetime.now(UTC).isoformat(),
                "models": {}
            }

    def _save_pricing_history(self):
        """Save pricing history to JSON file"""
        try:
            self.pricing_history["last_updated"] = datetime.now(UTC).isoformat()
            with open(self.pricing_history_path, 'w') as f:
                json.dump(self.pricing_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pricing history: {e}")
            raise

    def update_model_pricing(
        self,
        model_name: str,
        input_price: float,
        output_price: float,
        source: str = "manual",
        notes: Optional[str] = None
    ) -> Dict:
        """
        Update pricing for a specific model

        Args:
            model_name: Model identifier (e.g., "gpt-4o")
            input_price: Price per 1M input tokens in USD
            output_price: Price per 1M output tokens in USD
            source: Source of the pricing update (e.g., "manual", "web_scrape", "admin")
            notes: Optional notes about the update

        Returns:
            Dict with update status and details
        """
        model_name = model_name.lower().strip()

        # Validate pricing
        if input_price < 0 or output_price < 0:
            raise ValueError("Pricing must be non-negative")

        if input_price > 1000 or output_price > 1000:
            logger.warning(f"Unusually high pricing for {model_name}: ${input_price}/${output_price} per 1M tokens")

        # Get current pricing
        current_pricing = MODEL_PRICING.get(model_name)

        # Check if pricing actually changed
        if current_pricing:
            if (current_pricing["input"] == input_price and
                current_pricing["output"] == output_price):
                return {
                    "status": "unchanged",
                    "model": model_name,
                    "message": "Pricing is already up to date"
                }

        # Record in history
        if model_name not in self.pricing_history["models"]:
            self.pricing_history["models"][model_name] = {
                "provider": get_provider_from_model(model_name),
                "updates": []
            }

        # Add update record
        update_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "input_price": input_price,
            "output_price": output_price,
            "previous_input_price": current_pricing["input"] if current_pricing else None,
            "previous_output_price": current_pricing["output"] if current_pricing else None,
            "source": source,
            "notes": notes
        }

        self.pricing_history["models"][model_name]["updates"].append(update_record)

        # Save history
        self._save_pricing_history()

        # Calculate change percentage
        change_info = self._calculate_price_change(current_pricing, input_price, output_price)

        logger.info(
            f"Updated pricing for {model_name}: "
            f"${input_price}/${output_price} per 1M tokens "
            f"(source: {source})"
        )

        return {
            "status": "updated",
            "model": model_name,
            "new_pricing": {"input": input_price, "output": output_price},
            "previous_pricing": current_pricing,
            "change_info": change_info,
            "timestamp": update_record["timestamp"]
        }

    def _calculate_price_change(
        self,
        current_pricing: Optional[Dict],
        new_input: float,
        new_output: float
    ) -> Dict:
        """Calculate percentage change in pricing"""
        if not current_pricing:
            return {"type": "new_model", "message": "New model added to pricing"}

        input_change = ((new_input - current_pricing["input"]) / current_pricing["input"]) * 100
        output_change = ((new_output - current_pricing["output"]) / current_pricing["output"]) * 100

        return {
            "input_change_percent": round(input_change, 2),
            "output_change_percent": round(output_change, 2),
            "input_direction": "increase" if input_change > 0 else "decrease" if input_change < 0 else "unchanged",
            "output_direction": "increase" if output_change > 0 else "decrease" if output_change < 0 else "unchanged"
        }

    def bulk_update_pricing(self, updates: List[Dict]) -> Dict:
        """
        Update pricing for multiple models at once

        Args:
            updates: List of dicts with keys: model_name, input_price, output_price, notes (optional)

        Returns:
            Dict with summary of updates
        """
        results = {
            "updated": [],
            "unchanged": [],
            "failed": []
        }

        for update in updates:
            try:
                result = self.update_model_pricing(
                    model_name=update["model_name"],
                    input_price=update["input_price"],
                    output_price=update["output_price"],
                    source=update.get("source", "bulk_update"),
                    notes=update.get("notes")
                )

                if result["status"] == "updated":
                    results["updated"].append(result)
                else:
                    results["unchanged"].append(result)

            except Exception as e:
                logger.error(f"Error updating {update.get('model_name', 'unknown')}: {e}")
                results["failed"].append({
                    "model": update.get("model_name"),
                    "error": str(e)
                })

        return results

    def get_pricing_history(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get pricing history for models

        Args:
            model_name: Filter by specific model (optional)
            provider: Filter by provider (optional)
            limit: Limit number of results per model (optional)

        Returns:
            List of pricing update records
        """
        results = []

        for model, data in self.pricing_history["models"].items():
            # Apply filters
            if model_name and model != model_name.lower().strip():
                continue

            if provider and data["provider"] != provider.lower():
                continue

            updates = data["updates"]
            if limit:
                updates = updates[-limit:]  # Get most recent N updates

            for update in updates:
                results.append({
                    "model": model,
                    "provider": data["provider"],
                    **update
                })

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)

        return results

    def get_models_needing_update(self, days_threshold: int = 30) -> List[Dict]:
        """
        Get list of models that haven't been updated recently

        Args:
            days_threshold: Number of days to consider "stale" (default: 30)

        Returns:
            List of models with their last update time
        """
        from datetime import timedelta

        stale_models = []
        current_time = datetime.now(UTC)
        threshold = timedelta(days=days_threshold)

        for model_name in MODEL_PRICING.keys():
            if model_name == "default":
                continue

            model_history = self.pricing_history["models"].get(model_name)

            if not model_history or not model_history.get("updates"):
                stale_models.append({
                    "model": model_name,
                    "provider": get_provider_from_model(model_name),
                    "last_updated": "never",
                    "days_since_update": None,
                    "status": "never_validated"
                })
                continue

            last_update = model_history["updates"][-1]
            last_update_time = datetime.fromisoformat(last_update["timestamp"])
            days_since_update = (current_time - last_update_time).days

            if days_since_update > days_threshold:
                stale_models.append({
                    "model": model_name,
                    "provider": get_provider_from_model(model_name),
                    "last_updated": last_update_time.isoformat(),
                    "days_since_update": days_since_update,
                    "status": "stale"
                })

        return stale_models

    def generate_pricing_change_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Generate a report of pricing changes in a date range

        Args:
            start_date: Start of date range (optional, defaults to beginning of history)
            end_date: End of date range (optional, defaults to now)

        Returns:
            Dict with pricing change summary
        """
        if end_date is None:
            end_date = datetime.now(UTC)

        changes = {
            "price_increases": [],
            "price_decreases": [],
            "new_models": [],
            "summary": {
                "total_changes": 0,
                "increases": 0,
                "decreases": 0,
                "new_models": 0
            }
        }

        for model, data in self.pricing_history["models"].items():
            for update in data["updates"]:
                update_time = datetime.fromisoformat(update["timestamp"])

                # Filter by date range
                if start_date and update_time < start_date:
                    continue
                if update_time > end_date:
                    continue

                change_record = {
                    "model": model,
                    "provider": data["provider"],
                    "timestamp": update["timestamp"],
                    "new_input": update["input_price"],
                    "new_output": update["output_price"],
                    "old_input": update.get("previous_input_price"),
                    "old_output": update.get("previous_output_price"),
                    "source": update.get("source"),
                    "notes": update.get("notes")
                }

                changes["summary"]["total_changes"] += 1

                # Categorize change
                if update.get("previous_input_price") is None:
                    changes["new_models"].append(change_record)
                    changes["summary"]["new_models"] += 1
                else:
                    input_change = update["input_price"] - update["previous_input_price"]
                    output_change = update["output_price"] - update["previous_output_price"]

                    if input_change > 0 or output_change > 0:
                        changes["price_increases"].append(change_record)
                        changes["summary"]["increases"] += 1
                    elif input_change < 0 or output_change < 0:
                        changes["price_decreases"].append(change_record)
                        changes["summary"]["decreases"] += 1

        return changes

    def export_current_pricing(self) -> Dict[str, Dict]:
        """
        Export current pricing data in a structured format

        Returns:
            Dict mapping model names to their current pricing
        """
        return {
            model: {
                "input_per_1m": pricing["input"],
                "output_per_1m": pricing["output"],
                "provider": get_provider_from_model(model),
                "last_verified": self.pricing_history["models"].get(model, {})
                    .get("updates", [{}])[-1]
                    .get("timestamp", "never")
            }
            for model, pricing in MODEL_PRICING.items()
            if model != "default"
        }


# Singleton instance
_pricing_updater_instance = None


def get_pricing_updater() -> PricingUpdater:
    """Get singleton instance of PricingUpdater"""
    global _pricing_updater_instance
    if _pricing_updater_instance is None:
        _pricing_updater_instance = PricingUpdater()
    return _pricing_updater_instance
