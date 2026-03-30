# backend/tests/unit/test_tier_scoring.py
import pytest
from decimal import Decimal

from backend.app.core.exceptions import (
    InsufficientDataException,
    StockBridgeException,
)
from backend.app.services.tier_scoring import (
    TierDecisionResult,
    TierScoringInput,
    compute_tier_decision,
)


def make_input(
    total_po_lines=30,
    backorder_rate=Decimal("0.05"),
    on_time_rate=Decimal("0.95"),
    current_tier="Silver",
    tier_locked=False,
    consecutive_qualifying_months=0,
    consecutive_underperforming_months=0,
) -> TierScoringInput:
    return TierScoringInput(
        total_po_lines=total_po_lines,
        backorder_rate=backorder_rate,
        on_time_rate=on_time_rate,
        current_tier=current_tier,
        tier_locked=tier_locked,
        consecutive_qualifying_months=consecutive_qualifying_months,
        consecutive_underperforming_months=consecutive_underperforming_months,
    )


def test_compute_tier_insufficient_data_below_20_lines():
    data = make_input(total_po_lines=19)
    with pytest.raises(InsufficientDataException) as exc_info:
        compute_tier_decision(data)
    assert exc_info.value.details["total_po_lines"] == 19
    assert exc_info.value.details["minimum_required"] == 20


def test_compute_tier_insufficient_data_zero_lines():
    data = make_input(total_po_lines=0)
    with pytest.raises(InsufficientDataException) as exc_info:
        compute_tier_decision(data)
    assert exc_info.value.details["total_po_lines"] == 0


def test_compute_tier_exactly_20_lines_is_sufficient():
    data = make_input(
        total_po_lines=20,
        backorder_rate=Decimal("0.20"),
        on_time_rate=Decimal("0.80"),
        current_tier="Silver",
    )
    result = compute_tier_decision(data)
    assert isinstance(result, TierDecisionResult)
    assert result.insufficient_data is False


def test_compute_tier_locked_supplier_tier_unchanged():
    data = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.02"),
        on_time_rate=Decimal("0.98"),
        current_tier="Gold",
        tier_locked=True,
        consecutive_qualifying_months=3,
    )
    result = compute_tier_decision(data)
    assert result.new_tier == "Gold"
    assert "locked" in result.decision_reason.lower()


def test_compute_tier_locked_streaks_still_update():
    data = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.02"),
        on_time_rate=Decimal("0.98"),
        current_tier="Gold",
        tier_locked=True,
        consecutive_qualifying_months=1,
        consecutive_underperforming_months=0,
    )
    result = compute_tier_decision(data)
    # Tier unchanged but qualifying streak increments
    # 1 prior + current = 2
    assert result.new_tier == "Gold"
    assert result.consecutive_qualifying_months == 2


def test_compute_tier_worst_metric_wins_backorder_overrides_ontime():
    # on_time_rate qualifies Diamond (>= 0.95)
    # backorder_rate only qualifies Gold (<= 0.10 but > 0.05)
    # Worst-metric-wins: result tier to promote toward is Gold

    # With 2 prior qualifying months, current month qualifies
    # -> streak becomes 3 -> promotes to Gold (not Diamond)
    data = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.08"),
        on_time_rate=Decimal("0.97"),
        current_tier="Silver",
        consecutive_qualifying_months=2,
    )
    result = compute_tier_decision(data)
    assert result.new_tier == "Gold"  # not Diamond

    # With 1 prior qualifying month -> streak becomes 2
    # -> stays Silver
    data_not_yet = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.08"),
        on_time_rate=Decimal("0.97"),
        current_tier="Silver",
        consecutive_qualifying_months=1,
    )
    result_not_yet = compute_tier_decision(data_not_yet)
    assert result_not_yet.new_tier == "Silver"
    assert result_not_yet.consecutive_qualifying_months == 2


def test_compute_tier_worst_metric_wins_ontime_overrides_backorder():
    data = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.03"),
        on_time_rate=Decimal("0.92"),
        current_tier="Silver",
        consecutive_qualifying_months=3,
    )
    result = compute_tier_decision(data)
    assert result.new_tier == "Gold"


def test_compute_tier_silver_to_gold_requires_3_consecutive():
    qualifying_metrics = dict(
        total_po_lines=30,
        backorder_rate=Decimal("0.08"),
        on_time_rate=Decimal("0.92"),
        current_tier="Silver",
    )
    # 1 prior qualifying month + current month = 2 total
    # streak increments to 2 -> stays Silver
    result_not_yet = compute_tier_decision(
        make_input(
            **qualifying_metrics,
            consecutive_qualifying_months=1,
        )
    )
    assert result_not_yet.new_tier == "Silver"
    assert result_not_yet.consecutive_qualifying_months == 2

    # 2 prior qualifying months + current month = 3 total
    # streak increments to 3 -> promotes to Gold
    result_promote = compute_tier_decision(
        make_input(
            **qualifying_metrics,
            consecutive_qualifying_months=2,
        )
    )
    assert result_promote.new_tier == "Gold"
    assert result_promote.consecutive_qualifying_months == 0


def test_compute_tier_gold_to_diamond_requires_3_consecutive():
    qualifying_metrics = dict(
        total_po_lines=30,
        backorder_rate=Decimal("0.03"),
        on_time_rate=Decimal("0.97"),
        current_tier="Gold",
    )
    # 1 prior qualifying month + current = 2 -> stays Gold
    result_not_yet = compute_tier_decision(
        make_input(
            **qualifying_metrics,
            consecutive_qualifying_months=1,
        )
    )
    assert result_not_yet.new_tier == "Gold"
    assert result_not_yet.consecutive_qualifying_months == 2

    # 2 prior qualifying months + current = 3 -> promotes Diamond
    result_promote = compute_tier_decision(
        make_input(
            **qualifying_metrics,
            consecutive_qualifying_months=2,
        )
    )
    assert result_promote.new_tier == "Diamond"
    assert result_promote.consecutive_qualifying_months == 0


def test_compute_tier_demotion_requires_2_consecutive():
    demotion_metrics = dict(
        total_po_lines=30,
        backorder_rate=Decimal("0.35"),
        on_time_rate=Decimal("0.80"),
        current_tier="Gold",
    )
    # 0 prior underperforming + current = 1 -> stays Gold
    result_not_yet = compute_tier_decision(
        make_input(
            **demotion_metrics,
            consecutive_underperforming_months=0,
        )
    )
    assert result_not_yet.new_tier == "Gold"
    assert result_not_yet.consecutive_underperforming_months == 1

    # 1 prior underperforming + current = 2 -> demotes to Silver
    result_demote = compute_tier_decision(
        make_input(
            **demotion_metrics,
            consecutive_underperforming_months=1,
        )
    )
    assert result_demote.new_tier == "Silver"
    assert result_demote.consecutive_underperforming_months == 0


def test_compute_tier_streak_resets_on_direction_change():
    data = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.35"),
        on_time_rate=Decimal("0.60"),
        current_tier="Silver",
        consecutive_qualifying_months=2,
        consecutive_underperforming_months=0,
    )
    result = compute_tier_decision(data)
    assert result.consecutive_qualifying_months == 0
    assert result.consecutive_underperforming_months == 1
    assert result.new_tier == "Silver"


def test_compute_tier_new_supplier_no_history_stays_silver():
    data = make_input(
        total_po_lines=0,
        current_tier="Silver",
    )
    with pytest.raises(InsufficientDataException):
        compute_tier_decision(data)


def test_compute_tier_all_thresholds_silver_boundaries():
    data_above = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.101"),
        on_time_rate=Decimal("0.92"),
        current_tier="Silver",
        consecutive_qualifying_months=3,
    )
    result_above = compute_tier_decision(data_above)
    assert result_above.new_tier == "Silver"

    data_exact = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.10"),
        on_time_rate=Decimal("0.90"),
        current_tier="Silver",
        consecutive_qualifying_months=3,
    )
    result_exact = compute_tier_decision(data_exact)
    assert result_exact.new_tier == "Gold"


def test_compute_tier_all_thresholds_gold_boundaries():
    data_above = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.051"),
        on_time_rate=Decimal("0.97"),
        current_tier="Gold",
        consecutive_qualifying_months=3,
    )
    result_above = compute_tier_decision(data_above)
    assert result_above.new_tier == "Gold"

    data_exact = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.05"),
        on_time_rate=Decimal("0.95"),
        current_tier="Gold",
        consecutive_qualifying_months=3,
    )
    result_exact = compute_tier_decision(data_exact)
    assert result_exact.new_tier == "Diamond"


def test_compute_tier_all_thresholds_diamond_boundaries():
    data_demote = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.31"),
        on_time_rate=Decimal("0.80"),
        current_tier="Diamond",
        consecutive_underperforming_months=2,
    )
    result_demote = compute_tier_decision(data_demote)
    assert result_demote.new_tier == "Gold"

    data_safe = make_input(
        total_po_lines=30,
        backorder_rate=Decimal("0.30"),
        on_time_rate=Decimal("0.80"),
        current_tier="Diamond",
        consecutive_underperforming_months=2,
    )
    result_safe = compute_tier_decision(data_safe)
    assert result_safe.new_tier == "Diamond"


def test_compute_tier_invalid_tier_raises_exception():
    data = make_input(
        total_po_lines=30,
        current_tier="Bronze",
    )
    with pytest.raises(StockBridgeException) as exc_info:
        compute_tier_decision(data)
    assert "Bronze" in exc_info.value.message
    assert exc_info.value.details["provided"] == "Bronze"
