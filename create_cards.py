import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FireReg.settings')
django.setup()

from register.models import Card
from django.db import IntegrityError

# List of cards to create
cards_data = [
    {"name": "Test Card", "card_number": "19-132-38-3"},
    {"name": "Jane", "card_number": "33-16-32-62"},
    {"name": "Maxine", "card_number": "3-106-44-3"},
    {"name": "Chris", "card_number": "34-232-220-79"},
    {"name": "Tina", "card_number": "12-184-31-62"},
    {"name": "Dhanu", "card_number": "105-95-31-62"},
    {"name": "Jenelle", "card_number": "252-152-35-62"},
    {"name": "Kiana", "card_number": "143-28-28-62"},
    {"name": "Sophie", "card_number": "217-140-176-131"},
    {"name": "Kim", "card_number": "253-14-1-3"},
    {"name": "Heather", "card_number": "115-193-118-111"},
    {"name": "Kayleigh", "card_number": "112-189-109-111"},
    {"name": "Toyah", "card_number": "113-185-106-111"},
]

# Create cards
for card_data in cards_data:
    try:
        card = Card.objects.create(
            name=card_data["name"],
            card_number=card_data["card_number"]
        )
        print(f"Card '{card.name}' with number '{card.card_number}' created successfully!")
    except IntegrityError:
        card = Card.objects.get(card_number=card_data["card_number"])
        print(f"Using existing card '{card.name}' with number '{card.card_number}'")

print("\nCards created successfully!")
