"""
Simple health check service for basic system monitoring.
"""

from typing import Dict
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
from datetime import datetime, timezone
from ..config import settings

logger = logging.getLogger(__name__)

class HealthService:
    async def check_health(self, db: Session) -> Dict:
        """Basic health check of critical system components."""
        try:
            results = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "components": {}
            }
            
            # Check database
            try:
                db.execute(text("SELECT 1"))
                results["components"]["database"] = {"status": "healthy"}
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                results["components"]["database"] = {"status": "unhealthy"}
                results["status"] = "unhealthy"
            
            # Check OpenAI API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                    )
                if response.status_code == 200:
                    results["components"]["openai"] = {"status": "healthy"}
                else:
                    results["components"]["openai"] = {"status": "unhealthy"}
                    results["status"] = "unhealthy"
            except Exception as e:
                logger.error(f"OpenAI health check failed: {e}")
                results["components"]["openai"] = {"status": "unhealthy"}
                results["status"] = "unhealthy"
                
            return results
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
