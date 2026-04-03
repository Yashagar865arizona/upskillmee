from typing import Dict, List, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self):
        self.current_model = "gpt-4"  # Default model
        self.available_models = {
            "gpt-4": {
                "provider": "openai",
                "description": "GPT-4 by OpenAI",
                "api_key_env": "OPENAI_API_KEY"
            },
            "deepseek": {
                "provider": "deepseek",
                "description": "Deepseek for learning plan generation",
                "api_key_env": "DEEPSEEK_API_KEY"
            }
        }

    def get_available_models(self) -> List[Dict]:
        """Get list of available models"""
        return [
            {
                "id": model_id,
                "provider": info["provider"],
                "description": info["description"],
                "is_active": model_id == self.current_model
            }
            for model_id, info in self.available_models.items()
        ]

    def get_current_model(self) -> str:
        """Get currently active model"""
        return self.current_model

    def switch_model(self, model_id: str) -> bool:
        """Switch to a different model"""
        if model_id not in self.available_models:
            return False
        self.current_model = model_id
        return True

    def get_model_api_key(self, model_id: Optional[str] = None) -> Optional[str]:
        """Get API key for specified model"""
        model = model_id or self.current_model
        if model not in self.available_models:
            return None
        env_var = self.available_models[model]["api_key_env"]
        return getattr(settings, env_var, None) 