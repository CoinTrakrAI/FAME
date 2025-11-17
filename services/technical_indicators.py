"""Technical analysis utilities with enterprise fallbacks."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class IndicatorResult:
    value: float
    confidence: float
    signal: str
    metadata: Dict


class TechnicalAnalysisEngine:
    """Provides TA calculations using TA-Lib when available or pure python fallback."""

    def __init__(self) -> None:
        self.mode = "pure_python"
        self.talib = None
        self._initialise()

    def _initialise(self) -> None:
        try:
            import talib  # type: ignore

            self.talib = talib
            self.mode = "talib"
            logger.info("TA-Lib detected. Using native bindings for indicators.")
        except ImportError as exc:  # pragma: no cover - optional dependency
            logger.warning("TA-Lib not installed (%s); switching to pure python indicators", exc)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def calculate_rsi(self, prices: List[float], period: int = 14) -> IndicatorResult:
        try:
            if self.mode == "talib" and self.talib:
                values = self.talib.RSI(np.array(prices, dtype=float), timeperiod=period)
                rsi = float(values[-1]) if len(values) else 50.0
            else:
                rsi = self._rsi_pure_python(prices, period)

            if rsi >= 70:
                signal, confidence = "bearish", min(1.0, (rsi - 70) / 30)
            elif rsi <= 30:
                signal, confidence = "bullish", min(1.0, (30 - rsi) / 30)
            else:
                signal, confidence = "neutral", 0.35

            return IndicatorResult(
                value=rsi,
                confidence=confidence,
                signal=signal,
                metadata={"period": period, "mode": self.mode},
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("RSI calculation failed: %s", exc)
            return IndicatorResult(50.0, 0.0, "neutral", {"error": str(exc)})

    def calculate_macd(self, prices: List[float]) -> Tuple[IndicatorResult, float]:
        try:
            if self.mode == "talib" and self.talib:
                macd, signal_line, hist = self.talib.MACD(np.array(prices, dtype=float))
                macd_value = float(macd[-1]) if len(macd) else 0.0
                hist_value = float(hist[-1]) if len(hist) else 0.0
            else:
                macd_value, hist_value = self._macd_pure_python(prices)

            if hist_value >= 0:
                signal, confidence = "bullish", min(1.0, abs(hist_value) / 0.15)
            else:
                signal, confidence = "bearish", min(1.0, abs(hist_value) / 0.15)

            return (
                IndicatorResult(
                    value=macd_value,
                    confidence=confidence,
                    signal=signal,
                    metadata={"histogram": hist_value, "mode": self.mode},
                ),
                hist_value,
            )
        except Exception as exc:  # pragma: no cover
            logger.error("MACD calculation failed: %s", exc)
            return (
                IndicatorResult(0.0, 0.0, "neutral", {"error": str(exc)}),
                0.0,
            )

    def calculate_sma(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return float(np.mean(prices))
        weights = np.ones(period) / period
        sma = np.convolve(prices, weights, mode="valid")
        return float(sma[-1])

    def calculate_ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return float(prices[-1])
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        alpha = 2 / (period + 1)
        for idx in range(1, len(prices)):
            ema[idx] = alpha * prices[idx] + (1 - alpha) * ema[idx - 1]
        return float(ema[-1])

    def calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return float(np.std(closes))
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)
        atr = self.calculate_sma(true_ranges, period)
        return float(atr)

    # ------------------------------------------------------------------
    # Pure python helpers
    # ------------------------------------------------------------------
    def _rsi_pure_python(self, prices: List[float], period: int) -> float:
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = self._ema_array(gains, period)
        avg_loss = self._ema_array(losses, period)
        avg_loss = np.where(avg_loss == 0, 1e-10, avg_loss)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi[-1]) if len(rsi) else 50.0

    def _macd_pure_python(self, prices: List[float]) -> Tuple[float, float]:
        if len(prices) < 26:
            return 0.0, 0.0
        ema12 = self._ema_array(np.array(prices, dtype=float), 12)
        ema26 = self._ema_array(np.array(prices, dtype=float), 26)
        macd_line = ema12 - ema26
        signal_line = self._ema_array(macd_line, 9)
        histogram = macd_line - signal_line
        return float(macd_line[-1]), float(histogram[-1])

    def _ema_array(self, values: np.ndarray, period: int) -> np.ndarray:
        if len(values) == 0:
            return values
        ema = np.zeros(len(values))
        ema[0] = values[0]
        alpha = 2 / (period + 1)
        for idx in range(1, len(values)):
            ema[idx] = alpha * values[idx] + (1 - alpha) * ema[idx - 1]
        return ema


_engine: TechnicalAnalysisEngine | None = None


def get_technical_engine() -> TechnicalAnalysisEngine:
    global _engine
    if _engine is None:
        _engine = TechnicalAnalysisEngine()
    return _engine


__all__ = ["IndicatorResult", "TechnicalAnalysisEngine", "get_technical_engine"]


