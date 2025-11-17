#!/usr/bin/env python3
"""
FAME AGI - Benchmark Suite
Speed, reasoning depth, memory precision, and trade signal confidence benchmarks
"""

import logging
import time
import asyncio
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run"""
    name: str
    metric: str
    value: float
    unit: str
    timestamp: float
    details: Dict[str, Any]


class BenchmarkSuite:
    """
    Comprehensive benchmark suite for FAME AGI evaluation.
    """
    
    def __init__(self, agi_core: Any):
        self.agi = agi_core
        self.results: List[BenchmarkResult] = []
        self.data_dir = Path("./benchmark_results")
        self.data_dir.mkdir(exist_ok=True)
    
    async def run_speed_benchmark(self, num_queries: int = 10) -> BenchmarkResult:
        """Benchmark response speed"""
        queries = [
            "What is the price of Bitcoin?",
            "Analyze Apple stock",
            "What are current market trends?",
            "Explain quantum computing",
            "Compare Tesla and Ford",
            "What is machine learning?",
            "Current weather forecast",
            "Latest AI news",
            "Stock market analysis",
            "Crypto market overview"
        ]
        
        latencies = []
        for query in queries[:num_queries]:
            start = time.time()
            try:
                await self.agi.run(query)
                latency = time.time() - start
                latencies.append(latency)
            except Exception as e:
                logger.error(f"Query failed: {e}")
        
        avg_latency = statistics.mean(latencies) if latencies else 0.0
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else avg_latency
        
        result = BenchmarkResult(
            name="speed_benchmark",
            metric="response_time",
            value=avg_latency,
            unit="seconds",
            timestamp=time.time(),
            details={
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "min_latency": min(latencies) if latencies else 0.0,
                "max_latency": max(latencies) if latencies else 0.0,
                "queries_tested": len(latencies)
            }
        )
        
        self.results.append(result)
        return result
    
    async def run_reasoning_depth_benchmark(self) -> BenchmarkResult:
        """Benchmark multi-step reasoning depth"""
        complex_queries = [
            "Plan a comprehensive investment strategy for a tech startup portfolio",
            "Analyze the relationship between interest rates and stock market performance",
            "Create a step-by-step guide for building a trading bot"
        ]
        
        reasoning_depths = []
        for query in complex_queries:
            try:
                result = await self.agi.run(query)
                plan_id = result.get("plan_id")
                
                if plan_id and hasattr(self.agi, 'active_plans'):
                    plan = self.agi.active_plans.get(plan_id)
                    if plan:
                        depth = len(plan.tasks) if hasattr(plan, 'tasks') else 1
                        reasoning_depths.append(depth)
            except Exception as e:
                logger.error(f"Reasoning test failed: {e}")
        
        avg_depth = statistics.mean(reasoning_depths) if reasoning_depths else 0.0
        
        result = BenchmarkResult(
            name="reasoning_depth_benchmark",
            metric="average_depth",
            value=avg_depth,
            unit="tasks",
            timestamp=time.time(),
            details={
                "avg_depth": avg_depth,
                "max_depth": max(reasoning_depths) if reasoning_depths else 0,
                "queries_tested": len(reasoning_depths)
            }
        )
        
        self.results.append(result)
        return result
    
    async def run_memory_precision_benchmark(self) -> BenchmarkResult:
        """Benchmark memory retrieval precision"""
        # Store test knowledge
        test_queries = [
            ("What is FAME?", "FAME is a Financial AI system"),
            ("What is the capital of France?", "Paris"),
            ("Who invented the telephone?", "Alexander Graham Bell")
        ]
        
        # Store in memory
        for query, answer in test_queries:
            try:
                await self.agi.run(query)  # This stores in memory
            except Exception:
                pass
        
        # Test retrieval
        correct = 0
        total = len(test_queries)
        
        for query, expected_answer in test_queries:
            try:
                result = await self.agi.run(query)
                response = result.get("response", "").lower()
                if expected_answer.lower() in response:
                    correct += 1
            except Exception:
                pass
        
        precision = correct / total if total > 0 else 0.0
        
        result = BenchmarkResult(
            name="memory_precision_benchmark",
            metric="precision",
            value=precision,
            unit="ratio",
            timestamp=time.time(),
            details={
                "precision": precision,
                "correct": correct,
                "total": total,
                "accuracy": f"{precision * 100:.1f}%"
            }
        )
        
        self.results.append(result)
        return result
    
    async def run_trade_signal_confidence_benchmark(self) -> BenchmarkResult:
        """Benchmark trade signal confidence accuracy"""
        financial_queries = [
            "What is the current price of Bitcoin?",
            "Analyze Apple stock performance",
            "What are the best crypto investments?",
            "Stock market prediction for next week",
            "Crypto market analysis"
        ]
        
        confidences = []
        for query in financial_queries:
            try:
                result = await self.agi.run(query)
                confidence = result.get("confidence", 0.0)
                confidences.append(confidence)
            except Exception:
                pass
        
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        result = BenchmarkResult(
            name="trade_signal_confidence_benchmark",
            metric="average_confidence",
            value=avg_confidence,
            unit="ratio",
            timestamp=time.time(),
            details={
                "avg_confidence": avg_confidence,
                "min_confidence": min(confidences) if confidences else 0.0,
                "max_confidence": max(confidences) if confidences else 0.0,
                "queries_tested": len(confidences)
            }
        )
        
        self.results.append(result)
        return result
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks"""
        logger.info("Starting benchmark suite...")
        
        results = {}
        
        # Speed benchmark
        logger.info("Running speed benchmark...")
        results["speed"] = await self.run_speed_benchmark()
        
        # Reasoning depth benchmark
        logger.info("Running reasoning depth benchmark...")
        results["reasoning"] = await self.run_reasoning_depth_benchmark()
        
        # Memory precision benchmark
        logger.info("Running memory precision benchmark...")
        results["memory"] = await self.run_memory_precision_benchmark()
        
        # Trade signal confidence benchmark
        logger.info("Running trade signal confidence benchmark...")
        results["confidence"] = await self.run_trade_signal_confidence_benchmark()
        
        # Save results
        self.save_results()
        
        return results
    
    def save_results(self):
        """Save benchmark results to disk"""
        results_file = self.data_dir / f"benchmark_{int(time.time())}.json"
        try:
            data = {
                "timestamp": time.time(),
                "results": [
                    {
                        "name": r.name,
                        "metric": r.metric,
                        "value": r.value,
                        "unit": r.unit,
                        "details": r.details
                    }
                    for r in self.results
                ]
            }
            with open(results_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Benchmark results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get benchmark summary"""
        return {
            "total_benchmarks": len(self.results),
            "results": [
                {
                    "name": r.name,
                    "metric": r.metric,
                    "value": r.value,
                    "unit": r.unit
                }
                for r in self.results
            ]
        }


async def main():
    """Run benchmarks"""
    from core.agi_core import AGICore
    import yaml
    
    # Load config
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize AGI
    agi = AGICore(config)
    
    # Run benchmarks
    suite = BenchmarkSuite(agi)
    results = await suite.run_all_benchmarks()
    
    # Print summary
    print("\n=== Benchmark Results ===")
    for name, result in results.items():
        print(f"{name}: {result.value:.3f} {result.unit}")
        print(f"  Details: {result.details}")


if __name__ == "__main__":
    asyncio.run(main())

