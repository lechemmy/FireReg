from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
import json
import csv
from datetime import timedelta

from .models import RFIDTag, EntryExitLog, StaffPresence, Card, APIKey

class ModelTests(TestCase):
    """Tests for the models in the register app."""

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )

    def test_rfid_tag_creation(self):
        """Test creating an RFID tag."""
        tag = RFIDTag.objects.create(
            tag_id='12345',
            user=self.user,
            is_active=True
        )
        self.assertEqual(tag.tag_id, '12345')
        self.assertEqual(tag.user, self.user)
        self.assertTrue(tag.is_active)
        self.assertEqual(str(tag), '12345 - Test User')

    def test_entry_exit_log_creation(self):
        """Test creating an entry/exit log."""
        log = EntryExitLog.objects.create(
            user=self.user,
            event_type='entry',
            timestamp=timezone.now()
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.event_type, 'entry')
        self.assertIn('Test User - Entry at', str(log))

    def test_staff_presence_creation(self):
        """Test creating a staff presence record."""
        presence = StaffPresence.objects.create(
            user=self.user,
            is_present=True,
            last_entry=timezone.now()
        )
        self.assertEqual(presence.user, self.user)
        self.assertTrue(presence.is_present)
        self.assertEqual(str(presence), 'Test User - In')

        # Test changing presence status
        presence.is_present = False
        presence.save()
        self.assertEqual(str(presence), 'Test User - Out')

    def test_card_creation(self):
        """Test creating a card."""
        card = Card.objects.create(
            name='Test Card',
            card_number='54321'
        )
        self.assertEqual(card.name, 'Test Card')
        self.assertEqual(card.card_number, '54321')
        self.assertEqual(str(card), 'Test Card - 54321')

    def test_api_key_creation(self):
        """Test creating an API key."""
        api_key = APIKey.objects.create(
            user=self.user,
            name='Test API Key'
        )
        self.assertEqual(api_key.user, self.user)
        self.assertEqual(api_key.name, 'Test API Key')
        self.assertTrue(api_key.is_active)
        self.assertIsNotNone(api_key.key)  # Key should be auto-generated
        self.assertEqual(len(api_key.key), 32)  # UUID4 hex is 32 chars
        self.assertEqual(str(api_key), 'Test API Key (testuser)')

        # Test masked key
        self.assertEqual(api_key.get_masked_key(), api_key.key[:6] + '...')

class ViewTests(TestCase):
    """Tests for the views in the register app."""

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )

        # Create a superuser
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )

        # Create a Fire Marshal group and user
        self.fire_marshal_group = Group.objects.create(name='Fire Marshal')
        self.fire_marshal = User.objects.create_user(
            username='firemarshal',
            password='marshalpassword',
            first_name='Fire',
            last_name='Marshal'
        )
        self.fire_marshal_group.user_set.add(self.fire_marshal)

        # Create an RFID tag for the test user
        self.tag = RFIDTag.objects.create(
            tag_id='12345',
            user=self.user,
            is_active=True
        )

        # Create a staff presence record for the test user
        self.presence = StaffPresence.objects.create(
            user=self.user,
            is_present=False
        )

        # Create a card
        self.card = Card.objects.create(
            name='Test Card',
            card_number='54321'
        )

        # Create an API key for the admin
        self.api_key = APIKey.objects.create(
            user=self.admin,
            name='Test API Key'
        )

        # Set up the test client
        self.client = Client()

    def test_index_view(self):
        """Test the index view."""
        response = self.client.get(reverse('register:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/index.html')

    def test_current_staff_view(self):
        """Test the current staff view."""
        # Log the user in
        self.presence.is_present = True
        self.presence.last_entry = timezone.now()
        self.presence.save()

        response = self.client.get(reverse('register:current_staff'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/current_staff.html')
        self.assertContains(response, 'Test User')

    def test_event_log_view_requires_login(self):
        """Test that the event log view requires login."""
        response = self.client.get(reverse('register:event_log'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("register:event_log")}')

        # Log in and try again
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('register:event_log'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/event_log.html')

    def test_cards_view_requires_login(self):
        """Test that the cards view requires login."""
        response = self.client.get(reverse('register:cards'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("register:cards")}')

        # Log in and try again
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('register:cards'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/cards.html')
        self.assertContains(response, 'Test Card')

    def test_api_keys_view_requires_login(self):
        """Test that the API keys view requires login."""
        response = self.client.get(reverse('register:api_keys'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("register:api_keys")}')

        # Log in and try again
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('register:api_keys'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/api_keys.html')
        self.assertContains(response, 'Test API Key')

    def test_fire_marshals_view_requires_login(self):
        """Test that the fire marshals view requires login."""
        response = self.client.get(reverse('register:fire_marshals'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("register:fire_marshals")}')

        # Log in and try again
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('register:fire_marshals'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/fire_marshals.html')
        self.assertContains(response, 'firemarshal')

    def test_exit_staff_view(self):
        """Test the exit staff view."""
        # Log the user in
        self.presence.is_present = True
        self.presence.last_entry = timezone.now()
        self.presence.save()

        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Exit the staff member
        response = self.client.post(reverse('register:exit_staff'), {'user_ids[]': [self.user.id]})
        self.assertRedirects(response, reverse('register:current_staff'))

        # Check that the user is now marked as not present
        self.presence.refresh_from_db()
        self.assertFalse(self.presence.is_present)

        # Check that an exit log was created
        self.assertTrue(EntryExitLog.objects.filter(user=self.user, event_type='exit').exists())

    def test_create_api_key_view(self):
        """Test creating an API key."""
        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Create a new API key
        response = self.client.post(reverse('register:create_api_key'), {'name': 'New API Key'})
        self.assertRedirects(response, reverse('register:api_keys'))

        # Check that the API key was created
        self.assertTrue(APIKey.objects.filter(user=self.admin, name='New API Key').exists())

    def test_revoke_api_key_view(self):
        """Test revoking an API key."""
        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Revoke the API key
        response = self.client.post(reverse('register:revoke_api_key', args=[self.api_key.id]))
        self.assertRedirects(response, reverse('register:api_keys'))

        # Check that the API key is now inactive
        self.api_key.refresh_from_db()
        self.assertFalse(self.api_key.is_active)

    def test_fire_marshal_cannot_access_api_keys(self):
        """Test that fire marshals cannot access API keys."""
        # Log in as fire marshal
        self.client.login(username='firemarshal', password='marshalpassword')

        # Try to access API keys
        response = self.client.get(reverse('register:api_keys'))
        self.assertRedirects(response, reverse('register:index'))

    def test_fire_marshal_cannot_access_event_log(self):
        """Test that fire marshals cannot access the event log."""
        # Log in as fire marshal
        self.client.login(username='firemarshal', password='marshalpassword')

        # Try to access event log
        response = self.client.get(reverse('register:event_log'))
        self.assertRedirects(response, reverse('register:index'))

class APITests(TestCase):
    """Tests for the API endpoints in the register app."""

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )

        # Create an RFID tag for the test user
        self.tag = RFIDTag.objects.create(
            tag_id='12345',
            user=self.user,
            is_active=True
        )

        # Create a staff presence record for the test user
        self.presence = StaffPresence.objects.create(
            user=self.user,
            is_present=False
        )

        # Create an API key
        self.api_key = APIKey.objects.create(
            user=self.user,
            name='Test API Key'
        )

        # Set up the test client
        self.client = Client()

    def test_rfid_scan_api_requires_api_key(self):
        """Test that the RFID scan API requires an API key."""
        # Try without an API key
        response = self.client.post(
            reverse('register:rfid_scan'),
            json.dumps({'tag_id': '12345'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'API key is required')

    def test_rfid_scan_api_with_query_param_api_key(self):
        """Test the RFID scan API with an API key as a query parameter."""
        # Try with a valid API key as a query parameter
        response = self.client.post(
            f"{reverse('register:rfid_scan')}?api_key={self.api_key.key}",
            json.dumps({'tag_id': '12345'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['user'], 'Test User')
        self.assertEqual(response.json()['event_type'], 'entry')

        # Check that the user is now marked as present
        self.presence.refresh_from_db()
        self.assertTrue(self.presence.is_present)

        # Check that an entry log was created
        self.assertTrue(EntryExitLog.objects.filter(user=self.user, event_type='entry').exists())

    def test_rfid_scan_api_with_header_api_key(self):
        """Test the RFID scan API with an API key as a header."""
        # Try with a valid API key as a header
        response = self.client.post(
            reverse('register:rfid_scan'),
            json.dumps({'tag_id': '12345', 'event_type': 'exit'}),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['user'], 'Test User')
        self.assertEqual(response.json()['event_type'], 'exit')

        # Check that the user is now marked as not present
        self.presence.refresh_from_db()
        self.assertFalse(self.presence.is_present)

        # Check that an exit log was created
        self.assertTrue(EntryExitLog.objects.filter(user=self.user, event_type='exit').exists())

    def test_rfid_scan_api_with_invalid_api_key(self):
        """Test the RFID scan API with an invalid API key."""
        # Try with an invalid API key
        response = self.client.post(
            f"{reverse('register:rfid_scan')}?api_key=invalid_key",
            json.dumps({'tag_id': '12345'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'Invalid or inactive API key')

    def test_rfid_scan_api_with_invalid_tag(self):
        """Test the RFID scan API with an invalid tag."""
        # Try with an invalid tag
        response = self.client.post(
            f"{reverse('register:rfid_scan')}?api_key={self.api_key.key}",
            json.dumps({'tag_id': 'invalid_tag'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'Invalid or inactive RFID tag')

    def test_rfid_scan_api_with_invalid_event_type(self):
        """Test the RFID scan API with an invalid event type."""
        # Try with an invalid event type
        response = self.client.post(
            f"{reverse('register:rfid_scan')}?api_key={self.api_key.key}",
            json.dumps({'tag_id': '12345', 'event_type': 'invalid'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'Invalid event_type - must be "entry" or "exit" if provided')

    def test_search_staff_api(self):
        """Test the search staff API."""
        # Log the user in
        self.presence.is_present = True
        self.presence.last_entry = timezone.now()
        self.presence.save()

        # Log in as the test user
        self.client.login(username='testuser', password='testpassword')

        # Search for staff
        response = self.client.get(f"{reverse('register:search_staff')}?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['staff']), 1)
        self.assertEqual(response.json()['staff'][0]['name'], 'Test User')

    def test_search_cards_api(self):
        """Test the search cards API."""
        # Create a card
        card = Card.objects.create(
            name='Test Card',
            card_number='54321'
        )

        # Log in as the test user
        self.client.login(username='testuser', password='testpassword')

        # Search for cards
        response = self.client.get(f"{reverse('register:search_cards')}?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['cards']), 1)
        self.assertEqual(response.json()['cards'][0]['name'], 'Test Card')
        self.assertEqual(response.json()['cards'][0]['card_number'], '54321')

class ManagementCommandTests(TestCase):
    """Tests for the management commands in the register app."""

    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpassword',
            first_name='Test',
            last_name='User1'
        )

        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword',
            first_name='Test',
            last_name='User2'
        )

        # Create staff presence records
        self.presence1 = StaffPresence.objects.create(
            user=self.user1,
            is_present=True,
            last_entry=timezone.now() - timedelta(hours=1)
        )

        self.presence2 = StaffPresence.objects.create(
            user=self.user2,
            is_present=True,
            last_entry=timezone.now() - timedelta(hours=2)
        )

    def test_exit_all_cards_command(self):
        """Test the exit_all_cards management command."""
        # Capture command output
        out = StringIO()
        call_command('exit_all_cards', stdout=out)

        # Check command output
        self.assertIn('Successfully logged out 2 staff member(s)', out.getvalue())

        # Check that all users are now marked as not present
        self.presence1.refresh_from_db()
        self.presence2.refresh_from_db()
        self.assertFalse(self.presence1.is_present)
        self.assertFalse(self.presence2.is_present)

        # Check that exit logs were created
        self.assertTrue(EntryExitLog.objects.filter(user=self.user1, event_type='exit').exists())
        self.assertTrue(EntryExitLog.objects.filter(user=self.user2, event_type='exit').exists())

    def test_exit_all_cards_command_no_staff_present(self):
        """Test the exit_all_cards management command when no staff are present."""
        # Mark all staff as not present
        self.presence1.is_present = False
        self.presence1.save()
        self.presence2.is_present = False
        self.presence2.save()

        # Capture command output
        out = StringIO()
        call_command('exit_all_cards', stdout=out)

        # Check command output
        self.assertIn('No staff members were logged out', out.getvalue())

class FormTests(TestCase):
    """Tests for the forms in the register app."""

    def setUp(self):
        # Create a superuser
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )

        # Create a Fire Marshal group
        self.fire_marshal_group = Group.objects.create(name='Fire Marshal')

        # Set up the test client
        self.client = Client()

    def test_card_form(self):
        """Test the card form."""
        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Create a card
        card = Card.objects.create(
            name='Test Card',
            card_number='54321'
        )

        # Edit the card
        response = self.client.post(
            reverse('register:edit_card', args=[card.id]),
            {'name': 'Updated Card', 'card_number': '12345'}
        )
        self.assertRedirects(response, reverse('register:cards'))

        # Check that the card was updated
        card.refresh_from_db()
        self.assertEqual(card.name, 'Updated Card')
        self.assertEqual(card.card_number, '12345')

    def test_fire_marshal_form_create(self):
        """Test creating a fire marshal."""
        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Create a fire marshal
        response = self.client.post(
            reverse('register:add_fire_marshal'),
            {
                'username': 'newmarshal',
                'first_name': 'New',
                'last_name': 'Marshal',
                'email': 'new@example.com',
                'is_active': True,
                'password1': 'newpassword',
                'password2': 'newpassword'
            }
        )
        self.assertRedirects(response, reverse('register:fire_marshals'))

        # Check that the fire marshal was created
        user = User.objects.get(username='newmarshal')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Marshal')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.groups.filter(name='Fire Marshal').exists())

    def test_fire_marshal_form_edit(self):
        """Test editing a fire marshal."""
        # Create a fire marshal
        marshal = User.objects.create_user(
            username='firemarshal',
            password='marshalpassword',
            first_name='Fire',
            last_name='Marshal',
            email='fire@example.com'
        )
        self.fire_marshal_group.user_set.add(marshal)

        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Edit the fire marshal
        response = self.client.post(
            reverse('register:edit_fire_marshal', args=[marshal.id]),
            {
                'username': 'firemarshal',
                'first_name': 'Updated',
                'last_name': 'Marshal',
                'email': 'updated@example.com',
                'is_active': True
            }
        )
        self.assertRedirects(response, reverse('register:fire_marshals'))

        # Check that the fire marshal was updated
        marshal.refresh_from_db()
        self.assertEqual(marshal.first_name, 'Updated')
        self.assertEqual(marshal.last_name, 'Marshal')
        self.assertEqual(marshal.email, 'updated@example.com')

    def test_fire_marshal_form_password_mismatch(self):
        """Test fire marshal form with mismatched passwords."""
        # Log in as admin
        self.client.login(username='admin', password='adminpassword')

        # Try to create a fire marshal with mismatched passwords
        response = self.client.post(
            reverse('register:add_fire_marshal'),
            {
                'username': 'newmarshal',
                'first_name': 'New',
                'last_name': 'Marshal',
                'email': 'new@example.com',
                'is_active': True,
                'password1': 'password1',
                'password2': 'password2'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords don&#x27;t match")

        # Check that the fire marshal was not created
        self.assertFalse(User.objects.filter(username='newmarshal').exists())
