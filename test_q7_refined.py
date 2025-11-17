#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Question 7: REFINED Bayesian Signal Fusion"""

import sys
import asyncio

if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

from core.advanced_investor_ai import AdvancedInvestorAI

async def test_question_7_refined():
    """Test Question 7: REFINED Signal Fusion"""
    
    print("="*70)
    print("Testing Question 7: REFINED Bayesian Signal Fusion")
    print("="*70)
    
    ai = AdvancedInvestorAI()
    
    print("\nAnalyzing with temporal lag/lead awareness...")
    result = await ai.analyze_signal_fusion_scenario()
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    # Bayesian inference
    bayesian = result.get('bayesian_inference', {})
    posterior = bayesian.get('posterior_probability', 0.0)
    
    print(f"\nBAYESIAN POSTERIOR: {posterior*100:.1f}% risk-off")
    print(f"Signal Agreement: {bayesian.get('agreement', False)}")
    
    # Recommendation
    rec = result.get('risk_management_recommendation', {})
    print(f"\nPRIMARY SIGNAL: {rec.get('primary_signal', 'unknown')}")
    print(f"ACTION: {rec.get('recommended_action', 'unknown')}")
    
    # Temporal nature
    if 'signal_temporal_nature' in rec:
        print("\nSIGNAL TEMPORAL CHARACTERISTICS:")
        for signal, nature in rec['signal_temporal_nature'].items():
            print(f"  {signal}: {nature}")
    
    if 'key_insight' in rec:
        print("\n" + "="*70)
        print("KEY INSIGHT (REFINED):")
        print("="*70)
        print(rec['key_insight'])
    
    print("\n" + "="*70)
    print("TEST COMPLETE - INSTITUTIONAL-GRADE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_question_7_refined())

