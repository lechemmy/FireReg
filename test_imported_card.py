import requests
import json
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FireReg.settings')
django.setup()

from register.models import Card

# API endpoint URL
API_URL = 'http://localhost:8000/api/rfid-scan/'

# Test card details
TEST_CARD_NAME = 'Test Imported Card'
TEST_CARD_NUMBER = 'IMPORTED123456'

# API key (replace with your actual API key)
API_KEY = 'your-api-key-here'

def create_test_card():
    """Create a test card in the database if it doesn't exist."""
    try:
        card, created = Card.objects.get_or_create(
            card_number=TEST_CARD_NUMBER,
            defaults={'name': TEST_CARD_NAME}
        )
        if created:
            print(f"Created test card: {card}")
        else:
            print(f"Using existing test card: {card}")
        return card
    except Exception as e:
        print(f"Error creating test card: {e}")
        sys.exit(1)

def simulate_scan(card_number, event_type=None, api_key=API_KEY):
    """
    Simulate an RFID tag scan by sending a request to the API.
    If event_type is None, the system will automatically determine whether it's an entry or exit event.
    """
    # Add API key to the URL as a query parameter
    url = f"{API_URL}?api_key={api_key}"

    payload = {
        'tag_id': card_number
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
            return True
        else:
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("\nMake sure the Django development server is running with:")
        print("python manage.py runserver")
        return False

# Instructions
print("=== Imported Card Test ===")
print("This script tests the API with an imported card.")
print("Make sure the Django development server is running with:")
print("python manage.py runserver")
print("\nIMPORTANT: Replace 'your-api-key-here' at the top of this script with a valid API key.")
print("You can create an API key in the web interface at: http://localhost:8000/api-keys/")

# Create the test card
card = create_test_card()

# Test the API with the imported card
print("\nTesting API with imported card...")
success = simulate_scan(card.card_number, 'entry')

if success:
    print("\nTest passed! The API successfully processed the imported card.")
else:
    print("\nTest failed! The API could not process the imported card.")