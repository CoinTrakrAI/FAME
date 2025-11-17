"""
Position-sizing and allocation utilities for strategy outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore


@dataclass(slots=True)
class AllocationConfig:
    max_leverage: float = 3.0
    target_volatility: float = 0.1
    min_allocation: float = 0.0
    max_allocation: float = 0.2
    rebalance_threshold: float = 0.05


def risk_parity_allocation(
    assets: Iterable[str],
    volatility: Dict[str, float],
    correlations: Optional[Dict[Tuple[str, str], float]] = None,
) -> Dict[str, float]:
    """
    Compute weights proportional to inverse volatility.
    """
    vol_array = []
    asset_list = list(assets)
    for asset in asset_list:
        vol_array.append(abs(float(volatility.get(asset, 1.0))) or 1.0)
    total = sum(1 / v for v in vol_array)
    return {asset: (1 / vol) / total for asset, vol in zip(asset_list, vol_array)}


def apply_position_scales(
    base_positions: Dict[str, float],
    target_var: float,
    current_var: float,
    max_leverage: float,
) -> Dict[str, float]:
    scale = 1.0
    if current_var > 0:
        scale = min(1.0, target_var / current_var)
    total_abs = sum(abs(size) for size in base_positions.values())
    if total_abs > max_leverage > 0:
        scale = min(scale, max_leverage / total_abs)
    return {asset: size * scale for asset, size in base_positions.items()}

