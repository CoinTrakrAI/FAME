"""
Model Manager for F.A.M.E Training
Handles model loading, saving, and updates
"""

import json
from pathlib import Path
from typing import Dict, Optional

class ModelManager:
    """Manages AI model lifecycle"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
    def save_model_info(self, model_name: str, info: Dict):
        """Save model metadata"""
        info_file = self.models_dir / f"{model_name}_info.json"
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
    
    def load_model_info(self, model_name: str) -> Optional[Dict]:
        """Load model metadata"""
        info_file = self.models_dir / f"{model_name}_info.json"
        if info_file.exists():
            with open(info_file, 'r') as f:
                return json.load(f)
        return None
    
    def list_models(self) -> list:
        """List all available models"""
        models = []
        for info_file in self.models_dir.glob("*_info.json"):
            model_name = info_file.stem.replace("_info", "")
            models.append(model_name)
        return models

