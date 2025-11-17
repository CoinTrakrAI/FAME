#!/usr/bin/env python3
"""
Safety Controller - Enforces safety policies and gates dangerous operations
"""

from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
import json
from pathlib import Path
from datetime import datetime


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyController:
    """Controls access to dangerous capabilities and enforces safety policies"""
    
    def __init__(self, policy_file: Optional[Path] = None):
        self.policy_file = policy_file or Path("safety_policy.json")
        self.policies = self._load_policies()
        self.audit_log: List[Dict] = []
        self.safety_enabled = True
        self.admin_keys: List[str] = []
        
        # Dangerous capabilities that require explicit enablement
        self.restricted_capabilities = {
            'universal_hacker': RiskLevel.CRITICAL,
            'cyber_warfare': RiskLevel.CRITICAL,
            'network_god': RiskLevel.HIGH,
            'physical_god': RiskLevel.CRITICAL,
            'reality_manipulator': RiskLevel.HIGH,
        }
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load safety policies from file"""
        if self.policy_file.exists():
            try:
                with open(self.policy_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default policies
        return {
            'code_generation': {
                'require_sandbox': True,
                'max_execution_time': 30,
                'require_human_approval': False
            },
            'network_access': {
                'allowed': False,
                'whitelist': [],
                'require_approval': True
            },
            'file_system': {
                'read_allowed': True,
                'write_allowed': False,
                'require_approval': True
            },
            'dangerous_capabilities': {
                'enabled': False,
                'require_admin_key': True
            }
        }
    
    def check_permission(self, capability: str, operation: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Check if an operation is allowed
        Returns: (allowed, reason)
        """
        if not self.safety_enabled:
            return True, "Safety disabled"
        
        context = context or {}
        
        # Check if capability is restricted
        if capability in self.restricted_capabilities:
            risk = self.restricted_capabilities[capability]
            
            # Check if dangerous capabilities are enabled
            if not self.policies.get('dangerous_capabilities', {}).get('enabled', False):
                self._audit_log('BLOCKED', capability, operation, risk.value, "Dangerous capability disabled")
                return False, f"{capability} is a {risk.value} risk capability and is disabled"
            
            # Check for admin key if required
            if self.policies.get('dangerous_capabilities', {}).get('require_admin_key', True):
                provided_key = context.get('admin_key', context.get('api_key'))
                if not provided_key or provided_key not in self.admin_keys:
                    self._audit_log('BLOCKED', capability, operation, risk.value, "Missing admin key")
                    return False, f"{capability} requires admin key"
        
        # Check network access
        if operation in ['network_request', 'connect', 'download']:
            network_policy = self.policies.get('network_access', {})
            if not network_policy.get('allowed', False):
                return False, "Network access not allowed by policy"
        
        # Check file system writes
        if operation in ['write_file', 'delete_file', 'modify_file']:
            fs_policy = self.policies.get('file_system', {})
            if not fs_policy.get('write_allowed', False):
                return False, "File system writes not allowed by policy"
        
        # All checks passed
        self._audit_log('ALLOWED', capability, operation, 'low', "Permission granted")
        return True, "Permission granted"
    
    def _audit_log(self, decision: str, capability: str, operation: str, risk: str, reason: str):
        """Log safety decision"""
        entry = {
            'decision': decision,
            'capability': capability,
            'operation': operation,
            'risk_level': risk,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        self.audit_log.append(entry)
        
        # Keep log size manageable
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
    
    def enable_capability(self, capability: str, admin_key: str) -> bool:
        """Enable a restricted capability with admin key"""
        if admin_key not in self.admin_keys:
            return False
        
        if capability in self.restricted_capabilities:
            if 'enabled_capabilities' not in self.policies:
                self.policies['enabled_capabilities'] = []
            
            if capability not in self.policies['enabled_capabilities']:
                self.policies['enabled_capabilities'].append(capability)
                self._save_policies()
                return True
        
        return False
    
    def disable_capability(self, capability: str):
        """Disable a capability"""
        if 'enabled_capabilities' in self.policies:
            if capability in self.policies['enabled_capabilities']:
                self.policies['enabled_capabilities'].remove(capability)
                self._save_policies()
    
    def _save_policies(self):
        """Save policies to file"""
        try:
            with open(self.policy_file, 'w') as f:
                json.dump(self.policies, f, indent=2)
        except Exception as e:
            print(f"[SafetyController] ⚠️ Failed to save policies: {e}")
    
    def get_audit_report(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        return self.audit_log[-limit:]

