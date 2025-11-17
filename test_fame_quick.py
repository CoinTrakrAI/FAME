#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test script for FAME"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fame_unified import get_fame

print("=" * 60)
print("FAME Production Verification Test")
print("=" * 60)
print()

# Test 1: Initialize
print("Test 1: Initialization...")
try:
    fame = get_fame()
    print("[OK] FAME initialized successfully")
    print(f"   Modules loaded: {len(fame.brain.plugins)}")
except Exception as e:
    print(f"[FAIL] Initialization failed: {e}")
    sys.exit(1)

print()

# Test 2: Health Check
print("Test 2: Health Monitoring...")
try:
    health = fame.get_health_status()
    print("[OK] Health check successful")
    print(f"   Status: {health.get('overall_status', 'unknown')}")
    print(f"   CPU: {health.get('system', {}).get('cpu_percent', 'N/A')}%")
    print(f"   Memory: {health.get('system', {}).get('memory_percent', 'N/A')}%")
except Exception as e:
    print(f"[FAIL] Health check failed: {e}")

print()

# Test 3: Simple Query
print("Test 3: Simple Query (Hello)...")
try:
    response = fame.process_text("Hello, how are you?")
    response_text = response.get('response', 'No response')
    print("[OK] Query processed successfully")
    print(f"   Response: {response_text[:100]}...")
    print(f"   Confidence: {response.get('confidence', 'N/A')}")
    print(f"   Intent: {response.get('intent', 'N/A')}")
except Exception as e:
    print(f"[FAIL] Query processing failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Factual Query
print("Test 4: Factual Query (President)...")
try:
    response = fame.process_text("Who is the current US president?")
    response_text = response.get('response', 'No response')
    print("[OK] Query processed successfully")
    print(f"   Response: {response_text[:200]}...")
    print(f"   Confidence: {response.get('confidence', 'N/A')}")
    print(f"   Intent: {response.get('intent', 'N/A')}")
except Exception as e:
    print(f"[FAIL] Query processing failed: {e}")

print()

# Test 5: Performance Metrics
print("Test 5: Performance Metrics...")
try:
    metrics = fame.get_performance_metrics()
    print("[OK] Metrics retrieved successfully")
    print(f"   Avg Response Time: {metrics.get('average_response_time', 0):.3f}s")
    print(f"   Total Requests: {metrics.get('total_requests', 0)}")
except Exception as e:
    print(f"[FAIL] Metrics retrieval failed: {e}")

print()
print("=" * 60)
print("All tests completed!")
print("=" * 60)

