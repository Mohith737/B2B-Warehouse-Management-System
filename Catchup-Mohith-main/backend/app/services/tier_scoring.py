# backend/app/services/tier_scoring.py
from dataclasses import dataclass
from decimal import Decimal

from backend.app.core.exceptions import (
    InsufficientDataException,
    StockBridgeException,
)

MIN_PO_LINES: int = 20

SILVER_TO_GOLD_BACKORDER_MAX: Decimal = Decimal("0.10")
SILVER_TO_GOLD_ONTIME_MIN: Decimal = Decimal("0.90")
GOLD_TO_DIAMOND_BACKORDER_MAX: Decimal = Decimal("0.05")
GOLD_TO_DIAMOND_ONTIME_MIN: Decimal = Decimal("0.95")
PROMOTION_STREAK_REQUIRED: int = 3

DEMOTION_BACKORDER_THRESHOLD: Decimal = Decimal("0.30")
DEMOTION_ONTIME_THRESHOLD: Decimal = Decimal("0.70")
DEMOTION_STREAK_REQUIRED: int = 2

TIER_ORDER: dict[str, int] = {
    "Silver": 0,
    "Gold": 1,
    "Diamond": 2,
}
VALID_TIERS: frozenset[str] = frozenset({"Silver", "Gold", "Diamond"})


@dataclass
class TierScoringInput:
    total_po_lines: int
    backorder_rate: Decimal
    on_time_rate: Decimal
    current_tier: str
    tier_locked: bool
    consecutive_qualifying_months: int
    consecutive_underperforming_months: int


@dataclass
class TierDecisionResult:
    new_tier: str
    consecutive_qualifying_months: int
    consecutive_underperforming_months: int
    decision_reason: str
    insufficient_data: bool


def _is_underperforming(
    backorder_rate: Decimal,
    on_time_rate: Decimal,
) -> bool:
    return (
        backorder_rate > DEMOTION_BACKORDER_THRESHOLD
        or on_time_rate < DEMOTION_ONTIME_THRESHOLD
    )


def _demote(current_tier: str) -> str:
    if current_tier == "Diamond":
        return "Gold"
    if current_tier == "Gold":
        return "Silver"
    return "Silver"


def _promote(current_tier: str) -> str:
    if current_tier == "Silver":
        return "Gold"
    if current_tier == "Gold":
        return "Diamond"
    return "Diamond"


def compute_tier_decision(
    data: TierScoringInput,
) -> TierDecisionResult:
    if data.total_po_lines < MIN_PO_LINES:
        raise InsufficientDataException(
            details={
                "total_po_lines": data.total_po_lines,
                "minimum_required": MIN_PO_LINES,
                "message": (
                    f"Tier scoring requires at least "
                    f"{MIN_PO_LINES} PO lines. "
                    f"Found {data.total_po_lines}."
                ),
            }
        )

    if data.current_tier not in VALID_TIERS:
        raise StockBridgeException(
            code="INVALID_TIER",
            message=f"Invalid tier value: {data.current_tier}",
            details={
                "provided": data.current_tier,
                "valid_values": sorted(VALID_TIERS),
            },
        )

    backorder_qualifies = _tier_for_backorder(data.backorder_rate, data.current_tier)
    ontime_qualifies = _tier_for_ontime(data.on_time_rate, data.current_tier)

    qualifying_tier_rank = min(
        TIER_ORDER[backorder_qualifies],
        TIER_ORDER[ontime_qualifies],
    )
    qualifying_tier = [t for t, r in TIER_ORDER.items() if r == qualifying_tier_rank][0]

    underperforming = _is_underperforming(data.backorder_rate, data.on_time_rate)

    # Step 4: Update streak counters (increment FIRST)
    if underperforming:
        new_qualifying = 0
        new_underperforming = data.consecutive_underperforming_months + 1
    elif TIER_ORDER[qualifying_tier] > TIER_ORDER[data.current_tier]:
        # Current month qualifies for a higher tier
        new_qualifying = data.consecutive_qualifying_months + 1
        new_underperforming = 0
    else:
        # Holding steady or below — reset both streaks
        new_qualifying = 0
        new_underperforming = 0

    # Step 5: If tier_locked, return current tier unchanged
    # but with updated streak counters
    if data.tier_locked:
        return TierDecisionResult(
            new_tier=data.current_tier,
            consecutive_qualifying_months=new_qualifying,
            consecutive_underperforming_months=new_underperforming,
            decision_reason=("Tier is locked. No automatic changes."),
            insufficient_data=False,
        )

    # Step 6: Check for demotion using INCREMENTED value
    if (
        new_underperforming >= DEMOTION_STREAK_REQUIRED
        and data.current_tier != "Silver"
    ):
        new_tier = _demote(data.current_tier)
        return TierDecisionResult(
            new_tier=new_tier,
            consecutive_qualifying_months=0,
            consecutive_underperforming_months=0,
            decision_reason=(
                f"Demoted from {data.current_tier} to "
                f"{new_tier} after "
                f"{new_underperforming} underperforming "
                f"months."
            ),
            insufficient_data=False,
        )

    # Step 7: Check for promotion using INCREMENTED value
    if (
        new_qualifying >= PROMOTION_STREAK_REQUIRED
        and TIER_ORDER[qualifying_tier] > TIER_ORDER[data.current_tier]
    ):
        new_tier = _promote(data.current_tier)
        return TierDecisionResult(
            new_tier=new_tier,
            consecutive_qualifying_months=0,
            consecutive_underperforming_months=0,
            decision_reason=(
                f"Promoted from {data.current_tier} to "
                f"{new_tier} after "
                f"{new_qualifying} consecutive qualifying "
                f"months."
            ),
            insufficient_data=False,
        )

    # Step 8: No tier change
    return TierDecisionResult(
        new_tier=data.current_tier,
        consecutive_qualifying_months=new_qualifying,
        consecutive_underperforming_months=new_underperforming,
        decision_reason="No tier change this period.",
        insufficient_data=False,
    )


def _tier_for_backorder(backorder_rate: Decimal, current_tier: str) -> str:
    if backorder_rate <= GOLD_TO_DIAMOND_BACKORDER_MAX:
        return "Diamond"
    if backorder_rate <= SILVER_TO_GOLD_BACKORDER_MAX:
        return "Gold"
    return "Silver"


def _tier_for_ontime(on_time_rate: Decimal, current_tier: str) -> str:
    if on_time_rate >= GOLD_TO_DIAMOND_ONTIME_MIN:
        return "Diamond"
    if on_time_rate >= SILVER_TO_GOLD_ONTIME_MIN:
        return "Gold"
    return "Silver"
