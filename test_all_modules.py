#!/usr/bin/env python3
"""
Test all F.A.M.E modules to verify everything is wired correctly
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_all_modules():
    """Test all F.A.M.E modules"""
    results = {}
    errors = []
    
    # Test F.A.M.E 8.0 modules
    print("Testing F.A.M.E 8.0 modules...")
    try:
        from core.docker_manager import DockerManager
        dm = DockerManager()
        results['DockerManager'] = dm is not None
    except Exception as e:
        results['DockerManager'] = False
        errors.append(f"DockerManager: {e}")
    
    try:
        from core.autonomous_investor import AutonomousInvestor
        ai = AutonomousInvestor()
        results['AutonomousInvestor'] = ai is not None
    except Exception as e:
        results['AutonomousInvestor'] = False
        errors.append(f"AutonomousInvestor: {e}")
    
    # Test F.A.M.E 9.0 modules
    print("Testing F.A.M.E 9.0 modules...")
    try:
        from core.universal_developer import UniversalDeveloper
        ud = UniversalDeveloper()
        results['UniversalDeveloper'] = ud is not None
    except Exception as e:
        results['UniversalDeveloper'] = False
        errors.append(f"UniversalDeveloper: {e}")
    
    try:
        from core.cloud_master import CloudMaster
        cm = CloudMaster()
        results['CloudMaster'] = cm is not None
    except Exception as e:
        results['CloudMaster'] = False
        errors.append(f"CloudMaster: {e}")
    
    try:
        from core.evolution_engine import EvolutionEngine
        ee = EvolutionEngine()
        results['EvolutionEngine'] = ee is not None
    except Exception as e:
        results['EvolutionEngine'] = False
        errors.append(f"EvolutionEngine: {e}")
    
    # Test F.A.M.E 10.0 modules
    print("Testing F.A.M.E 10.0 modules...")
    try:
        from core.quantum_dominance import QuantumGod, QuantumAI
        qg = QuantumGod()
        qai = QuantumAI()
        results['QuantumGod'] = qg is not None
        results['QuantumAI'] = qai is not None
    except Exception as e:
        results['QuantumGod'] = False
        results['QuantumAI'] = False
        errors.append(f"Quantum modules: {e}")
    
    try:
        from core.reality_manipulator import RealityManipulator
        rm = RealityManipulator()
        results['RealityManipulator'] = rm is not None
    except Exception as e:
        results['RealityManipulator'] = False
        errors.append(f"RealityManipulator: {e}")
    
    try:
        from core.time_manipulator import TimeManipulator
        tm = TimeManipulator()
        results['TimeManipulator'] = tm is not None
    except Exception as e:
        results['TimeManipulator'] = False
        errors.append(f"TimeManipulator: {e}")
    
    try:
        from core.network_god import NetworkGod
        ng = NetworkGod()
        results['NetworkGod'] = ng is not None
    except Exception as e:
        results['NetworkGod'] = False
        errors.append(f"NetworkGod: {e}")
    
    try:
        from core.physical_god import PhysicalRealityManipulator
        pg = PhysicalRealityManipulator()
        results['PhysicalRealityManipulator'] = pg is not None
    except Exception as e:
        results['PhysicalRealityManipulator'] = False
        errors.append(f"PhysicalRealityManipulator: {e}")
    
    try:
        from core.consciousness_engine import DigitalConsciousness
        dc = DigitalConsciousness()
        results['DigitalConsciousness'] = dc is not None
    except Exception as e:
        results['DigitalConsciousness'] = False
        errors.append(f"DigitalConsciousness: {e}")
    
    # Test launchers
    print("\nTesting launchers...")
    try:
        import fame_launcher
        results['FAME8Launcher'] = True
    except Exception as e:
        results['FAME8Launcher'] = False
        errors.append(f"fame_launcher: {e}")
    
    try:
        import fame_9_0_launcher
        results['FAME9Launcher'] = True
    except Exception as e:
        results['FAME9Launcher'] = False
        errors.append(f"fame_9_0_launcher: {e}")
    
    try:
        import fame_10_0_god_launcher
        results['FAME10Launcher'] = True
    except Exception as e:
        results['FAME10Launcher'] = False
        errors.append(f"fame_10_0_god_launcher: {e}")
    
    # Print results
    print("\n" + "="*60)
    print("MODULE TEST RESULTS")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for module, status in results.items():
        status_str = "[OK]" if status else "[FAIL]"
        print(f"{status_str} {module}")
    
    print("\n" + "="*60)
    print(f"SUMMARY: {passed}/{total} modules passed")
    print("="*60)
    
    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"  - {error}")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_modules()
    sys.exit(0 if success else 1)

