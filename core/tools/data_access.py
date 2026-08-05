import csv
from pathlib import Path
from typing import List, Optional

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "skus.csv"
_NUMERIC_FIELDS = ("lead_time_days", "stock_on_hand", "reorder_point", "open_po_delay_days")

_cache: Optional[List[dict]] = None


def load_skus() -> List[dict]:
    global _cache
    if _cache is None:
        with open(_DATA_PATH, newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            for field in _NUMERIC_FIELDS:
                row[field] = int(row[field])
        _cache = rows
    return _cache
