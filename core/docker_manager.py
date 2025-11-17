import docker
import os
import subprocess
import psutil
import time
import hashlib
from pathlib import Path
from typing import Dict, Any
import logging

class DockerManager:
    def __init__(self):
        self.client = None
        self.connection_status = "disconnected"
        
    def connect_to_docker(self):
        """Connect to Docker with multiple fallback methods"""
        connection_methods = [
            self._connect_via_npipe,      # Windows default
            self._connect_via_tcp,        # Docker TCP
            self._connect_via_socket,     # Linux/Mac
            self._start_docker_desktop    # Last resort - start Docker
        ]
        
        for method in connection_methods:
            try:
                logging.info(f"Trying connection method: {method.__name__}")
                if method():
                    self.connection_status = "connected"
                    logging.info("✅ Docker connection established!")
                    return True
            except Exception as e:
                logging.warning(f"Connection method failed: {e}")
                continue
        
        logging.error("❌ All Docker connection methods failed")
        return False
    
    def _connect_via_npipe(self):
        """Connect via Windows named pipe"""
        try:
            self.client = docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
            self.client.ping()
            return True
        except:
            return False
    
    def _connect_via_tcp(self):
        """Connect via TCP (Docker might be on different port)"""
        try:
            self.client = docker.DockerClient(base_url='tcp://localhost:2375')
            self.client.ping()
            return True
        except:
            return False
    
    def _connect_via_socket(self):
        """Connect via Unix socket (Linux/Mac)"""
        try:
            self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            self.client.ping()
            return True
        except:
            return False
    
    def _start_docker_desktop(self):
        """Attempt to start Docker Desktop"""
        try:
            # Windows Docker Desktop paths
            docker_paths = [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                r"C:\Program Files\Docker\Docker\resources\com.docker.docker.exe",
                os.path.expanduser(r"~\AppData\Local\Docker\Docker Desktop.exe")
            ]
            
            for path in docker_paths:
                if os.path.exists(path):
                    subprocess.Popen([path], shell=True)
                    logging.info("🔄 Starting Docker Desktop...")
                    time.sleep(15)  # Wait for Docker to start
                    
                    # Try connecting again
                    return self._connect_via_npipe()
            
            return False
        except Exception as e:
            logging.error(f"Failed to start Docker: {e}")
            return False
    
    def is_docker_running(self):
        """Check if Docker is running"""
        try:
            if self.client:
                self.client.ping()
                return True
            return False
        except:
            return False
    
    def start_localai_container(self):
        """Start LocalAI container automatically"""
        try:
            # Check if container already exists
            try:
                container = self.client.containers.get('local-ai')
                if container.status != 'running':
                    container.start()
                    logging.info("🔄 Starting existing LocalAI container...")
            except:
                # Create new container
                logging.info("🐳 Pulling and starting LocalAI container...")
                container = self.client.containers.run(
                    'localai/localai:latest-aio-cpu',
                    name='local-ai',
                    ports={'8080/tcp': 8080},
                    detach=True,
                    restart_policy={"Name": "always"}
                )
            
            # Wait for container to be ready
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                container.reload()
                if container.status == 'running':
                    # Test if API is responsive
                    import requests
                    try:
                        response = requests.get('http://localhost:8080/ready', timeout=5)
                        if response.status_code == 200:
                            logging.info("✅ LocalAI is ready!")
                            return True
                    except:
                        continue
            
            logging.error("❌ LocalAI container started but API not responding")
            return False
            
        except Exception as e:
            logging.error(f"Failed to start LocalAI: {e}")
            return False
    
    def run_code_in_container(self, code: str, timeout: int = 30, allow_network: bool = False, 
                              cpu_limit: float = 0.5, memory_limit: int = 512) -> Dict[str, Any]:
        """
        Run code in isolated sandbox container with strict limits
        Returns test report with stdout, stderr, success flag, and metrics
        """
        if not self.client:
            if not self.connect_to_docker():
                return {
                    'success': False,
                    'error': 'Docker not available',
                    'stdout': '',
                    'stderr': 'Docker connection failed',
                    'exit_code': -1,
                    'execution_time': 0
                }
        
        try:
            import tempfile
            import uuid
            
            # Create temporary file with code
            code_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
            container_name = f"fame-sandbox-{code_hash}"
            
            # Prepare Docker run command with limits
            docker_cmd = [
                'docker', 'run',
                '--rm',
                f'--name={container_name}',
                f'--cpus={cpu_limit}',
                f'--memory={memory_limit}m',
                f'--network={"none" if not allow_network else "bridge"}',
                '--workdir=/code',
                '-v', f'{tempfile.gettempdir()}:/code',
                'python:3.11-slim',
                'python', '-c', code
            ]
            
            # Execute with timeout
            import subprocess
            import time
            
            start_time = time.time()
            try:
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )
                execution_time = time.time() - start_time
                
                return {
                    'success': result.returncode == 0,
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'execution_time': execution_time,
                    'timeout': False
                }
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return {
                    'success': False,
                    'error': 'Execution timeout',
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': f'Code execution exceeded {timeout}s timeout',
                    'execution_time': execution_time,
                    'timeout': True
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Sandbox execution error: {e}',
                'execution_time': 0
            }
    
    def cleanup_sandbox_containers(self):
        """Clean up any leftover sandbox containers"""
        if not self.client:
            return
        
        try:
            containers = self.client.containers.list(all=True, filters={'name': 'fame-sandbox'})
            for container in containers:
                try:
                    container.remove(force=True)
                except:
                    pass
        except:
            pass

