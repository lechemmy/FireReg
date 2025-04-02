import requests
import json

# API endpoint URL
API_URL = 'http://localhost:8000/api/rfid-scan/'

# Test RFID tag ID
TAG_ID = 'TEST123456'

def test_without_api_key():
    """Test the API endpoint without providing an API key (should fail)"""
    payload = {
        'tag_id': TAG_ID
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print("\n--- Testing API without API key ---")
        response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("Test PASSED: API correctly requires authentication")
        else:
            print("Test FAILED: API did not require authentication")
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("\nMake sure the Django development server is running with:")
        print("python manage.py runserver")

if __name__ == "__main__":
    print("=== API Authentication Test ===")
    print("This script tests that the API requires an API key for authentication.")
    print("Make sure the Django development server is running.")
    
    test_without_api_key()