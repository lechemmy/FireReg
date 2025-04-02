from django.contrib.auth.models import User
from register.models import RFIDTag, StaffPresence
from django.db import IntegrityError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a test user
try:
    test_user = User.objects.create_user(
        username=os.getenv('TEST_USER_USERNAME'),
        email=os.getenv('TEST_USER_EMAIL'),
        password=os.getenv('TEST_USER_PASSWORD'),
        first_name='Test',
        last_name='User'
    )
    print(f"Test user '{test_user.username}' created successfully!")
except IntegrityError:
    test_user = User.objects.get(username=os.getenv('TEST_USER_USERNAME'))
    print(f"Using existing test user '{test_user.username}'")

# Create an RFID tag for the test user
try:
    rfid_tag = RFIDTag.objects.create(
        tag_id='TEST123456',
        user=test_user,
        is_active=True
    )
    print(f"RFID tag '{rfid_tag.tag_id}' created for user '{test_user.username}'")
except IntegrityError:
    rfid_tag = RFIDTag.objects.get(user=test_user)
    print(f"Using existing RFID tag '{rfid_tag.tag_id}' for user '{test_user.username}'")

# Create a staff presence record for the test user
try:
    presence, created = StaffPresence.objects.get_or_create(user=test_user)
    if created:
        print(f"Staff presence record created for user '{test_user.username}'")
    else:
        print(f"Using existing staff presence record for user '{test_user.username}'")
except Exception as e:
    print(f"Error creating staff presence record: {e}")

print("\nTest data created successfully!")
print(f"You can now use the RFID tag ID '{rfid_tag.tag_id}' for testing the API.")
