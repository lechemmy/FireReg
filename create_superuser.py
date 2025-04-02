from django.contrib.auth.models import User
from django.db import IntegrityError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    superuser = User.objects.create_superuser(
        username=os.getenv('SUPERUSER_USERNAME'),
        email=os.getenv('SUPERUSER_EMAIL'),
        password=os.getenv('SUPERUSER_PASSWORD')
    )
    print(f"Superuser '{superuser.username}' created successfully!")
except IntegrityError:
    print("Superuser already exists.")
