##Test Onboarding
import requests
from app.config import settings

def test_onboarding():
    base_url = "http://localhost:8000"
    onboarding_endpoint = f"{base_url}/api/v1/onboarding/step"
    headers = {"Content-Type": "application/json"}
    
    # Test Step 1: Career Path
    step1_payload = {
        "user_id": "test_user",
        "step": 1,
        "data": {"career_path": "software_development"}
    }
    
    print("\n=== Testing Onboarding Step 1 ===")
    response = requests.post(onboarding_endpoint, headers=headers, json=step1_payload)
    if response.status_code == 200:
        print("✅ Step 1 Success!")
        print(response.json()["response"])
    
    # Test Step 2: Specific Interests
    step2_payload = {
        "user_id": "test_user",
        "step": 2,
        "data": {"interests": ["web_development", "python_backend"]}
    }
    
    print("\n=== Testing Onboarding Step 2 ===")
    response = requests.post(onboarding_endpoint, headers=headers, json=step2_payload)
    if response.status_code == 200:
        print("✅ Step 2 Success!")
        print(response.json()["response"])
    
    # Test Step 3: Projects
    step3_payload = {
        "user_id": "test_user",
        "step": 3,
        "data": {"projects": ["todo_app", "blog_site"]}
    }
    
    print("\n=== Testing Onboarding Step 3 ===")
    response = requests.post(onboarding_endpoint, headers=headers, json=step3_payload)
    if response.status_code == 200:
        print("✅ Step 3 Success!")
        print(response.json()["response"])

if __name__ == "__main__":
    test_onboarding() 