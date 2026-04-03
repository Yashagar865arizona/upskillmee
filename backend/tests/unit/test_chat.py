import requests
import json
from backend.app.config import settings

def test_chat():
    # Verify API key is loaded
    if not settings.OPENAI_API_KEY:
        print("\n❌ Error: OPENAI_API_KEY not found in environment variables")
        return
        
    # API endpoint for chat
    base_url = "http://localhost:8000"
    chat_endpoint = f"{base_url}/api/v1/chat/chat"
    
    # Message to send
    message = "Hello, can you help me learn Python programming?"
    
    # Prepare the request
    headers = {"Content-Type": "application/json"}
    payload = {
        "message": message,
        "user_id": "test_user"
    }
    
    # Send request and get response
    print("\n=== Testing Chat API ===")
    print(f"Sending message: {message}")
    
    try:
        response = requests.post(chat_endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            print(f"Response: {result['response']['text']}")
        else:
            print(f"\n❌ Error: Status code {response.status_code}")
            print(response.json())
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {str(e)}")
        
if __name__ == "__main__":
    test_chat()