#!/usr/bin/env python3
"""
FAME AGI Core - Production Entry Point
Main AGI loop with real-time processing and autonomous operation
"""

import asyncio
import yaml
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.agi_core import AGICore
from utils.logger import AGILogger
from utils.monitoring import SystemMonitor


class FAMEAGI:
    """Production AGI runtime with continuous operation"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.logger = AGILogger(self.config)
        self.monitor = SystemMonitor()
        self.core = AGICore(self.config)
        
        # Add alert callback
        self.monitor.add_alert_callback(self.handle_alert)
        
        self.running = False
    
    def load_config(self, path: str) -> dict:
        """Load configuration from YAML file"""
        config_path = Path(path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                "system": {"name": "FAME AGI", "mode": "autonomous"},
                "logging": {"level": "INFO", "log_dir": "./logs"},
                "models": {"primary_llm": "gpt-4o-mini"},
                "execution": {"dual_core": True},
                "spiders": {"enabled": True},
                "api": {"host": "0.0.0.0", "port": 8080}
            }
    
    def handle_alert(self, alert_data: dict):
        """Handle system alerts"""
        self.logger.warning(f"System Alert: {alert_data['type']}", extra=alert_data)
    
    async def run_continuous(self):
        """Main AGI loop with real-time processing"""
        self.running = True
        self.logger.info("FAME AGI Core Online - System Nominal")
        
        while self.running:
            try:
                # Process real-time inputs
                user_input = await self.get_next_input()
                
                if user_input:
                    result = await self.core.run(user_input)
                    await self.handle_output(result)
                
                # Autonomous background processing
                await self.core.run_autonomous_cycle()
                
                # System health check
                await self.monitor.check_health()
                
                await asyncio.sleep(0.1)  # 10Hz processing loop
                
            except KeyboardInterrupt:
                self.logger.info("Shutdown requested by user")
                break
            except Exception as e:
                self.logger.error(f"AGI loop error: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        # Graceful shutdown
        await self.shutdown()
    
    async def get_next_input(self) -> Optional[str]:
        """Get input from multiple sources (user, APIs, sensors)"""
        # For now, return None (no interactive input)
        # In production, this would poll from:
        # - User interface
        # - API endpoints
        # - Message queues
        # - Sensor inputs
        # - Scheduled tasks
        return None
    
    async def handle_output(self, result: dict):
        """Handle AGI outputs (responses, actions, alerts)"""
        # In production, this would:
        # - Send to user interface
        # - Trigger actions
        # - Send notifications
        # - Log to database
        self.logger.info(f"AGI Output: {result.get('response', '')[:100]}...")
    
    async def autonomous_cycle(self):
        """Background autonomous processing"""
        # Continuous learning, market analysis, strategy updates
        await self.core.run_autonomous_cycle()
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("FAME AGI Core shutting down...")
        self.running = False
        await self.core.shutdown()
        self.logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    agi = FAMEAGI()
    try:
        await agi.run_continuous()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await agi.shutdown()


if __name__ == "__main__":
    # Check if running as service or interactive
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        # Run as FastAPI service
        from api.fastapi_app import app, cfg
        import uvicorn
        api_config = cfg.get("api", {})
        uvicorn.run(
            app,
            host=api_config.get("host", "0.0.0.0"),
            port=api_config.get("port", 8080),
            log_level="info"
        )
    else:
        # Run as continuous AGI loop
        asyncio.run(main())

