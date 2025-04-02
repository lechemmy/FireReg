from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class RFIDTag(models.Model):
    """Model representing an RFID tag assigned to a staff member."""
    tag_id = models.CharField(max_length=100, unique=True, help_text="Unique ID of the RFID tag")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rfid_tag')
    is_active = models.BooleanField(default=True, help_text="Whether this tag is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tag_id} - {self.user.get_full_name() or self.user.username}"

class EntryExitLog(models.Model):
    """Model for logging entry and exit events."""
    EVENT_TYPES = (
        ('entry', 'Entry'),
        ('exit', 'Exit'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=5, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_event_type_display()} at {self.timestamp}"

class StaffPresence(models.Model):
    """Model to track whether a staff member is currently in the building."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    is_present = models.BooleanField(default=False)
    last_entry = models.DateTimeField(null=True, blank=True)
    last_exit = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "In" if self.is_present else "Out"
        return f"{self.user.get_full_name() or self.user.username} - {status}"

class Card(models.Model):
    """Model representing a card with a name and card number."""
    name = models.CharField(max_length=100, help_text="Name associated with the card")
    card_number = models.CharField(max_length=100, unique=True, help_text="Unique card number")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.card_number}"

class APIKey(models.Model):
    """Model representing an API key for authentication."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, help_text="Name to identify this API key")
    key = models.CharField(max_length=64, unique=True, help_text="The API key value")
    is_active = models.BooleanField(default=True, help_text="Whether this API key is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate a unique API key if one doesn't exist
        if not self.key:
            self.key = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
