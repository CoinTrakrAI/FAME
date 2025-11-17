#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Question 10: Ransomware Containment Response"""

import sys
import asyncio

if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

from core.universal_hacker import UniversalHacker

async def test_question_10():
    """Test Question 10: Ransomware Containment"""
    
    print("="*70)
    print("Testing Question 10: Ransomware Containment Response")
    print("="*70)
    
    hacker = UniversalHacker()
    
    scenario = {
        'environment': 'Windows domain',
        'threat': 'Active ransomware encrypting SMB shares',
        'severity': 'CRITICAL'
    }
    
    print("\nAnalyzing ransomware containment for Windows domain SMB encryption...")
    result = await hacker.ransomware_containment_response(scenario)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\nTHREAT TYPE: {result.get('threat_type', 'unknown')}")
    print(f"ENVIRONMENT: {result.get('environment', 'unknown')}")
    
    # Containment steps
    containment = result.get('containment_steps', [])
    print("\n" + "="*70)
    print("IMMEDIATE CONTAINMENT (0-15 minutes):")
    print("="*70)
    for step in containment:
        print(f"\nStep {step.get('step')}: {step.get('action')}")
        print(f"  Timeframe: {step.get('timeframe', '')}")
        print(f"  Priority: {step.get('priority', '')}")
        print(f"  Details:")
        for detail in step.get('details', [])[:2]:
            print(f"    - {detail}")
    
    # Triage steps
    triage = result.get('triage_steps', [])
    print("\n" + "="*70)
    print("TRIAGE (15-60 minutes):")
    print("="*70)
    for step in triage:
        print(f"\nStep {step.get('step')}: {step.get('action')}")
        print(f"  Timeframe: {step.get('timeframe', '')}")
        print(f"  Priority: {step.get('priority', '')}")
    
    # Recovery steps
    recovery = result.get('recovery_steps', [])
    print("\n" + "="*70)
    print("RECOVERY (Hours 1-24):")
    print("="*70)
    for step in recovery:
        print(f"\nStep {step.get('step')}: {step.get('action')}")
        print(f"  Timeframe: {step.get('timeframe', '')}")
        print(f"  Priority: {step.get('priority', '')}")
        if 'data_loss' in step:
            print(f"  Data Loss: {step.get('data_loss', '')}")
    
    # Data loss minimization
    data_protection = result.get('data_loss_minimization', {})
    print("\n" + "="*70)
    print("DATA LOSS MINIMIZATION:")
    print("="*70)
    estimated = data_protection.get('estimated_data_loss', {})
    for timeframe, estimate in estimated.items():
        print(f"  {timeframe.replace('_', ' ').title()}: {estimate}")
    
    # Timeline
    timeline = result.get('timeline', {})
    print("\n" + "="*70)
    print("INCIDENT TIMELINE:")
    print("="*70)
    for period, phase_info in list(timeline.items())[:3]:
        print(f"\n{period.replace('_', ' ').title()}:")
        print(f"  Phase: {phase_info.get('phase', '')}")
        print(f"  Goal: {phase_info.get('goal', '')}")
    
    # Key insight
    if 'key_insight' in result:
        print("\n" + "="*70)
        print("KEY INSIGHT:")
        print("="*70)
        print(result['key_insight'])
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_question_10())

