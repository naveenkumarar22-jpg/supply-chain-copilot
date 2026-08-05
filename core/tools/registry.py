from typing import Callable, Optional

from core.tools.inventory_risk import check_inventory_risk
from core.tools.supplier_delay import check_supplier_delay

REGISTRY: dict[str, Callable] = {
    "supplier_delay_tool": check_supplier_delay,
    "inventory_risk_tool": check_inventory_risk,
}


def get_tool(route: str) -> Optional[Callable]:
    return REGISTRY.get(route)
