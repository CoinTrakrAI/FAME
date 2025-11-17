"""Trading preferences data model and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskTolerance(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


class TradingStyle(Enum):
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    POSITION_TRADING = "position_trading"
    SCALPING = "scalping"


class AssetClass(Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"
    FOREX = "forex"
    OPTIONS = "options"
    FUTURES = "futures"
    ETFs = "etfs"


@dataclass
class RiskParameters:
    max_position_size_pct: float = 0.05
    max_daily_loss_pct: float = 0.02
    max_drawdown_pct: float = 0.08
    min_risk_reward_ratio: float = 1.5
    stop_loss_pct: float = 0.02

    @classmethod
    def from_risk_tolerance(cls, risk_tolerance: RiskTolerance) -> "RiskParameters":
        if risk_tolerance == RiskTolerance.CONSERVATIVE:
            return cls(
                max_position_size_pct=0.02,
                max_daily_loss_pct=0.01,
                max_drawdown_pct=0.08,
                min_risk_reward_ratio=2.0,
                stop_loss_pct=0.015,
            )
        if risk_tolerance == RiskTolerance.MODERATE:
            return cls(
                max_position_size_pct=0.05,
                max_daily_loss_pct=0.02,
                max_drawdown_pct=0.12,
                min_risk_reward_ratio=1.5,
                stop_loss_pct=0.02,
            )
        if risk_tolerance == RiskTolerance.AGGRESSIVE:
            return cls(
                max_position_size_pct=0.08,
                max_daily_loss_pct=0.04,
                max_drawdown_pct=0.18,
                min_risk_reward_ratio=1.2,
                stop_loss_pct=0.03,
            )
        return cls(
            max_position_size_pct=0.15,
            max_daily_loss_pct=0.08,
            max_drawdown_pct=0.25,
            min_risk_reward_ratio=1.0,
            stop_loss_pct=0.05,
        )


@dataclass
class TradingPreferences:
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    trading_style: TradingStyle = TradingStyle.SWING_TRADING
    enabled_asset_classes: Optional[List[AssetClass]] = None
    default_timeframe: str = "1h"

    risk_parameters: Optional[RiskParameters] = None

    watchlist: Optional[List[str]] = None
    banned_symbols: Optional[List[str]] = None
    max_open_positions: int = 10

    allow_autonomous_trading: bool = False
    require_trade_confirmation: bool = True
    max_autonomous_position_size: float = 0.02

    notify_on_signals: bool = True
    notify_on_executions: bool = True
    notify_on_stop_loss: bool = True
    notify_portfolio_updates: bool = False

    use_trading_jargon: bool = False
    preferred_currency: str = "USD"

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.enabled_asset_classes is None:
            self.enabled_asset_classes = [AssetClass.STOCKS, AssetClass.CRYPTO]
        if self.watchlist is None:
            self.watchlist = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD"]
        if self.banned_symbols is None:
            self.banned_symbols = []
        if self.risk_parameters is None:
            self.risk_parameters = RiskParameters.from_risk_tolerance(self.risk_tolerance)
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_tolerance"] = self.risk_tolerance.value
        data["trading_style"] = self.trading_style.value
        data["enabled_asset_classes"] = [ac.value for ac in self.enabled_asset_classes]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingPreferences":
        local = dict(data)
        if "risk_tolerance" in local:
            local["risk_tolerance"] = RiskTolerance(local["risk_tolerance"])
        if "trading_style" in local:
            local["trading_style"] = TradingStyle(local["trading_style"])
        if "enabled_asset_classes" in local and local["enabled_asset_classes"] is not None:
            local["enabled_asset_classes"] = [AssetClass(item) for item in local["enabled_asset_classes"]]
        if "risk_parameters" in local and local["risk_parameters"] is not None:
            local["risk_parameters"] = RiskParameters(**local["risk_parameters"])
        return cls(**local)

    def update(self, **kwargs: Any) -> None:
        risk_tolerance_changed = False
        for key, value in kwargs.items():
            if not hasattr(self, key):
                continue
            if key == "risk_tolerance" and isinstance(value, str):
                value = RiskTolerance(value)
                risk_tolerance_changed = True
            elif key == "trading_style" and isinstance(value, str):
                value = TradingStyle(value)
            elif key == "enabled_asset_classes":
                value = [AssetClass(item) if isinstance(item, str) else item for item in value]
            setattr(self, key, value)
        if risk_tolerance_changed:
            self.risk_parameters = RiskParameters.from_risk_tolerance(self.risk_tolerance)
        self.updated_at = datetime.now().isoformat()

    def validate_symbol(self, symbol: str) -> bool:
        symbol_upper = symbol.upper()
        if any(banned.upper() == symbol_upper for banned in self.banned_symbols):
            return False
        if symbol_upper.endswith("-USD") and AssetClass.CRYPTO not in self.enabled_asset_classes:
            return False
        return True

    def get_position_size(self, portfolio_value: float, volatility: float = 0.02) -> float:
        risk_amount = portfolio_value * self.risk_parameters.max_daily_loss_pct
        position_size = risk_amount / max(volatility * 2, 1e-6)
        max_size = portfolio_value * self.risk_parameters.max_position_size_pct
        return min(position_size, max_size)


DEFAULT_PREFERENCES = TradingPreferences()


