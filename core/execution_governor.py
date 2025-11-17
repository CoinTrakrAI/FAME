#!/usr/bin/env python3
"""
FAME AGI - Dual-Core Execution Governor
Smart fallback logic with latency prediction, GPU/CPU detection, and mode switching
"""

import logging
import time
import psutil
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode types"""
    FAST = "fast"  # Prioritize speed
    DEEP = "deep"  # Prioritize quality
    BALANCED = "balanced"  # Balance speed and quality


@dataclass
class ExecutionDecision:
    """Execution decision with reasoning"""
    executor: str
    mode: ExecutionMode
    expected_latency: float
    confidence: float
    reasoning: str
    fallback_chain: List[str]


class ExecutionGovernor:
    """
    Smart execution governor that decides which executor to use.
    Implements auto-fallback, latency prediction, and device detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = ExecutionMode.BALANCED
        
        # Device detection
        self.has_gpu = self._detect_gpu()
        self.cpu_count = psutil.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Latency tracking
        self.latency_history: Dict[str, List[float]] = {}
        
        # Preference settings
        self.cloud_preference = config.get("execution", {}).get("prefer_cloud", True)
        self.local_preference = config.get("execution", {}).get("prefer_local", False)
        
        logger.info(f"Execution Governor initialized: GPU={self.has_gpu}, CPU={self.cpu_count}, RAM={self.memory_gb:.1f}GB")
    
    def decide_executor(self, intent: str, complexity: int, latency_sensitive: bool = False,
                       context: Optional[Dict[str, Any]] = None) -> ExecutionDecision:
        """
        Decide which executor to use based on context.
        This is the core decision-making function.
        """
        context = context or {}
        
        # Determine mode
        if latency_sensitive or complexity < 3:
            mode = ExecutionMode.FAST
        elif complexity > 7:
            mode = ExecutionMode.DEEP
        else:
            mode = ExecutionMode.BALANCED
        
        # Build executor chain
        executors = self._build_executor_chain(intent, complexity, mode, latency_sensitive)
        
        # Select primary executor
        primary_executor = executors[0]
        fallback_chain = executors[1:]
        
        # Predict latency
        expected_latency = self._predict_latency(primary_executor, complexity)
        
        # Estimate confidence
        confidence = self._estimate_confidence(primary_executor, intent, complexity)
        
        reasoning = f"Selected {primary_executor} in {mode.value} mode (latency: {expected_latency:.2f}s, confidence: {confidence:.2f})"
        
        return ExecutionDecision(
            executor=primary_executor,
            mode=mode,
            expected_latency=expected_latency,
            confidence=confidence,
            reasoning=reasoning,
            fallback_chain=fallback_chain
        )
    
    def _build_executor_chain(self, intent: str, complexity: int, mode: ExecutionMode,
                             latency_sensitive: bool) -> List[str]:
        """Build ordered executor chain"""
        chain = []
        
        if mode == ExecutionMode.FAST:
            # Fast mode: local first, then cloud
            if self.local_preference and self.has_gpu:
                chain.append("local_llm")
            if self.cloud_preference:
                chain.append("cloud_llm")
            if not chain:
                chain.append("local_llm")
                chain.append("cloud_llm")
            chain.append("vector_recall")  # Fastest fallback
        
        elif mode == ExecutionMode.DEEP:
            # Deep mode: cloud first, then local
            if self.cloud_preference:
                chain.append("cloud_llm")
            if self.local_preference:
                chain.append("local_llm")
            if not chain:
                chain.append("cloud_llm")
                chain.append("local_llm")
            chain.append("knowledge_fusion")
            chain.append("vector_recall")
        
        else:  # BALANCED
            # Balanced: try both, prefer based on availability
            if self.cloud_preference:
                chain.append("cloud_llm")
            if self.local_preference:
                chain.append("local_llm")
            if not chain:
                # Default: cloud first, then local
                chain.append("cloud_llm")
                chain.append("local_llm")
            chain.append("knowledge_fusion")
            chain.append("vector_recall")
        
        return chain
    
    def _predict_latency(self, executor: str, complexity: int) -> float:
        """Predict execution latency"""
        # Base latencies (seconds)
        base_latencies = {
            "local_llm": 0.5,
            "cloud_llm": 1.5,
            "vector_recall": 0.1,
            "knowledge_fusion": 0.8,
            "web_search": 2.0
        }
        
        base = base_latencies.get(executor, 1.0)
        
        # Adjust for complexity
        complexity_factor = 1.0 + (complexity - 1) * 0.2
        
        # Adjust for device
        if executor == "local_llm":
            if self.has_gpu:
                complexity_factor *= 0.5  # GPU is faster
            else:
                complexity_factor *= 1.5  # CPU is slower
        
        # Use historical data if available
        if executor in self.latency_history:
            recent_latencies = self.latency_history[executor][-10:]
            if recent_latencies:
                avg_latency = sum(recent_latencies) / len(recent_latencies)
                # Blend with prediction
                base = (base * 0.3 + avg_latency * 0.7)
        
        return base * complexity_factor
    
    def _estimate_confidence(self, executor: str, intent: str, complexity: int) -> float:
        """Estimate confidence in executor"""
        confidence = 0.7  # Base confidence
        
        # Adjust based on executor
        if executor == "cloud_llm":
            confidence = 0.9  # Cloud LLMs are most reliable
        elif executor == "local_llm":
            confidence = 0.7 if self.has_gpu else 0.5
        elif executor == "vector_recall":
            confidence = 0.8  # Vector search is reliable
        elif executor == "knowledge_fusion":
            confidence = 0.85  # Fusion is high quality
        
        # Adjust for complexity
        if complexity > 7:
            confidence *= 0.9  # High complexity reduces confidence
        elif complexity < 3:
            confidence *= 1.1  # Low complexity increases confidence
        
        return min(1.0, confidence)
    
    def record_latency(self, executor: str, latency: float):
        """Record actual latency for future predictions"""
        if executor not in self.latency_history:
            self.latency_history[executor] = []
        self.latency_history[executor].append(latency)
        
        # Keep only recent history
        if len(self.latency_history[executor]) > 100:
            self.latency_history[executor] = self.latency_history[executor][-100:]
    
    def should_fallback(self, executor: str, elapsed_time: float, 
                       expected_latency: float) -> bool:
        """Determine if should fallback to next executor"""
        # Fallback if taking too long
        if elapsed_time > expected_latency * 2:
            return True
        
        # Fallback if timeout exceeded
        timeout = self._get_timeout(executor)
        if elapsed_time > timeout:
            return True
        
        return False
    
    def _get_timeout(self, executor: str) -> float:
        """Get timeout for executor"""
        timeouts = {
            "local_llm": 10.0,
            "cloud_llm": 30.0,
            "vector_recall": 2.0,
            "knowledge_fusion": 15.0,
            "web_search": 20.0
        }
        return timeouts.get(executor, 15.0)
    
    def _detect_gpu(self) -> bool:
        """Detect if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass
        
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=2)
            return result.returncode == 0
        except Exception:
            pass
        
        return False
    
    def set_mode(self, mode: ExecutionMode):
        """Set execution mode"""
        self.mode = mode
        logger.info(f"Execution mode set to {mode.value}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        avg_latencies = {
            executor: sum(latencies) / len(latencies) if latencies else 0.0
            for executor, latencies in self.latency_history.items()
        }
        
        return {
            "mode": self.mode.value,
            "has_gpu": self.has_gpu,
            "cpu_count": self.cpu_count,
            "memory_gb": self.memory_gb,
            "avg_latencies": avg_latencies,
            "cloud_preference": self.cloud_preference,
            "local_preference": self.local_preference
        }

