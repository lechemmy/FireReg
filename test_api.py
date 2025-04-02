import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoint URL
API_URL = 'http://localhost:8000/api/rfid-scan/'

# Test RFID tag ID
TAG_ID = 'TEST123456'

# API key (loaded from .env file)
API_KEY = os.getenv('API_KEY')

def simulate_scan(tag_id, event_type=None, api_key=API_KEY):
    """
    Simulate an RFID tag scan by sending a request to the API.
    If event_type is None, the system will automatically determine whether it's an entry or exit event.
    """
    # Add API key to the URL as a query parameter
    url = f"{API_URL}?api_key={api_key}"

    payload = {
        'tag_id': tag_id
    }

    # Only include event_type in payload if it's provided
    if event_type is not None:
        payload['event_type'] = event_type

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        event_label = event_type.upper() if event_type else "AUTO-DETECT"
        print(f"\n--- {event_label} EVENT ---")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if event_type is None:
                print(f"Auto-detected event type: {data.get('event_type', 'unknown')}")
        else:
            print(f"Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("\nMake sure the Django development server is running with:")
        print("python manage.py runserver")

# Instructions
print("=== RFID Tag Scan Simulator ===")
print("This script simulates RFID tag scans for entry and exit events.")
print("Make sure the Django development server is running with:")
print("python manage.py runserver")
print("\nIMPORTANT: Update the API_KEY in the .env file with a valid API key.")
print("You can create an API key in the web interface at: http://localhost:8000/api-keys/")
print("\nPress Ctrl+C to exit at any time.")

try:
    # Simulate entry event
    print("\nSimulating entry event...")
    simulate_scan(TAG_ID, 'entry')

    # Wait for 5 seconds
    print("\nWaiting for 5 seconds...")
    time.sleep(5)

    # Simulate exit event
    print("\nSimulating exit event...")
    simulate_scan(TAG_ID, 'exit')

    # Wait for 5 seconds
    print("\nWaiting for 5 seconds...")
    time.sleep(5)

    # Simulate auto-detect event (should be entry since user is now out)
    print("\nSimulating auto-detect event (should be entry)...")
    simulate_scan(TAG_ID)

    # Wait for 5 seconds
    print("\nWaiting for 5 seconds...")
    time.sleep(5)

    # Simulate another auto-detect event (should be exit since user is now in)
    print("\nSimulating auto-detect event (should be exit)...")
    simulate_scan(TAG_ID)

    print("\nTest completed successfully!")

except KeyboardInterrupt:
    print("\nTest interrupted by user.")
