#!/usr/bin/env python3
"""
LocalAI Manager - Docker Desktop Integration
Manages LocalAI container and model operations
"""

import os
import subprocess
import json
import time
import logging
from typing import Dict, Any, Optional, List
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalAIManager:
    """
    Manages LocalAI Docker container and model operations
    """
    
    def __init__(self, endpoint: str = "http://localhost:8080"):
        self.endpoint = endpoint
        self.container_name = "local-ai"
        self.docker_available = self._check_docker()
        self.container_running = False
    
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def is_docker_running(self) -> bool:
        """Check if Docker daemon is running"""
        if not self.docker_available:
            return False
        
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def is_container_running(self) -> bool:
        """Check if LocalAI container is running"""
        if not self.docker_available:
            return False
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return self.container_name in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def start_localai(self, gpu: bool = False) -> Dict[str, Any]:
        """
        Start LocalAI container
        
        Args:
            gpu: Whether to use GPU (NVIDIA CUDA)
        
        Returns:
            Dict with status and message
        """
        if not self.docker_available:
            return {
                'success': False,
                'message': 'Docker is not available. Please install Docker Desktop.',
                'error': 'docker_not_available'
            }
        
        if not self.is_docker_running():
            return {
                'success': False,
                'message': 'Docker daemon is not running. Please start Docker Desktop.',
                'error': 'docker_not_running'
            }
        
        if self.is_container_running():
            return {
                'success': True,
                'message': 'LocalAI container is already running.',
                'container_running': True
            }
        
        try:
            # Determine which image to use
            if gpu:
                # Check for NVIDIA GPU
                nvidia_check = subprocess.run(
                    ["docker", "run", "--rm", "--gpus", "all", "nvidia/cuda:12.0.0-base-ubuntu22.04", "nvidia-smi"],
                    capture_output=True,
                    timeout=10
                )
                if nvidia_check.returncode == 0:
                    image = "localai/localai:latest-gpu-nvidia-cuda-12"
                    gpu_args = ["--gpus", "all"]
                else:
                    # Fallback to CPU
                    image = "localai/localai:latest"
                    gpu_args = []
            else:
                image = "localai/localai:latest"
                gpu_args = []
            
            # Start container
            cmd = [
                "docker", "run", "-d",
                "--name", self.container_name,
                "-p", "8080:8080"
            ] + gpu_args + [image]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Wait for container to be ready
                time.sleep(5)
                if self.is_container_running():
                    return {
                        'success': True,
                        'message': 'LocalAI container started successfully.',
                        'container_id': result.stdout.strip(),
                        'endpoint': self.endpoint
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Container started but is not running. Check Docker logs.',
                        'error': 'container_not_ready'
                    }
            else:
                # Try to start existing container
                start_result = subprocess.run(
                    ["docker", "start", self.container_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if start_result.returncode == 0:
                    time.sleep(5)
                    return {
                        'success': True,
                        'message': 'LocalAI container started (was stopped).',
                        'endpoint': self.endpoint
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Failed to start LocalAI: {result.stderr}',
                        'error': 'start_failed'
                    }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Docker command timed out. Please check Docker Desktop.',
                'error': 'timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error starting LocalAI: {str(e)}',
                'error': str(e)
            }
    
    def stop_localai(self) -> Dict[str, Any]:
        """Stop LocalAI container"""
        if not self.docker_available:
            return {
                'success': False,
                'message': 'Docker is not available.'
            }
        
        try:
            result = subprocess.run(
                ["docker", "stop", self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'LocalAI container stopped successfully.'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to stop container: {result.stderr}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error stopping LocalAI: {str(e)}'
            }
    
    def check_localai_health(self) -> Dict[str, Any]:
        """Check if LocalAI API is responding"""
        try:
            response = requests.get(f"{self.endpoint}/healthz", timeout=5)
            if response.status_code == 200:
                return {
                    'success': True,
                    'healthy': True,
                    'message': 'LocalAI is healthy and responding.'
                }
            else:
                return {
                    'success': False,
                    'healthy': False,
                    'message': f'LocalAI returned status {response.status_code}'
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'healthy': False,
                'message': f'Cannot connect to LocalAI: {str(e)}'
            }
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models in LocalAI"""
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        models = self.list_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return None
    
    def ensure_running(self) -> bool:
        """
        Ensure LocalAI is running, start if necessary
        
        Returns:
            True if LocalAI is running, False otherwise
        """
        if self.is_container_running():
            # Check health
            health = self.check_localai_health()
            if health.get('healthy'):
                return True
        
        # Try to start
        result = self.start_localai()
        if result.get('success'):
            # Wait a bit and check health
            time.sleep(10)
            health = self.check_localai_health()
            return health.get('healthy', False)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of LocalAI"""
        docker_available = self.docker_available
        docker_running = self.is_docker_running() if docker_available else False
        container_running = self.is_container_running() if docker_running else False
        health = self.check_localai_health() if container_running else {'healthy': False}
        
        return {
            'docker_available': docker_available,
            'docker_running': docker_running,
            'container_running': container_running,
            'api_healthy': health.get('healthy', False),
            'endpoint': self.endpoint,
            'message': health.get('message', 'LocalAI not running')
        }


# Global instance
_localai_manager = None

def get_localai_manager(endpoint: str = None) -> LocalAIManager:
    """Get or create LocalAI manager instance"""
    global _localai_manager
    if _localai_manager is None:
        _localai_manager = LocalAIManager(endpoint=endpoint or os.getenv('LOCALAI_ENDPOINT', 'http://localhost:8080'))
    return _localai_manager

