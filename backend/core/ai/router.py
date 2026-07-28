import logging
from typing import Dict, Any

logger = logging.getLogger("backend.ai.router")


class ModelRoutingEngine:
    """Routes validation tasks to specific models based on reasoning complexity requirements."""

    def __init__(self):
        # Configure model routing defaults
        self.routes: Dict[str, Dict[str, Any]] = {
            "classification": {
                "model": "llama3-8b-8192",
                "temperature": 0.0,
                "max_tokens": 128
            },
            "static_validation": {
                "model": "llama3-8b-8192",
                "temperature": 0.1,
                "max_tokens": 1024
            },
            "complex_fix": {
                "model": "llama-3.1-70b-versatile",  # Route complex repairs to larger models if supported
                "temperature": 0.2,
                "max_tokens": 2048
            }
        }

    def route_task(self, task_type: str) -> Dict[str, Any]:
        route = self.routes.get(task_type.lower(), self.routes["static_validation"])
        logger.info(f"Routed task '{task_type}' to model '{route['model']}' (temp={route['temperature']})")
        return route
