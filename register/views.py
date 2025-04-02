from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django import forms
from .models import RFIDTag, EntryExitLog, StaffPresence, Card, APIKey
import json
import csv
import io

# Custom forms for Fire Marshal management
class FireMarshalForm(forms.ModelForm):
    """Form for creating and editing Fire Marshals."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            # Ensure user is in Fire Marshal group
            fire_marshal_group, _ = Group.objects.get_or_create(name='Fire Marshal')
            fire_marshal_group.user_set.add(user)
        return user

@csrf_exempt
@require_POST
def rfid_scan(request):
    """
    API endpoint for RFID tag readers to register entry/exit events.
    Requires an API key for authentication, which can be provided as:
    - A query parameter: ?api_key=your_api_key
    - A header: X-API-Key: your_api_key

    Expects a JSON payload with:
    {
        "tag_id": "the_rfid_tag_id",
        "event_type": "entry" or "exit" (optional - if not provided, will toggle based on current status)
    }
    """
    # Check for API key
    api_key = request.GET.get('api_key') or request.headers.get('X-API-Key')

    if not api_key:
        return JsonResponse({'status': 'error', 'message': 'API key is required'}, status=401)

    # Validate API key
    try:
        api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
        # Update last used timestamp
        api_key_obj.last_used = timezone.now()
        api_key_obj.save()
    except APIKey.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid or inactive API key'}, status=401)

    try:
        data = json.loads(request.body)
        tag_id = data.get('tag_id')
        event_type = data.get('event_type')

        if not tag_id:
            return JsonResponse({'status': 'error', 'message': 'Invalid request data - tag_id is required'}, status=400)

        if event_type is not None and event_type not in ['entry', 'exit']:
            return JsonResponse({'status': 'error', 'message': 'Invalid event_type - must be "entry" or "exit" if provided'}, status=400)

        # Find the RFID tag
        try:
            rfid_tag = RFIDTag.objects.get(tag_id=tag_id, is_active=True)
            user = rfid_tag.user
        except RFIDTag.DoesNotExist:
            # Check if this is a card that was imported but not yet used
            try:
                card = Card.objects.get(card_number=tag_id)
                # Create a user for this card if needed
                username = card.name.lower().replace(' ', '_')
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': card.name,
                        'is_active': True
                    }
                )

                # Create an RFID tag for this user
                rfid_tag = RFIDTag.objects.create(
                    user=user,
                    tag_id=card.card_number,
                    is_active=True
                )
            except Card.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid or inactive RFID tag'}, status=404)

        with transaction.atomic():
            # Update or create staff presence
            presence, created = StaffPresence.objects.get_or_create(user=user)

            # If event_type is not provided, determine it based on current presence status
            if event_type is None:
                event_type = 'exit' if presence.is_present else 'entry'

            # Log the entry/exit event
            log = EntryExitLog.objects.create(
                user=user,
                event_type=event_type,
                timestamp=timezone.now()
            )

            # Update presence status
            if event_type == 'entry':
                presence.is_present = True
                presence.last_entry = log.timestamp
            else:  # exit
                presence.is_present = False
                presence.last_exit = log.timestamp

            presence.save()

        return JsonResponse({
            'status': 'success',
            'user': user.get_full_name() or user.username,
            'event_type': event_type,
            'timestamp': log.timestamp.isoformat()
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def current_staff(request):
    """View to display staff currently in the building."""
    present_staff = StaffPresence.objects.filter(is_present=True).select_related('user')

    return render(request, 'register/current_staff.html', {
        'present_staff': present_staff,
    })

@login_required
@require_POST
def exit_staff(request):
    """View to handle logging selected staff out of the building."""
    user_ids = request.POST.getlist('user_ids[]')

    if not user_ids:
        messages.warning(request, 'No staff members were selected.')
        return redirect('register:current_staff')

    exit_count = 0
    current_time = timezone.now()

    for user_id in user_ids:
        try:
            # Get the staff presence record
            presence = StaffPresence.objects.get(user_id=user_id, is_present=True)

            # Create an exit log
            EntryExitLog.objects.create(
                user_id=user_id,
                event_type='exit',
                timestamp=current_time
            )

            # Update the presence record
            presence.is_present = False
            presence.last_exit = current_time
            presence.save()

            exit_count += 1
        except StaffPresence.DoesNotExist:
            # Skip if the staff member is not present or doesn't exist
            continue

    if exit_count > 0:
        messages.success(request, f'Successfully logged out {exit_count} staff member(s).')
    else:
        messages.warning(request, 'No staff members were logged out. They may have already left the building.')

    return redirect('register:current_staff')

@login_required
def event_log(request):
    """View to display logs of entry/exit events."""
    # Check if user is a Fire Marshal
    if request.user.groups.filter(name='Fire Marshal').exists():
        messages.error(request, 'Fire Marshals do not have access to the Event Log.')
        return redirect('register:index')

    logs = EntryExitLog.objects.all().select_related('user')[:100]  # Limit to last 100 events

    return render(request, 'register/event_log.html', {
        'logs': logs,
    })

def index(request):
    """Home page view."""
    return render(request, 'register/index.html')

@login_required
def cards(request):
    """View to display all registered cards."""
    all_cards = Card.objects.all().order_by('name')

    return render(request, 'register/cards.html', {
        'cards': all_cards,
    })

@login_required
def api_keys(request):
    """View to display and manage API keys for the current user."""
    # Check if user is a Fire Marshal
    if request.user.groups.filter(name='Fire Marshal').exists():
        messages.error(request, 'Fire Marshals do not have access to API Keys.')
        return redirect('register:index')

    user_api_keys = APIKey.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'register/api_keys.html', {
        'api_keys': user_api_keys,
    })

@login_required
@require_POST
def create_api_key(request):
    """View to create a new API key for the current user."""
    # Check if user is a Fire Marshal
    if request.user.groups.filter(name='Fire Marshal').exists():
        messages.error(request, 'Fire Marshals do not have access to API Keys.')
        return redirect('register:index')

    name = request.POST.get('name', '').strip()

    if not name:
        messages.error(request, 'API key name is required.')
        return redirect('register:api_keys')

    # Create a new API key
    api_key = APIKey.objects.create(
        user=request.user,
        name=name
    )

    messages.success(request, f'API key "{name}" created successfully. Make sure to copy your key now as it won\'t be shown again: {api_key.key}')
    return redirect('register:api_keys')

@login_required
@require_POST
def revoke_api_key(request, key_id):
    """View to revoke (deactivate) an API key."""
    # Check if user is a Fire Marshal
    if request.user.groups.filter(name='Fire Marshal').exists():
        messages.error(request, 'Fire Marshals do not have access to API Keys.')
        return redirect('register:index')

    try:
        api_key = APIKey.objects.get(id=key_id, user=request.user)
        api_key.is_active = False
        api_key.save()
        messages.success(request, f'API key "{api_key.name}" has been revoked.')
    except APIKey.DoesNotExist:
        messages.error(request, 'API key not found or you do not have permission to revoke it.')

    return redirect('register:api_keys')

@login_required
@require_POST
def log_cards_in_office(request):
    """View to handle logging selected cards as in the office."""
    card_ids = request.POST.getlist('card_ids[]')

    if not card_ids:
        messages.warning(request, 'No cards were selected.')
        return redirect('register:cards')

    success_count = 0
    current_time = timezone.now()

    for card_id in card_ids:
        try:
            # Get the card
            card = Card.objects.get(id=card_id)

            # Find or create a user with the card's name
            username = card.name.lower().replace(' ', '_')
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': card.name,
                    'is_active': True
                }
            )

            # Find or create an RFID tag for the user with the card's number
            rfid_tag, tag_created = RFIDTag.objects.get_or_create(
                user=user,
                defaults={
                    'tag_id': card.card_number,
                    'is_active': True
                }
            )

            # If the tag exists but has a different ID, update it
            if not tag_created and rfid_tag.tag_id != card.card_number:
                rfid_tag.tag_id = card.card_number
                rfid_tag.save()

            with transaction.atomic():
                # Update or create staff presence
                presence, presence_created = StaffPresence.objects.get_or_create(user=user)

                # Only log entry if not already present
                if not presence.is_present:
                    # Log the entry event
                    log = EntryExitLog.objects.create(
                        user=user,
                        event_type='entry',
                        timestamp=current_time
                    )

                    # Update presence status
                    presence.is_present = True
                    presence.last_entry = current_time
                    presence.save()

                    success_count += 1

        except Card.DoesNotExist:
            # Skip if the card doesn't exist
            continue
        except Exception as e:
            # Log the error but continue processing other cards
            print(f"Error processing card {card_id}: {str(e)}")
            continue

    if success_count > 0:
        messages.success(request, f'Successfully logged {success_count} card(s) as in the office.')
    else:
        messages.warning(request, 'No cards were logged as in the office. They may already be logged in.')

    return redirect('register:cards')

@login_required
def export_cards(request):
    """View to export all cards to a CSV file."""
    # Get all cards ordered by name
    all_cards = Card.objects.all().order_by('name')

    # Create a CSV file in memory
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write header row
    writer.writerow(['Name', 'Card Number'])

    # Write data rows
    for card in all_cards:
        writer.writerow([card.name, card.card_number])

    # Create the HTTP response with CSV content
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cards.csv"'

    return response

@login_required
@require_POST
def import_cards(request):
    """View to import cards from a CSV file, ignoring duplicates."""
    if 'csv_file' not in request.FILES:
        messages.error(request, 'No CSV file was uploaded.')
        return redirect('register:cards')

    csv_file = request.FILES['csv_file']

    # Check if it's a CSV file
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'File is not a CSV file.')
        return redirect('register:cards')

    # Process the CSV file
    try:
        # Decode the file
        file_data = csv_file.read().decode('utf-8')
        csv_data = csv.reader(io.StringIO(file_data))

        # Skip header row if it exists
        header = next(csv_data, None)

        # Count successes and duplicates
        success_count = 0
        duplicate_count = 0

        # Process each row
        for row in csv_data:
            # Skip empty rows
            if not row or len(row) < 2:
                continue

            name = row[0].strip()
            card_number = row[1].strip()

            # Skip rows with empty name or card number
            if not name or not card_number:
                continue

            # Check if card number already exists
            if Card.objects.filter(card_number=card_number).exists():
                duplicate_count += 1
                continue

            # Create the new card
            Card.objects.create(
                name=name,
                card_number=card_number
            )
            success_count += 1

        # Set appropriate messages
        if success_count > 0:
            messages.success(request, f'Successfully imported {success_count} card(s).')
        if duplicate_count > 0:
            messages.warning(request, f'Skipped {duplicate_count} duplicate card(s).')
        if success_count == 0 and duplicate_count == 0:
            messages.warning(request, 'No cards were imported. The CSV file may be empty or incorrectly formatted.')

    except Exception as e:
        messages.error(request, f'Error processing CSV file: {str(e)}')

    return redirect('register:cards')

@login_required
@require_POST
def register_cards(request):
    """View to handle registration of new cards."""
    names = request.POST.getlist('name[]')
    card_numbers = request.POST.getlist('card_number[]')

    # Ensure we have the same number of names and card numbers
    if len(names) != len(card_numbers):
        messages.error(request, 'Invalid form submission. Please try again.')
        return redirect('register:cards')

    # Count how many cards were successfully registered
    success_count = 0
    error_count = 0

    # Process each name/card number pair
    for i in range(len(names)):
        name = names[i].strip()
        card_number = card_numbers[i].strip()

        # Skip empty entries
        if not name or not card_number:
            continue

        try:
            # Check if card number already exists
            if Card.objects.filter(card_number=card_number).exists():
                error_count += 1
                continue

            # Create the new card
            Card.objects.create(
                name=name,
                card_number=card_number
            )
            success_count += 1
        except Exception:
            error_count += 1

    # Set appropriate messages
    if success_count > 0:
        messages.success(request, f'Successfully registered {success_count} card(s).')
    if error_count > 0:
        messages.warning(request, f'Failed to register {error_count} card(s). Card numbers must be unique.')

    return redirect('register:cards')

@login_required
def fire_marshals(request):
    """View to display and manage Fire Marshals."""
    # Ensure Fire Marshal group exists
    fire_marshal_group, created = Group.objects.get_or_create(name='Fire Marshal')

    # Get all users in the Fire Marshal group
    fire_marshals = User.objects.filter(groups=fire_marshal_group).order_by('username')

    return render(request, 'register/fire_marshals.html', {
        'fire_marshals': fire_marshals,
    })

@login_required
def add_fire_marshal(request):
    """View to add a new Fire Marshal."""
    if request.method == 'POST':
        form = FireMarshalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fire Marshal added successfully.')
            return redirect('register:fire_marshals')
    else:
        form = FireMarshalForm()

    return render(request, 'register/fire_marshal_form.html', {
        'form': form,
        'title': 'Add Fire Marshal',
    })

@login_required
def edit_fire_marshal(request, user_id):
    """View to edit an existing Fire Marshal."""
    user = get_object_or_404(User, id=user_id)

    # Ensure user is a Fire Marshal
    fire_marshal_group = Group.objects.get(name='Fire Marshal')
    if not user.groups.filter(id=fire_marshal_group.id).exists():
        messages.error(request, 'User is not a Fire Marshal.')
        return redirect('register:fire_marshals')

    if request.method == 'POST':
        form = FireMarshalForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fire Marshal updated successfully.')
            return redirect('register:fire_marshals')
    else:
        form = FireMarshalForm(instance=user)

    return render(request, 'register/fire_marshal_form.html', {
        'form': form,
        'title': 'Edit Fire Marshal',
        'user': user,
    })

@login_required
@require_POST
def delete_fire_marshal(request, user_id):
    """View to remove a user from the Fire Marshal group."""
    user = get_object_or_404(User, id=user_id)

    # Remove user from Fire Marshal group
    fire_marshal_group = Group.objects.get(name='Fire Marshal')
    fire_marshal_group.user_set.remove(user)

    messages.success(request, f'{user.username} removed from Fire Marshals.')
    return redirect('register:fire_marshals')
