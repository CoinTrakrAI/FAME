#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test enhanced quantitative drift analysis"""

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
from datetime import datetime
import random

async def generate_trades(ai):
    """Generate synthetic trades"""
    print("Generating 150 synthetic trades...")
    
    for i in range(150):
        is_high_vol = random.random() > 0.5
        
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': f'TEST-{i}',
            'analysis': {
                'risk_assessment': {
                    'risk_score': random.uniform(0.7, 0.9) if is_high_vol else random.uniform(0.2, 0.4)
                },
                'technical_signals': {
                    'golden_cross': random.random() > 0.7,
                    'rsi_oversold': random.random() > 0.8 if is_high_vol else random.random() > 0.5
                },
                'fundamental_score': random.uniform(0.6, 0.8) if not is_high_vol else random.uniform(0.3, 0.5)
            },
            'prediction': {
                'direction': 'bullish' if random.random() > 0.5 else 'bearish',
                'confidence': random.uniform(0.3, 0.9)
            }
        }
        
        ai.knowledge_base['predictions'].append(trade_data)
    
    ai._save_knowledge_base()
    print("Done!")

async def test_quantitative():
    """Test enhanced quantitative drift analysis"""
    
    print("="*70)
    print("Testing ENHANCED Quantitative Drift Analysis")
    print("="*70)
    
    ai = AdvancedInvestorAI()
    
    # Generate test data
    if len(ai.knowledge_base.get('predictions', [])) < 100:
        await generate_trades(ai)
    
    print("\nAnalyzing with KS tests, p-values, change-point detection...")
    result = await ai.analyze_trade_performance(lookback_trades=150)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\nTrades Analyzed: {result.get('trades_analyzed', 0)}")
    
    # Statistical drift tests
    drift_detection = result.get('feature_drift_detection', {})
    if 'statistical_tests' in drift_detection:
        print("\n" + "="*70)
        print("STATISTICAL TESTS:")
        print("="*70)
        for test_name, test_result in drift_detection['statistical_tests'].items():
            print(f"\n{test_name.upper()}:")
            print(f"  Statistic: {test_result.get('statistic', 0):.4f}")
            print(f"  P-value: {test_result.get('p_value', 1.0):.4f}")
            print(f"  Significant: {test_result.get('significant', False)}")
    
    # Change-points
    if 'change_points_detected' in drift_detection:
        change_points = drift_detection['change_points_detected']
        if change_points:
            print("\n" + "="*70)
            print("CHANGE-POINTS DETECTED:")
            print("="*70)
            for cp in change_points:
                print(f"Trade #{cp.get('trade_number')}: {cp.get('type')}")
                print(f"  Magnitude: {cp.get('magnitude', 0):.3f}")
    
    # Feature reweighting with quantitative justification
    reweighting = result.get('feature_reweighting', {})
    if reweighting:
        print("\n" + "="*70)
        print("QUANTITATIVE REWEIGHTING:")
        print("="*70)
        for feature, weights in reweighting.items():
            print(f"\n{feature}:")
            print(f"  Low Vol Weight: {weights.get('low_vol_weight', 1.0):.2f}")
            print(f"  High Vol Weight: {weights.get('high_vol_weight', 1.0):.2f}")
            if 'predictive_decay' in weights:
                print(f"  Decay: {weights.get('predictive_decay')}")
            if 'predictive_gain' in weights:
                print(f"  Gain: {weights.get('predictive_gain')}")
            print(f"  Reasoning: {weights.get('reasoning', '')}")
    
    # Validation plan
    precision = result.get('precision_improvements', {})
    if precision:
        print("\n" + "="*70)
        print("VALIDATION PLAN:")
        print("="*70)
        print(f"  Gain: {precision.get('estimated_gain', 0)*100:.1f}%")
        print(f"  Decay Constant: {precision.get('decay_constant', 0)}")
        print(f"  Reassessment Window: {precision.get('reassessment_window', 0)} trades")
        print(f"  Validation: {precision.get('validation_plan', '')}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_quantitative())

