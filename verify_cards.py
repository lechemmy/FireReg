import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FireReg.settings')
django.setup()

from register.models import Card

# Count the total number of cards
total_cards = Card.objects.count()
print(f"Total cards in the database: {total_cards}")

# List all cards
print("\nAll cards:")
for card in Card.objects.all().order_by('name'):
    print(f"- {card.name}: {card.card_number}")

print("\nVerification complete!")