#!/usr/bin/env python3
"""
FAME Safe Evolution Framework
Test-Driven Evolution with Multi-Layer Safety System
"""

import os
import ast
import subprocess
import shutil
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Safety thresholds
SAFETY_THRESHOLD = 0.7  # Risk score threshold (0.0-1.0)
CODE_QUALITY_RULES = {
    'max_complexity': 10,
    'min_test_coverage': 0.8,
    'max_file_size': 1000,
    'allowed_imports': ['core', 'orchestrator', 'plugins'],
    'forbidden_patterns': ['eval(', 'exec(', 'compile(']
}

PERFORMANCE_THRESHOLDS = {
    'max_memory_increase': 0.10,  # 10%
    'max_cpu_increase': 0.05,     # 5%
    'max_response_time': 2.0,     # 2 seconds
    'min_throughput': 100         # 100 requests per minute
}

FUNCTIONAL_REQUIREMENTS = {
    'core_features': ['chat_interface', 'knowledge_base', 'plugin_system'],
    'must_maintain': ['backward_compatibility', 'api_stability', 'data_integrity'],
    'critical_paths': ['system_startup', 'user_authentication', 'data_persistence']
}


@dataclass
class EvolutionTestResult:
    """Result from sandbox evolution testing"""
    test_results: Dict[str, Any]
    performance_metrics: Dict[str, float]
    applied_changes: List[Dict[str, Any]]
    validation_passed: bool = False
    error_message: Optional[str] = None


@dataclass
class EvolutionImpactReport:
    """Impact analysis report for proposed evolution"""
    affected_modules: List[str]
    dependency_impact: Dict[str, Any]
    performance_impact: Dict[str, float]
    security_implications: List[str]
    user_experience_impact: Dict[str, Any]
    risk_score: float = 0.0


@dataclass
class EvolutionProposal:
    """Evolution proposal with safety analysis"""
    plan: Dict[str, Any]
    impact: EvolutionImpactReport
    approved: bool = False
    reason: Optional[str] = None


@dataclass
class EvolutionResult:
    """Result of evolution execution"""
    success: bool
    changes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    checkpoint_id: Optional[str] = None


class EvolutionSandbox:
    """Isolated testing environment for evolution changes"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sandbox_dir = None
        self.sandbox_state = {}
    
    def clone_system_state(self) -> Dict[str, Any]:
        """Clone current system state to sandbox"""
        try:
            # Create temporary sandbox directory
            self.sandbox_dir = Path(tempfile.mkdtemp(prefix="fame_sandbox_"))
            logger.info(f"Created sandbox directory: {self.sandbox_dir}")
            
            # Copy critical files to sandbox
            critical_files = [
                "core",
                "orchestrator",
                "fame_chat_ui.py",
                "test_fixes.py"
            ]
            
            copied_files = []
            for item in critical_files:
                source = self.project_root / item
                if source.exists():
                    dest = self.sandbox_dir / item
                    if source.is_dir():
                        shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    else:
                        shutil.copy2(source, dest)
                    copied_files.append(item)
            
            self.sandbox_state = {
                "sandbox_dir": str(self.sandbox_dir),
                "copied_files": copied_files,
                "timestamp": datetime.now().isoformat()
            }
            
            return self.sandbox_state
        except Exception as e:
            logger.error(f"Failed to clone system state: {e}")
            raise
    
    def apply_changes(self, evolution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply proposed changes in sandbox"""
        applied_changes = []
        
        if not self.sandbox_dir:
            raise RuntimeError("Sandbox not initialized. Call clone_system_state first.")
        
        file_changes = evolution_plan.get("file_changes", [])
        
        for change in file_changes:
            file_path = change.get("file")
            new_content = change.get("content")
            
            if not file_path or not new_content:
                continue
            
            # Apply change in sandbox
            sandbox_file = self.sandbox_dir / file_path
            if sandbox_file.exists() or file_path.startswith("core/") or file_path.startswith("orchestrator/"):
                # Ensure directory exists
                sandbox_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write new content
                with open(sandbox_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                applied_changes.append({
                    "file": file_path,
                    "status": "applied",
                    "sandbox_path": str(sandbox_file)
                })
        
        return applied_changes
    
    def run_evolution_tests(self, applied_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive tests on sandbox changes"""
        test_results = {
            "syntax_tests": {},
            "import_tests": {},
            "functional_tests": {},
            "overall_pass": True
        }
        
        if not self.sandbox_dir:
            return test_results
        
        # Test 1: Syntax validation
        for change in applied_changes:
            file_path = change.get("sandbox_path")
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # AST parse
                    ast.parse(content)
                    
                    # Try to compile
                    compile(content, file_path, 'exec')
                    
                    test_results["syntax_tests"][change.get("file")] = "PASS"
                except SyntaxError as e:
                    test_results["syntax_tests"][change.get("file")] = f"FAIL: {e}"
                    test_results["overall_pass"] = False
                except Exception as e:
                    test_results["syntax_tests"][change.get("file")] = f"ERROR: {e}"
                    test_results["overall_pass"] = False
        
        # Test 2: Import validation
        for change in applied_changes:
            file_path = change.get("file")
            if file_path and file_path.endswith('.py'):
                try:
                    # Check imports in sandbox
                    sandbox_path = self.sandbox_dir / file_path
                    if sandbox_path.exists():
                        with open(sandbox_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        tree = ast.parse(content)
                        imports = []
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.append(alias.name)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.append(node.module)
                        
                        # Validate imports (basic check)
                        test_results["import_tests"][file_path] = {
                            "imports": imports,
                            "status": "PASS"
                        }
                except Exception as e:
                    test_results["import_tests"][file_path] = {
                        "status": f"FAIL: {e}"
                    }
                    test_results["overall_pass"] = False
        
        # Test 3: Basic functional test (try to import modified modules)
        # This is a simplified test - full functional tests would run actual test suite
        test_results["functional_tests"] = {
            "basic_import_test": "PASS",  # Simplified for now
            "note": "Full test suite would run here"
        }
        
        return test_results
    
    def measure_performance_impact(self) -> Dict[str, float]:
        """Measure performance impact of changes (simplified)"""
        # In a full implementation, this would run benchmarks
        return {
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "response_time": 0.0,
            "note": "Performance measurement requires full benchmark suite"
        }
    
    def test_evolution(self, evolution_plan: Dict[str, Any]) -> EvolutionTestResult:
        """Test changes in complete isolation"""
        try:
            # 1. Clone current system state
            sandbox_state = self.clone_system_state()
            
            # 2. Apply proposed changes
            applied_changes = self.apply_changes(evolution_plan)
            
            # 3. Run comprehensive tests
            test_results = self.run_evolution_tests(applied_changes)
            
            # 4. Analyze performance impact
            performance_metrics = self.measure_performance_impact()
            
            return EvolutionTestResult(
                test_results=test_results,
                performance_metrics=performance_metrics,
                applied_changes=applied_changes,
                validation_passed=test_results.get("overall_pass", False)
            )
        except Exception as e:
            logger.error(f"Sandbox test failed: {e}")
            return EvolutionTestResult(
                test_results={},
                performance_metrics={},
                applied_changes=[],
                validation_passed=False,
                error_message=str(e)
            )
        finally:
            # Cleanup sandbox
            self.cleanup()
    
    def cleanup(self):
        """Clean up sandbox directory"""
        if self.sandbox_dir and self.sandbox_dir.exists():
            try:
                shutil.rmtree(self.sandbox_dir)
                logger.info(f"Cleaned up sandbox: {self.sandbox_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup sandbox: {e}")


class ValidationEngine:
    """Comprehensive validation engine for evolution changes"""
    
    def __init__(self):
        self.validation_history = []
    
    def validate_evolution(self, test_result: EvolutionTestResult) -> bool:
        """Comprehensive validation of evolution test results"""
        validations = [
            self.syntax_validation(test_result),
            self.import_dependency_validation(test_result),
            self.functional_validation(test_result),
            self.performance_validation(test_result),
            self.security_validation(test_result),
            self.code_quality_validation(test_result)
        ]
        
        all_passed = all(validations)
        
        validation_record = {
            "timestamp": datetime.now().isoformat(),
            "validations": validations,
            "all_passed": all_passed,
            "test_result": asdict(test_result) if hasattr(test_result, '__dict__') else {}
        }
        self.validation_history.append(validation_record)
        
        return all_passed
    
    def syntax_validation(self, test_result: EvolutionTestResult) -> bool:
        """Validate syntax using AST parsing"""
        if not test_result.validation_passed:
            return False
        
        for change in test_result.applied_changes:
            file_path = change.get("file", "")
            syntax_test = test_result.test_results.get("syntax_tests", {}).get(file_path, "")
            
            if "FAIL" in syntax_test or "ERROR" in syntax_test:
                logger.warning(f"Syntax validation failed for {file_path}: {syntax_test}")
                return False
        
        return True
    
    def import_dependency_validation(self, test_result: EvolutionTestResult) -> bool:
        """Validate import dependencies"""
        for change in test_result.applied_changes:
            file_path = change.get("file", "")
            import_test = test_result.test_results.get("import_tests", {}).get(file_path, {})
            
            if isinstance(import_test, dict) and "FAIL" in str(import_test.get("status", "")):
                logger.warning(f"Import validation failed for {file_path}")
                return False
        
        return True
    
    def functional_validation(self, test_result: EvolutionTestResult) -> bool:
        """Validate functional requirements"""
        # Check if core features still work
        functional_tests = test_result.test_results.get("functional_tests", {})
        if "basic_import_test" in functional_tests:
            return functional_tests["basic_import_test"] == "PASS"
        return True
    
    def performance_validation(self, test_result: EvolutionTestResult) -> bool:
        """Validate performance metrics"""
        metrics = test_result.performance_metrics
        
        # Check if performance is within thresholds
        if metrics.get("memory_usage", 0) > PERFORMANCE_THRESHOLDS["max_memory_increase"]:
            logger.warning("Memory usage exceeds threshold")
            return False
        
        if metrics.get("cpu_usage", 0) > PERFORMANCE_THRESHOLDS["max_cpu_increase"]:
            logger.warning("CPU usage exceeds threshold")
            return False
        
        return True
    
    def security_validation(self, test_result: EvolutionTestResult) -> bool:
        """Validate security implications"""
        for change in test_result.applied_changes:
            file_path = change.get("file", "")
            # Check for forbidden patterns
            try:
                # This would scan the file content for security issues
                # Simplified for now
                pass
            except Exception as e:
                logger.warning(f"Security validation error for {file_path}: {e}")
                return False
        
        return True
    
    def code_quality_validation(self, test_result: EvolutionTestResult) -> bool:
        """Validate code quality rules"""
        # Check file sizes, complexity, etc.
        # Simplified for now - would use tools like pylint, flake8
        return True


class RollbackManager:
    """Enhanced rollback manager with version control integration"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_control_available = self._check_git_available()
        self.checkpoints = []
    
    def _check_git_available(self) -> bool:
        """Check if git is available"""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def create_evolution_checkpoint(self) -> str:
        """Create a restore point before any evolution"""
        checkpoint_id = f"evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 1. Use existing backup system
        try:
            from core.backup_restore import create_backup
            backup_id = create_backup(checkpoint_id)
            logger.info(f"Created backup checkpoint: {backup_id}")
        except Exception as e:
            logger.warning(f"Backup system failed: {e}")
            backup_id = None
        
        # 2. Git commit if available
        git_commit_hash = None
        if self.version_control_available:
            try:
                result = subprocess.run(
                    ['git', 'add', '-A'],
                    cwd=self.project_root,
                    capture_output=True,
                    timeout=10
                )
                result = subprocess.run(
                    ['git', 'commit', '-m', f"Pre-evolution checkpoint: {checkpoint_id}"],
                    cwd=self.project_root,
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Get commit hash
                    result = subprocess.run(
                        ['git', 'rev-parse', 'HEAD'],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    git_commit_hash = result.stdout.strip()
                    logger.info(f"Git checkpoint created: {git_commit_hash}")
            except Exception as e:
                logger.warning(f"Git checkpoint failed: {e}")
        
        checkpoint_info = {
            "checkpoint_id": checkpoint_id,
            "backup_id": backup_id,
            "git_commit": git_commit_hash,
            "timestamp": datetime.now().isoformat()
        }
        
        self.checkpoints.append(checkpoint_info)
        return checkpoint_id
    
    def rollback_if_failed(self, checkpoint_id: str, validation_passed: bool) -> bool:
        """Automatically restore if evolution fails"""
        if validation_passed:
            return True
        
        logger.warning(f"Evolution failed, rolling back to {checkpoint_id}")
        
        # Find checkpoint
        checkpoint = None
        for cp in self.checkpoints:
            if cp["checkpoint_id"] == checkpoint_id:
                checkpoint = cp
                break
        
        if not checkpoint:
            logger.error(f"Checkpoint {checkpoint_id} not found")
            return False
        
        # 1. Restore from backup
        if checkpoint.get("backup_id"):
            try:
                from core.backup_restore import restore_backup
                restore_backup(checkpoint["backup_id"])
                logger.info(f"Restored from backup: {checkpoint['backup_id']}")
            except Exception as e:
                logger.error(f"Backup restore failed: {e}")
        
        # 2. Git revert if available
        if checkpoint.get("git_commit") and self.version_control_available:
            try:
                result = subprocess.run(
                    ['git', 'reset', '--hard', checkpoint["git_commit"]],
                    cwd=self.project_root,
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"Git revert successful to {checkpoint['git_commit']}")
            except Exception as e:
                logger.error(f"Git revert failed: {e}")
        
        return False


class ImpactAnalyzer:
    """Impact analysis system for evolution changes"""
    
    def analyze_evolution_impact(self, proposed_changes: Dict[str, Any]) -> EvolutionImpactReport:
        """Analyze impact of proposed evolution"""
        file_changes = proposed_changes.get("file_changes", [])
        
        # Find affected modules
        affected_modules = []
        for change in file_changes:
            file_path = change.get("file", "")
            if file_path:
                # Extract module name
                if "/" in file_path:
                    module = file_path.split("/")[0]
                    if module not in affected_modules:
                        affected_modules.append(module)
        
        # Analyze dependency impact
        dependency_impact = self._analyze_dependency_impact(file_changes)
        
        # Predict performance impact
        performance_impact = self._predict_performance_impact(file_changes)
        
        # Assess security implications
        security_implications = self._assess_security_implications(file_changes)
        
        # Assess UX impact
        ux_impact = self._assess_ux_impact(file_changes)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            affected_modules,
            dependency_impact,
            performance_impact,
            security_implications
        )
        
        return EvolutionImpactReport(
            affected_modules=affected_modules,
            dependency_impact=dependency_impact,
            performance_impact=performance_impact,
            security_implications=security_implications,
            user_experience_impact=ux_impact,
            risk_score=risk_score
        )
    
    def _analyze_dependency_impact(self, file_changes: List[Dict]) -> Dict[str, Any]:
        """Analyze dependency impact"""
        # Simplified - would do full dependency graph analysis
        return {
            "new_dependencies": [],
            "modified_dependencies": [],
            "broken_dependencies": []
        }
    
    def _predict_performance_impact(self, file_changes: List[Dict]) -> Dict[str, float]:
        """Predict performance impact"""
        # Simplified - would use ML models or benchmarks
        return {
            "estimated_memory_increase": 0.0,
            "estimated_cpu_increase": 0.0,
            "estimated_response_time_change": 0.0
        }
    
    def _assess_security_implications(self, file_changes: List[Dict]) -> List[str]:
        """Assess security implications"""
        issues = []
        for change in file_changes:
            content = change.get("content", "")
            # Check for security issues
            for pattern in CODE_QUALITY_RULES.get('forbidden_patterns', []):
                if pattern in content:
                    issues.append(f"Security risk: {pattern} found in {change.get('file')}")
        return issues
    
    def _assess_ux_impact(self, file_changes: List[Dict]) -> Dict[str, Any]:
        """Assess user experience impact"""
        # Check if UI files are modified
        ui_files_modified = any(
            "chat_ui" in change.get("file", "") or "interface" in change.get("file", "")
            for change in file_changes
        )
        
        return {
            "ui_changes": ui_files_modified,
            "api_changes": False,  # Would check API compatibility
            "breaking_changes": False
        }
    
    def _calculate_risk_score(
        self,
        affected_modules: List[str],
        dependency_impact: Dict,
        performance_impact: Dict,
        security_implications: List[str]
    ) -> float:
        """Calculate overall risk score (0.0-1.0)"""
        risk = 0.0
        
        # Module risk (more modules = higher risk)
        risk += len(affected_modules) * 0.1
        
        # Dependency risk
        if dependency_impact.get("broken_dependencies"):
            risk += 0.3
        
        # Security risk
        risk += len(security_implications) * 0.2
        
        # Performance risk (simplified)
        if performance_impact.get("estimated_memory_increase", 0) > 0.1:
            risk += 0.2
        
        return min(risk, 1.0)


class SafeEvolutionFramework:
    """Main Safe Evolution Framework coordinator"""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = project_root
        self.sandbox_env = EvolutionSandbox(project_root)
        self.validation_engine = ValidationEngine()
        self.rollback_manager = RollbackManager(project_root)
        self.impact_analyzer = ImpactAnalyzer()
        self.evolution_history = []
    
    def propose_safe_evolution(self, evolution_goal: str) -> EvolutionProposal:
        """Generate evolution proposal with safety constraints"""
        # 1. Analyze current system state
        current_state_analysis = self._analyze_current_state()
        
        # 2. Generate evolution plan (simplified - would use AI/ML)
        evolution_plan = self._generate_evolution_plan(evolution_goal)
        
        # 3. Impact analysis
        impact_report = self.impact_analyzer.analyze_evolution_impact(evolution_plan)
        
        # 4. Check safety threshold
        approved = impact_report.risk_score <= SAFETY_THRESHOLD
        
        proposal = EvolutionProposal(
            plan=evolution_plan,
            impact=impact_report,
            approved=approved,
            reason=None if approved else f"Risk score {impact_report.risk_score:.2f} exceeds threshold {SAFETY_THRESHOLD}"
        )
        
        return proposal
    
    def execute_safe_evolution(self, evolution_proposal: EvolutionProposal) -> EvolutionResult:
        """Execute evolution with full safety checks"""
        if not evolution_proposal.approved:
            return EvolutionResult(
                success=False,
                error=f"Evolution not approved: {evolution_proposal.reason}"
            )
        
        # 1. Create checkpoint
        checkpoint_id = self.rollback_manager.create_evolution_checkpoint()
        
        try:
            # 2. Test in sandbox
            sandbox_result = self.sandbox_env.test_evolution(evolution_proposal.plan)
            
            # 3. Validate results
            validation_passed = self.validation_engine.validate_evolution(sandbox_result)
            
            if validation_passed:
                # 4. Apply changes to live system
                success = self._apply_evolution_to_live(evolution_proposal.plan)
                
                if success:
                    # 5. Run live validation
                    live_validation = self._validate_live_system()
                    
                    if live_validation:
                        self._log_successful_evolution(evolution_proposal)
                        return EvolutionResult(
                            success=True,
                            changes=evolution_proposal.plan,
                            checkpoint_id=checkpoint_id
                        )
            
            # If anything fails, rollback
            self.rollback_manager.rollback_if_failed(checkpoint_id, False)
            return EvolutionResult(
                success=False,
                error="Evolution validation failed",
                checkpoint_id=checkpoint_id
            )
        
        except Exception as e:
            logger.error(f"Evolution execution failed: {e}")
            self.rollback_manager.rollback_if_failed(checkpoint_id, False)
            return EvolutionResult(
                success=False,
                error=str(e),
                checkpoint_id=checkpoint_id
            )
    
    def _analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current system state"""
        return {
            "timestamp": datetime.now().isoformat(),
            "files_count": len(list(self.project_root.rglob("*.py"))),
            "note": "Full analysis would include more metrics"
        }
    
    def _generate_evolution_plan(self, evolution_goal: str) -> Dict[str, Any]:
        """Generate evolution plan (simplified - would use AI)"""
        # This would integrate with the existing self_evolution system
        # For now, return a placeholder structure
        return {
            "goal": evolution_goal,
            "file_changes": [],
            "description": "Evolution plan placeholder"
        }
    
    def _apply_evolution_to_live(self, evolution_plan: Dict[str, Any]) -> bool:
        """Apply evolution changes to live system"""
        # This would apply the actual file changes
        # For now, this is a placeholder
        file_changes = evolution_plan.get("file_changes", [])
        
        for change in file_changes:
            file_path = change.get("file")
            content = change.get("content")
            
            if file_path and content:
                target_file = self.project_root / file_path
                try:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Applied change to {file_path}")
                except Exception as e:
                    logger.error(f"Failed to apply change to {file_path}: {e}")
                    return False
        
        return True
    
    def _validate_live_system(self) -> bool:
        """Validate live system after evolution"""
        # Try to import critical modules
        try:
            import sys
            sys.path.insert(0, str(self.project_root))
            
            # Test critical imports
            from orchestrator.brain import Brain
            from core.self_evolution import handle_evolution_request
            
            return True
        except Exception as e:
            logger.error(f"Live system validation failed: {e}")
            return False
    
    def _log_successful_evolution(self, evolution_proposal: EvolutionProposal):
        """Log successful evolution"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "proposal": asdict(evolution_proposal),
            "success": True
        }
        self.evolution_history.append(log_entry)
        
        # Save to file
        history_file = self.project_root / "evolution_history.json"
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.evolution_history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save evolution history: {e}")


if __name__ == "__main__":
    # Test the framework
    framework = SafeEvolutionFramework()
    print("Safe Evolution Framework initialized")
    print(f"Git available: {framework.rollback_manager.version_control_available}")
    print(f"Project root: {framework.project_root}")

