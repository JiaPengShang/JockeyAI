"""
OCR Configuration Manager for saving and loading engine configurations
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from config import ocr_config
from ocr_engines import engine_manager


@dataclass
class OCRExperimentConfig:
    """Configuration for OCR ablation experiments"""
    name: str
    description: str
    active_engines: List[str]
    enable_preprocessing: bool
    combine_results: bool
    target_accuracy: float
    created_at: str
    experiment_id: str


class OCRConfigManager:
    """Manager for OCR experiment configurations"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "ocr_experiments.json")
        self.experiments = self._load_experiments()
    
    def _load_experiments(self) -> Dict[str, OCRExperimentConfig]:
        """Load saved experiments from file"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                experiments = {}
                for exp_id, exp_data in data.items():
                    experiments[exp_id] = OCRExperimentConfig(**exp_data)
                return experiments
        except Exception as e:
            print(f"Error loading experiments: {e}")
            return {}
    
    def _save_experiments(self):
        """Save experiments to file"""
        try:
            data = {}
            for exp_id, experiment in self.experiments.items():
                data[exp_id] = asdict(experiment)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving experiments: {e}")
    
    def create_experiment(self, name: str, description: str, 
                         active_engines: List[str], **kwargs) -> str:
        """Create a new experiment configuration"""
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        experiment = OCRExperimentConfig(
            name=name,
            description=description,
            active_engines=active_engines,
            enable_preprocessing=kwargs.get('enable_preprocessing', ocr_config.enable_preprocessing),
            combine_results=kwargs.get('combine_results', ocr_config.combine_results),
            target_accuracy=kwargs.get('target_accuracy', ocr_config.target_accuracy),
            created_at=datetime.now().isoformat(),
            experiment_id=experiment_id
        )
        
        self.experiments[experiment_id] = experiment
        self._save_experiments()
        
        return experiment_id
    
    def load_experiment(self, experiment_id: str) -> bool:
        """Load an experiment configuration"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        
        # Apply configuration
        engine_manager.set_active_engines(experiment.active_engines)
        ocr_config.enable_preprocessing = experiment.enable_preprocessing
        ocr_config.combine_results = experiment.combine_results
        ocr_config.target_accuracy = experiment.target_accuracy
        
        return True
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment configuration"""
        if experiment_id in self.experiments:
            del self.experiments[experiment_id]
            self._save_experiments()
            return True
        return False
    
    def get_experiment(self, experiment_id: str) -> Optional[OCRExperimentConfig]:
        """Get experiment configuration by ID"""
        return self.experiments.get(experiment_id)
    
    def list_experiments(self) -> List[Dict]:
        """List all experiments"""
        experiments = []
        for exp_id, experiment in self.experiments.items():
            experiments.append({
                'id': exp_id,
                'name': experiment.name,
                'description': experiment.description,
                'active_engines': experiment.active_engines,
                'created_at': experiment.created_at
            })
        return experiments
    
    def save_current_config(self, name: str, description: str) -> str:
        """Save current configuration as an experiment"""
        current_engines = engine_manager.get_active_engines()
        
        return self.create_experiment(
            name=name,
            description=description,
            active_engines=current_engines,
            enable_preprocessing=ocr_config.enable_preprocessing,
            combine_results=ocr_config.combine_results,
            target_accuracy=ocr_config.target_accuracy
        )
    
    def get_preset_configs(self) -> Dict[str, Dict]:
        """Get preset configurations for common ablation studies"""
        return {
            'tesseract_only': {
                'name': 'TesseractOCR Only',
                'description': 'Ablation study using only TesseractOCR engine',
                'active_engines': ['tesseract'],
                'enable_preprocessing': True,
                'combine_results': False
            },
            'paddle_only': {
                'name': 'PaddleOCR Only',
                'description': 'Ablation study using only PaddleOCR engine',
                'active_engines': ['paddle'],
                'enable_preprocessing': True,
                'combine_results': False
            },
            'both_engines': {
                'name': 'Both Engines',
                'description': 'Using both TesseractOCR and PaddleOCR engines',
                'active_engines': ['tesseract', 'paddle'],
                'enable_preprocessing': True,
                'combine_results': True
            },
            'no_preprocessing': {
                'name': 'No Preprocessing',
                'description': 'Both engines without image preprocessing',
                'active_engines': ['tesseract', 'paddle'],
                'enable_preprocessing': False,
                'combine_results': True
            }
        }


# Global config manager instance
config_manager = OCRConfigManager()
