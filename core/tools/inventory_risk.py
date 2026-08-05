from core.intent import Intent
from core.tools.data_access import load_skus


def check_inventory_risk(intent: Intent) -> dict:
    sku = intent.sku
    rows = load_skus()

    if sku:
        return _check_single_sku(sku, rows)
    return _scan_all_skus(rows)


def _check_single_sku(sku: str, rows: list) -> dict:
    row = next((r for r in rows if r["sku"] == sku), None)
    if row is None:
        return {
            "tool": "inventory_risk",
            "scope": "single_sku",
            "sku": sku,
            "found": False,
            "at_risk": None,
            "confidence": "low",
            "reasoning": [f"{sku} was not found in the sample supplier/SKU dataset."],
        }

    at_risk = row["stock_on_hand"] <= row["reorder_point"]
    return {
        "tool": "inventory_risk",
        "scope": "single_sku",
        "sku": sku,
        "found": True,
        "supplier": row["supplier"],
        "criticality_tier": row["criticality_tier"],
        "stock_on_hand": row["stock_on_hand"],
        "reorder_point": row["reorder_point"],
        "at_risk": at_risk,
        "confidence": "high",
        "reasoning": [
            f"{sku} has {row['stock_on_hand']} units on hand against a reorder point of {row['reorder_point']}."
        ],
    }


def _scan_all_skus(rows: list) -> dict:
    at_risk_rows = [r for r in rows if r["stock_on_hand"] <= r["reorder_point"]]
    return {
        "tool": "inventory_risk",
        "scope": "all_skus",
        "found": True,
        "total_skus_scanned": len(rows),
        "at_risk_count": len(at_risk_rows),
        "at_risk_skus": [
            {
                "sku": r["sku"],
                "supplier": r["supplier"],
                "stock_on_hand": r["stock_on_hand"],
                "reorder_point": r["reorder_point"],
                "criticality_tier": r["criticality_tier"],
            }
            for r in at_risk_rows
        ],
        "at_risk": len(at_risk_rows) > 0,
        "confidence": "high",
        "reasoning": [f"Scanned {len(rows)} SKUs; {len(at_risk_rows)} are at or below their reorder point."],
    }
