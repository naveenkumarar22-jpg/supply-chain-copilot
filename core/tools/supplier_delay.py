from core.intent import Intent
from core.tools.data_access import load_skus

_LONG_LEAD_TIME_DAYS = 25


def check_supplier_delay(intent: Intent) -> dict:
    sku = intent.sku

    if not intent.sku_resolved or not sku:
        return {
            "tool": "supplier_delay",
            "sku": sku,
            "found": False,
            "at_risk": None,
            "risk_level": "unknown",
            "confidence": "low",
            "reasoning": ["No SKU could be resolved from the query -- ask the user which SKU they mean."],
            "conflict_note": None,
        }

    row = next((r for r in load_skus() if r["sku"] == sku), None)
    if row is None:
        return {
            "tool": "supplier_delay",
            "sku": sku,
            "found": False,
            "at_risk": None,
            "risk_level": "unknown",
            "confidence": "low",
            "reasoning": [f"{sku} was not found in the sample supplier/SKU dataset."],
            "conflict_note": None,
        }

    lead_time_days = row["lead_time_days"]
    open_po_delay_days = row["open_po_delay_days"]
    reasoning = []
    conflict_note = None

    if open_po_delay_days > 0:
        at_risk = True
        risk_level = "high" if open_po_delay_days >= 10 else "medium"
        confidence = "high"
        reasoning.append(
            f"Open purchase order for {sku} is already running {open_po_delay_days} day(s) late."
        )
        if lead_time_days < _LONG_LEAD_TIME_DAYS:
            conflict_note = (
                f"Nominal lead time ({lead_time_days}d) is not unusually long, yet this "
                "specific order is already late -- treat as a live risk, not a supplier pattern."
            )
    elif lead_time_days >= _LONG_LEAD_TIME_DAYS:
        at_risk = True
        risk_level = "medium"
        confidence = "medium"
        reasoning.append(
            f"No active delay reported, but {row['supplier']}'s nominal lead time for {sku} "
            f"is {lead_time_days} days, above the {_LONG_LEAD_TIME_DAYS}-day watch threshold."
        )
        conflict_note = (
            "Risk is structural (long lead time), not confirmed by a current delay -- monitor rather than escalate."
        )
    else:
        at_risk = False
        risk_level = "low"
        confidence = "high"
        reasoning.append(
            f"No active delay on the open order, and {row['supplier']}'s lead time "
            f"({lead_time_days}d) is within normal range."
        )

    return {
        "tool": "supplier_delay",
        "sku": sku,
        "found": True,
        "supplier": row["supplier"],
        "region": row["region"],
        "criticality_tier": row["criticality_tier"],
        "lead_time_days": lead_time_days,
        "open_po_delay_days": open_po_delay_days,
        "at_risk": at_risk,
        "risk_level": risk_level,
        "confidence": confidence,
        "reasoning": reasoning,
        "conflict_note": conflict_note,
    }
