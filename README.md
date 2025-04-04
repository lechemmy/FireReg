# Fire Register

A web application for tracking staff entering and exiting a building using RFID tags. The system logs entry and exit events and provides a real-time view of who is currently in the building.

## Features

- Track staff entering and exiting the building using RFID tags
- View a list of staff currently in the building
- View logs of entry and exit events
- API endpoint for RFID tag readers to register entry/exit events
- Automatic exit of all cards at 23:00 daily
- Dark and light theme support

## Requirements

- Python 3.8+
- Django 5.1+
- Raspberry Pi Pico with RFID reader (for production use)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd FireReg
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a .env file in the project root directory:
   ```
   # Create a .env file
   touch .env
   ```

   Add the following environment variables to the .env file:
   ```
   # Django Secret Key
   SECRET_KEY=your-secret-key-here

   # Superuser credentials
   SUPERUSER_USERNAME=admin
   SUPERUSER_EMAIL=admin@example.com
   SUPERUSER_PASSWORD=your-secure-password

   # Test user credentials
   TEST_USER_USERNAME=testuser
   TEST_USER_EMAIL=test@example.com
   TEST_USER_PASSWORD=your-test-password

   # API key placeholder (replace with your actual API key)
   API_KEY=your-api-key-here
   ```

5. Apply migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

## Running the Application

### Option 1: Running Locally

1. Start the development server:
   ```
   python manage.py runserver
   ```

2. Access the application in your web browser:
   - Home page: http://localhost:8000/
   - Admin site: http://localhost:8000/admin/
   - Current staff: http://localhost:8000/current/
   - Event logs: http://localhost:8000/logs/

### Option 2: Running with Docker

1. Make sure you have Docker and Docker Compose installed on your system.

2. Build and start the Docker containers:
   ```
   docker-compose up --build
   ```

3. Access the application in your web browser:
   - Home page: http://localhost:8000/
   - Admin site: http://localhost:8000/admin/
   - Current staff: http://localhost:8000/current/
   - Event logs: http://localhost:8000/logs/

4. To run the application in the background:
   ```
   docker-compose up -d
   ```

5. To stop the application:
   ```
   docker-compose down
   ```

## API Usage

The system provides an API endpoint for RFID tag readers to register entry and exit events. API keys are required for authentication.

### API Keys

API keys are used to secure the API endpoints. You can manage your API keys through the web interface:

1. Log in to the application
2. Navigate to the "API Keys" page from the navigation menu
3. Create a new API key with a descriptive name
4. Copy and securely store your API key (it will only be shown once)

### RFID Scan Endpoint

- Endpoint: `/api/rfid-scan/`
- Method: POST
- Authentication: API key (required)
  - As a query parameter: `?api_key=YOUR_API_KEY`
  - Or as a header: `X-API-Key: YOUR_API_KEY`
- Content-Type: application/json
- Payload:
  ```json
  {
    "tag_id": "RFID_TAG_ID",
    "event_type": "entry" or "exit" (optional)
  }
  ```

If the `event_type` is not provided, the system will automatically determine whether it's an entry or exit event based on the user's current presence status:
- If the user is not currently in the building, it will register as an entry event.
- If the user is currently in the building, it will register as an exit event.

### Example URL

```
http://your-server-address/api/rfid-scan/?api_key=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Example with Python (for Raspberry Pi Pico):

```python
import urequests
import json

def register_event(tag_id, event_type=None, api_key=None):
    # Include API key in the URL if provided
    if api_key:
        url = f"http://your-server-address/api/rfid-scan/?api_key={api_key}"
    else:
        url = "http://your-server-address/api/rfid-scan/"

    payload = {
        "tag_id": tag_id
    }

    # Only include event_type in payload if it's provided
    if event_type is not None:
        payload["event_type"] = event_type

    headers = {
        "Content-Type": "application/json"
    }

    # Alternatively, you can include the API key in the headers
    if api_key and not "api_key" in url:
        headers["X-API-Key"] = api_key

    response = urequests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

# Example usage:
# With API key (required):
# register_event("TAG123", api_key="your-api-key-here")
# 
# To specify event type:
# register_event("TAG123", event_type="entry", api_key="your-api-key-here")
# 
# To let the system auto-detect event type:
# register_event("TAG123", api_key="your-api-key-here")
```

## Automatic Card Exit

The system includes a feature to automatically exit all cards at 23:00 (11:00 PM) every day. This ensures that all staff members are properly logged out at the end of the day, even if they forget to manually log out.

### How It Works

The automatic exit feature is implemented as a Django management command that can be scheduled to run at 23:00 daily using a cron job or similar scheduler.

### Manual Execution

To manually exit all cards that are currently logged in:

```
python manage.py exit_all_cards
```

### Scheduling

To schedule the command to run automatically at 23:00 daily, set up a cron job:

1. Open your crontab file:
   ```
   crontab -e
   ```

2. Add the following line to schedule the command to run at 23:00 daily:
   ```
   0 23 * * * cd /path/to/your/project && /path/to/your/python /path/to/your/project/manage.py exit_all_cards
   ```

   Replace `/path/to/your/project` with the actual path to your Django project, and `/path/to/your/python` with the path to your Python executable.

For more detailed instructions, see the README.md file in the `register/management/commands/` directory.

## Testing

A test script is provided to simulate RFID tag scans:

```
python test_api.py
```

Before running the test script:
1. Make sure the development server is running
2. Create an API key in the web interface at http://localhost:8000/api-keys/
3. Update the API_KEY in the .env file with your actual API key

The test script will simulate entry and exit events using the API with your API key.

## Admin Interface

The admin interface allows you to:

1. Manage users
2. Assign RFID tags to users
3. View and manage entry/exit logs
4. View staff presence records

Access the admin interface at http://localhost:8000/admin/ using the superuser credentials.

## Theme Support

The application supports both light and dark themes. Click the theme toggle button in the navigation bar to switch between themes.

## License

[Your License Information]
