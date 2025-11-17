#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Question 7: Bayesian Signal Fusion"""

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

async def test_question_7():
    """Test Question 7: Signal Fusion"""
    
    print("="*70)
    print("Testing Question 7: Bayesian Signal Fusion Analysis")
    print("="*70)
    
    ai = AdvancedInvestorAI()
    
    print("\nAnalyzing Gold/NASDAQ vs BTC Funding signals...")
    result = await ai.analyze_signal_fusion_scenario()
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\nMETHODOLOGY: {result.get('methodology', 'unknown')}")
    
    # Signals analyzed
    signals = result.get('signals_analyzed', [])
    print(f"\nSIGNALS ANALYZED: {len(signals)}")
    
    for signal in signals:
        print(f"\n--- {signal.get('signal_name', 'unknown').upper()} ---")
        if 'current_ratio' in signal:
            print(f"Current Ratio: {signal.get('current_ratio', 0):.6f}")
        if 'percentile_rank' in signal:
            print(f"Percentile: {signal.get('percentile_rank', 0):.1f}%")
        if 'risk_off_strength' in signal:
            print(f"Risk-Off Strength: {signal.get('risk_off_strength', 'unknown')}")
            print(f"Probability: {signal.get('risk_off_probability', 0)*100:.1f}%")
        if 'divergence_level' in signal:
            print(f"Divergence: {signal.get('divergence_level', 'unknown')}")
            print(f"Probability: {signal.get('divergence_probability', 0)*100:.1f}%")
        if 'current_volatility' in signal:
            print(f"Volatility: {signal.get('current_volatility', 0)*100:.2f}%")
        print(f"Signal Reliability: {signal.get('signal_reliability', 0)*100:.0f}%")
    
    # Bayesian inference
    bayesian = result.get('bayesian_inference', {})
    print("\n" + "="*70)
    print("BAYESIAN INFERENCE:")
    print("="*70)
    print(f"Posterior Probability: {bayesian.get('posterior_probability', 0)*100:.1f}%")
    print(f"Signal Agreement: {bayesian.get('agreement', False)}")
    print(f"Stronger Signal: {bayesian.get('stronger_signal', 'unknown')}")
    print(f"Gold Evidence: {bayesian.get('gold_evidence_strength', 0):.3f}")
    print(f"BTC Evidence: {bayesian.get('btc_evidence_strength', 0):.3f}")
    print(f"Bayesian Confidence: {bayesian.get('bayesian_confidence', 0)*100:.0f}%")
    
    # Risk management recommendation
    rec = result.get('risk_management_recommendation', {})
    print("\n" + "="*70)
    print("RISK MANAGEMENT RECOMMENDATION:")
    print("="*70)
    print(f"Primary Signal: {rec.get('primary_signal', 'unknown')}")
    print(f"Gold Score: {rec.get('gold_score', 0):.3f}")
    print(f"BTC Score: {rec.get('btc_score', 0):.3f}")
    print(f"Action: {rec.get('recommended_action', 'unknown')}")
    print(f"Reasoning: {rec.get('reasoning', '')}")
    
    if 'key_insight' in rec:
        print("\n" + "="*70)
        print("KEY INSIGHT:")
        print("="*70)
        print(rec['key_insight'])
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_question_7())

