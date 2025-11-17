"""Reward computation utilities for training events."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml


@dataclass(slots=True)
class RewardEngine:
    """Compute scalar rewards for telemetry events."""

    config: Dict

    @classmethod
    def from_file(cls, path: Path) -> "RewardEngine":
        if not path.exists():
            return cls(config={})
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return cls(config=data)

    def compute(self, event: Dict) -> float:
        components = self.config.get("reward_components", {})
        reward = 0.0

        feedback_type = (event.get("feedback_type") or "").lower()
        score = event.get("score")
        if feedback_type == "explicit" and isinstance(score, (int, float)):
            mapping = components.get("explicit_feedback", {})
            reward += self._scale_score(score, mapping, default=0.0)
        elif isinstance(score, (int, float)):
            # Treat implicit scores as smaller contribution
            reward += 0.5 * score

        if event.get("context", {}).get("task_success") or event.get("task_success"):
            reward += components.get("task_success", 0.0)

        if event.get("guardrail_violation"):
            reward += components.get("guardrail_violation", -2.0)

        preference_hash = event.get("preferences", {}).get("integrity_hash")
        if preference_hash:
            reward += components.get("preference_alignment", {}).get("matched", 0.0)

        trade = event.get("trade") or {}
        roi = trade.get("roi")
        if isinstance(roi, (int, float)):
            config = components.get("trade_roi", {})
            clip = float(config.get("clip", 0.1))
            scale = float(config.get("scale", 0.5))
            clipped = max(-clip, min(clip, roi))
            reward += scale * (clipped / clip) if clip else 0.0

        risk_context = event.get("risk") or {}
        risk_conf = components.get("risk_signals", {})
        stress_crash = risk_context.get("stress_market_crash")
        if isinstance(stress_crash, (int, float)):
            threshold = float(risk_conf.get("crash_threshold", -0.15))
            if stress_crash < threshold:
                reward += float(risk_conf.get("crash_penalty", -1.0))
        liquidity_pressure = risk_context.get("liquidity_pressure")
        if isinstance(liquidity_pressure, (int, float)):
            limit = float(risk_conf.get("liquidity_threshold", 0.25))
            if liquidity_pressure > limit:
                reward += float(risk_conf.get("liquidity_penalty", -0.5))

        latency_ms = event.get("latency_ms")
        if isinstance(latency_ms, (int, float)):
            latency_cfg = components.get("response_latency_ms", {})
            fast_threshold = latency_cfg.get("fast_threshold")
            if fast_threshold and latency_ms <= fast_threshold:
                reward += latency_cfg.get("fast_bonus", 0.0)
            else:
                reward += latency_cfg.get("slow_penalty", 0.0)

        confidence = event.get("confidence")
        if isinstance(confidence, (int, float)):
            reward += (confidence - 0.5) * 0.2

        return float(max(-5.0, min(5.0, reward)))

    @staticmethod
    def _scale_score(score: float, mapping: Dict, default: float) -> float:
        if not mapping:
            return default
        positive = mapping.get("positive", 0.0)
        negative = mapping.get("negative", 0.0)
        neutral = mapping.get("neutral", 0.0)
        # Assume score already normalised 0-1
        if score >= 0.66:
            return positive
        if score <= 0.33:
            return negative
        return neutral

