"""Enterprise-grade trading preferences data models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
    constr,
    conint,
    confloat,
)


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


class TradingStyle(str, Enum):
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    POSITION_TRADING = "position_trading"
    SCALPING = "scalping"


AllowedTimeframe = constr(pattern=r"^(1m|5m|15m|1h|4h|1d)$")


class RiskParameters(BaseModel):
    max_position_size_pct: confloat(ge=0.01, le=0.25) = Field(..., description="Portion of portfolio allocated per position")
    max_daily_loss_pct: confloat(ge=0.005, le=0.1) = Field(..., description="Daily loss stop threshold")
    max_drawdown_pct: confloat(ge=0.05, le=0.3) = Field(..., description="Maximum portfolio drawdown")
    min_risk_reward_ratio: confloat(ge=1.0, le=3.0) = Field(..., description="Required risk/reward ratio")
    stop_loss_pct: confloat(ge=0.01, le=0.1) = Field(..., description="Default stop-loss percentage")

    @field_validator("max_position_size_pct")
    def validate_position_size(cls, value: float, info: ValidationInfo) -> float:
        daily_loss = (info.data or {}).get("max_daily_loss_pct")
        if daily_loss and value < daily_loss:
            raise ValueError("max_position_size_pct must be >= max_daily_loss_pct")
        return value

    @field_serializer(
        "max_position_size_pct",
        "max_daily_loss_pct",
        "max_drawdown_pct",
        "min_risk_reward_ratio",
        "stop_loss_pct",
    )
    def _serialize_float_fields(self, value: float, _info: ValidationInfo) -> float:
        return float(value)


class AuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    reason: str
    changes: Dict[str, Any]
    previous_state: Dict[str, Any]

    @field_serializer("timestamp")
    def _serialize_timestamp(self, value: datetime, _info: ValidationInfo) -> str:
        return value.isoformat()


class TradingPreferencesEnterprise(BaseModel):
    user_id: constr(min_length=1, max_length=100)
    session_id: constr(min_length=1, max_length=100)
    preference_version: str = "1.0.0"

    risk_tolerance: RiskTolerance
    trading_style: TradingStyle
    enabled_asset_classes: List[str] = Field(default_factory=lambda: ["stocks", "crypto"])
    default_timeframe: AllowedTimeframe = "1h"

    risk_parameters: RiskParameters
    watchlist: List[str] = Field(default_factory=list, max_length=100)
    banned_symbols: List[str] = Field(default_factory=list, max_length=50)
    max_open_positions: conint(ge=1, le=50) = 10

    allow_autonomous_trading: bool = False
    require_trade_confirmation: bool = True
    max_autonomous_position_size: confloat(ge=0.005, le=0.15) = 0.02
    require_2fa_for_trading: bool = False
    trading_pin_hash: Optional[str] = None
    compliance_acknowledged: bool = False
    risk_disclosure_accepted: bool = False

    notify_on_signals: bool = True
    notify_on_executions: bool = True
    notify_on_stop_loss: bool = True
    notify_portfolio_updates: bool = False
    preferred_currency: constr(min_length=3, max_length=5) = "USD"

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audit_trail: List[AuditEntry] = Field(default_factory=list)

    model_config = ConfigDict(validate_assignment=True)

    @field_serializer("created_at", "updated_at")
    def _serialize_datetime(self, value: datetime, _info: ValidationInfo) -> str:
        return value.isoformat()

    @model_validator(mode="after")
    def validate_asset_classes(self) -> "TradingPreferencesEnterprise":
        asset_classes = self.enabled_asset_classes or []
        normalised = []
        for asset in asset_classes:
            asset_lower = asset.lower()
            if asset_lower not in {"stocks", "crypto", "forex", "options", "futures", "etfs"}:
                raise ValueError(f"Unsupported asset class: {asset}")
            normalised.append(asset_lower)
        object.__setattr__(self, "enabled_asset_classes", normalised)
        return self

    def update_preferences(self, updates: Dict[str, Any], *, reason: str, actor: str) -> None:
        candidate_data = self.model_dump()
        candidate_data.update(updates)
        try:
            candidate = TradingPreferencesEnterprise.model_validate(candidate_data)
        except ValidationError as exc:
            raise ValueError(f"Invalid preference update: {exc}") from exc

        if "risk_tolerance" in updates:
            self._validate_risk_tolerance_change(candidate.risk_tolerance)
        if candidate.allow_autonomous_trading:
            self._validate_autonomous_trading_eligibility(candidate)

        snapshot = self._snapshot_state()
        for key in updates:
            object.__setattr__(self, key, getattr(candidate, key))
        self.updated_at = datetime.now(timezone.utc)
        change_set = {key: getattr(candidate, key) for key in updates}
        self.audit_trail.append(
            AuditEntry(
                actor=actor,
                reason=reason,
                changes=change_set,
                previous_state=snapshot,
            )
        )
        if len(self.audit_trail) > 100:
            self.audit_trail = self.audit_trail[-100:]

    def _validate_risk_tolerance_change(self, new_risk: RiskTolerance) -> None:
        recent_changes = [
            entry
            for entry in self.audit_trail
            if "risk_tolerance" in entry.changes
            and (datetime.now(timezone.utc) - entry.timestamp) < timedelta(hours=24)
        ]
        if recent_changes and new_risk in {RiskTolerance.AGGRESSIVE, RiskTolerance.EXTREME}:
            raise ValueError("Risk tolerance increases limited to once per 24 hours.")

    def _validate_autonomous_trading_eligibility(self, candidate: "TradingPreferencesEnterprise") -> None:
        if not candidate.compliance_acknowledged:
            raise ValueError("Compliance acknowledgement required for autonomous trading.")
        if not candidate.risk_disclosure_accepted:
            raise ValueError("Risk disclosure must be accepted for autonomous trading.")
        if candidate.risk_tolerance == RiskTolerance.EXTREME:
            raise ValueError("Autonomous trading not permitted for extreme risk tolerance.")

    def _snapshot_state(self) -> Dict[str, Any]:
        return {
            "risk_tolerance": self.risk_tolerance.value,
            "trading_style": self.trading_style.value,
            "allow_autonomous_trading": self.allow_autonomous_trading,
            "risk_parameters": self.risk_parameters.model_dump(),
        }

    def calculate_integrity_hash(self) -> str:
        import hashlib

        payload = f"{self.user_id}:{self.risk_tolerance.value}:{self.trading_style.value}:{len(self.watchlist)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

