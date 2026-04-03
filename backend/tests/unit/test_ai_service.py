"""
Simple test script to verify the AI integration service changes.
"""

from app.services.ai_integration_service import AIIntegrationService
from app.monitoring.metrics import ai_metrics

def test_ai_service_init():
    """Test that the AI service initializes correctly."""
    service = AIIntegrationService()
    print("AIIntegrationService initialized successfully")
    
    # Check that the DeepSeek client is initialized if the API key is available
    if service.deepseek_client:
        print("DeepSeek client initialized")
    else:
        print("DeepSeek client not initialized (API key may be missing)")
    
    # Check that the OpenAI client is initialized
    if service.openai_client:
        print("OpenAI client initialized")
    else:
        print("OpenAI client not initialized (API key may be missing)")
    
    return service

if __name__ == "__main__":
    print("Testing AI Integration Service...")
    service = test_ai_service_init()
    print("Test completed successfully")
