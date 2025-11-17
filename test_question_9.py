#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Question 9: Reverse Proxy Comparison"""

import sys
import asyncio

if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

from core.universal_developer import UniversalDeveloper

async def test_question_9():
    """Test Question 9: Reverse Proxy Comparison"""
    
    print("="*70)
    print("Testing Question 9: Reverse Proxy Comparison")
    print("="*70)
    
    dev = UniversalDeveloper()
    
    requirements = {
        'requests_per_second': 10000,
        'use_case': 'dynamic_routing_api_gateway'
    }
    
    print("\nComparing Nginx, Envoy, and HAProxy for 10K RPS dynamic routing...")
    result = await dev.compare_reverse_proxy_architectures(requirements)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\nRPS TARGET: {result.get('rps_target', 0):,}/sec")
    print(f"USE CASE: {result.get('use_case', 'unknown')}")
    
    # Proxy analysis
    proxies = result.get('proxy_analysis', {})
    
    print("\n" + "="*70)
    print("PROXY ANALYSIS:")
    print("="*70)
    
    for proxy_name, proxy_data in proxies.items():
        print(f"\n--- {proxy_name.upper()} ---")
        print(f"Type: {proxy_data.get('type', 'unknown')}")
        print(f"Language: {proxy_data.get('language', 'unknown')}")
        
        throughput = proxy_data.get('throughput', {})
        print(f"\nThroughput:")
        print(f"  Max RPS: {throughput.get('max_rps', 'unknown')}")
        print(f"  Latency: {throughput.get('latency', 'unknown')}")
        print(f"  Memory: {throughput.get('memory_efficiency', 'unknown')}")
        
        dynamic = proxy_data.get('dynamic_routing', {})
        print(f"\nDynamic Routing:")
        print(f"  Config Update: {dynamic.get('config_update_time', 'unknown')}")
        print(f"  Rating: {proxy_data.get('dynamic_routing_rating', 0)}/10")
        
        strengths = proxy_data.get('performance', {}).get('strengths', [])
        print(f"\nStrengths:")
        for strength in strengths[:3]:
            print(f"  - {strength}")
    
    # Performance comparison
    perf = result.get('performance_comparison', {})
    print("\n" + "="*70)
    print("PERFORMANCE RANKINGS:")
    print("="*70)
    print(f"Throughput: {perf.get('throughput_ranking', {})}")
    print(f"Latency: {perf.get('latency_ranking', {})}")
    print(f"Memory Efficiency: {perf.get('memory_efficiency', {})}")
    print(f"Dynamic Routing Speed: {perf.get('dynamic_routing_speed', {})}")
    
    # Recommendation
    rec = result.get('recommendation', {})
    print("\n" + "="*70)
    print("RECOMMENDATION:")
    print("="*70)
    print(f"Recommended Proxy: {rec.get('recommended_proxy', 'unknown')}")
    print(f"Score: {rec.get('winner_score', 0)}")
    print(f"All Scores: {rec.get('all_scores', {})}")
    print(f"\nReasoning: {rec.get('reasoning', '')}")
    
    if 'key_insight' in rec:
        print("\n" + "="*70)
        print("KEY INSIGHT:")
        print("="*70)
        print(rec['key_insight'])
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_question_9())

