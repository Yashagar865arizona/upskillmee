"""
Test script to generate a learning plan and verify the format.
Run this script with: python -m backend.test_learning_plan
"""

import asyncio
import json
import logging
import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.message_service import MessageService
from backend.app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_learning_plan():
    """Test generating a learning plan"""
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize message service
        message_service = MessageService(db)
        
        # Create a test message
        test_message = {
            "message": "Can you create a learning plan for web development?",
            "user_id": "test_user",
            "chat_history": [
                {"text": "Hi, I'm interested in learning web development.", "sender": "user"},
                {"text": "That's great! What's your experience level?", "sender": "bot"},
                {"text": "I'm a beginner with some basic HTML knowledge.", "sender": "user"},
                {"text": "How much time can you dedicate to learning?", "sender": "bot"},
                {"text": "I can spend about 10 hours per week.", "sender": "user"}
            ]
        }
        
        # Process the message
        logger.info("Processing test message to generate learning plan")
        response = await message_service.process_message(test_message)
        
        # Log the response
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
        
        # Check if we got a learning plan
        if isinstance(response, dict) and "metadata" in response and "learning_plan" in response.get("metadata", {}):
            learning_plan = response["metadata"]["learning_plan"]
            logger.info(f"Successfully generated learning plan: {json.dumps(learning_plan, indent=2)}")
            
            # Verify the structure
            if "projects" in learning_plan:
                logger.info(f"Learning plan has {len(learning_plan['projects'])} projects")
                for i, project in enumerate(learning_plan["projects"]):
                    logger.info(f"Project {i+1}: {project.get('title', 'No title')}")
                    logger.info(f"  - Tasks: {len(project.get('tasks', []))}")
                    logger.info(f"  - Skills: {len(project.get('skills', []))}")
            else:
                logger.error("Learning plan does not have 'projects' field")
        else:
            logger.error("Failed to generate learning plan")
            logger.info(f"Full response: {json.dumps(response, indent=2)}")
    
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_learning_plan()) 