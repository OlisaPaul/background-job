# Django Background Job Processing System with Celery, Channels, and DRF

A production-ready background job processing system built with Django, Celery, Django REST Framework, and Django Channels. This project provides a web interface and RESTful API for managing, monitoring, and executing various background jobs asynchronously, with real-time job status updates via WebSocket.

## Features

- **Web Interface**: Django Admin for job management
- **RESTful API**: Create, list, retry, and monitor jobs via API
- **Multiple Job Types**: Email sending, file upload to S3 (with temp file handling)
- **Real-time Monitoring**: Live job status updates via WebSocket (Django Channels)
- **Retry Logic**: Automatic retry with exponential backoff for failed jobs
- **Priority Queues**: Job prioritization system
- **Database Persistence**: SQLite by default (easy to switch to PostgreSQL)
- **Scheduling**: Immediate and one-off scheduled jobs
- **Extensible**: Easily add new job types and logic
- **React Frontend Ready**: Real-time job status updates can be consumed by a React frontend (optional)

## Available Job Types

- `send_email` - Send email notifications
- `upload_file` - Upload a file to S3 (background, with temp file cleanup)

## Project Structure

```
background-job-processing-system/
├── job_system/                # Django project settings and celery config
│   ├── __init__.py
│   ├── celery.py              # Celery app instance
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   └── wsgi.py
├── jobs/                      # App for job management
│   ├── admin.py
│   ├── apps.py
│   ├── models.py              # Job model
│   ├── serializers.py         # DRF serializers
│   ├── tasks.py               # Celery tasks
│   ├── urls.py                # API routes
│   └── views.py               # API views
├── manage.py
├── requirements.txt           # Python dependencies
└── db.sqlite3                 # SQLite database (default)
```

## Quick Start

1. **Clone the repository and navigate to the project directory**
2. **Create and activate a virtual environment**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Apply migrations**
   ```powershell
   python manage.py migrate
   ```
5. **Create a superuser**
   ```powershell
   python manage.py createsuperuser
   ```
6. **Start the Django development server**
   ```powershell
   python manage.py runserver
   ```
7. **Start a Redis server** (required for Celery broker and Channels)
   - **Redis 5.0 or higher is required!**
   - On Windows, use WSL, Docker, or a third-party Redis 5+ build. Example with Docker:
     ```powershell
     docker run -d -p 6379:6379 --name redis6 redis:6
     ```
   - Verify your Redis version:
     ```powershell
     redis-server --version
     ```
   - If you see errors about `BZPOPMIN`, your Redis version is too old.
8. **Start the Celery worker**
   ```powershell
   .venv\Scripts\celery -A job_system worker -l info -P solo
   ```
   - The `-P solo` flag is required for Celery on Windows.
9. **Start the Django Channels ASGI server** (for WebSocket support)
   ```powershell
   daphne -b 127.0.0.1 -p 9000 job_system.asgi:application
   ```
   - Or use `python manage.py runserver` for development (Channels will work if configured).
10. **Copy the example environment file and update with your secrets**
    ```powershell
    copy .env.example .env
    # Then edit .env with your own credentials
    ```

## Real-time Job Status Updates (WebSocket)

- The backend uses Django Channels and Redis to broadcast job status updates.
- A sample HTML/JS frontend is provided to connect to `/ws/jobs/status/` and display updates.
- You can build a React frontend to consume these updates for a modern UI.

## Troubleshooting

### Redis BZPOPMIN Error
If you see an error like:
```
redis.exceptions.ResponseError: unknown command 'BZPOPMIN'
```
Your Redis server is too old. Upgrade to Redis 5.0 or higher (see above for Windows instructions).

## API Endpoints

- `POST /api/jobs/` - Create a new job
- `GET /api/jobs/` - List jobs (with optional filtering)
- `GET /api/jobs/{id}/` - Get specific job details
- `DELETE /api/jobs/{id}/` - Delete a job
- `POST /api/jobs/{id}/retry/` - Retry a failed job
- `GET /api/jobs/stats/` - Get job statistics
- `GET /api/jobs/types/` - Get available job types
- `POST /api/jobs/upload-file/` - Upload a file to S3

## Example Usage

### Creating a Job via API

```python
import requests

job_data = {
    "job_type": "send_email",
    "parameters": {
        "recipient": "user@example.com",
        "subject": "Welcome!",
        "body": "Welcome to our service!"
    },
    "priority": 5,
    "max_retries": 3
}

response = requests.post("http://localhost:8000/api/jobs/", json=job_data)
print(response.json())
```

### Creating a Job via Django Admin

1. Go to `http://localhost:8000/admin/`
2. Log in with your superuser credentials
3. Add or manage jobs from the Jobs section

### Example File Upload via API (Python)

```python
import requests

with open('myfile.txt', 'rb') as f:
    files = {'file': f}
    data = {}  # file_name is not required
    response = requests.post('http://localhost:8000/api/jobs/upload-file/', files=files, data=data)
    print(response.json())
```

## Configuration

- **Celery Broker**: Uses Redis (`redis://localhost:6379/0`)
- **Channels Layer**: Uses Redis (same instance, port 6379)
- **Result Backend**: Uses Django DB (`django-db`)
- **Database**: SQLite by default (change in `settings.py` for PostgreSQL)
- **Job Types**: Defined in `jobs/models.py` as `JOB_TYPE_CHOICES`
- **API**: Powered by Django REST Framework

## File Uploads (S3)

- To upload a file to S3, use the endpoint:
  - `POST /api/jobs/upload-file/`
  - Use the DRF web UI or a tool like Postman.
  - Fields:
    - `file`: The file to upload (max 10 MB)
    - `priority`: (optional) Job priority
    - `max_retries`: (optional) Max retries
  - The file name is automatically taken from the uploaded file.
- The file is saved temporarily to disk, then uploaded to S3 in the background by Celery. The file is not stored in the database.
- The job result will include a `file_url` with a direct link to the uploaded file.

## Scheduling Jobs

Jobs can be scheduled in two ways using the `schedule_type` field:

- `immediate`: The job is executed as soon as it is created. Do not provide `scheduled_time`.
- `scheduled`: The job is executed at a specific future date and time. You must provide a `scheduled_time` (in ISO 8601 format, e.g., `2025-07-01T12:00:00Z`).

**Example JSON for immediate job:**

```json
{
  "job_type": "send_email",
  "parameters": { ... },
  "schedule_type": "immediate"
}
```

**Example JSON for scheduled job:**

```json
{
  "job_type": "send_email",
  "parameters": { ... },
  "schedule_type": "scheduled",
  "scheduled_time": "2025-07-01T12:00:00Z"
}
```

- For file uploads, use the `/api/jobs/upload-file/` endpoint with the same `schedule_type` logic.
- Recurring jobs (hourly, daily, etc.) are not supported in this version.

## Environment Variables

All sensitive settings are loaded from a `.env` file. See `.env.example` for required variables:

- `DJANGO_SECRET_KEY` - Django secret key
- `DJANGO_DEBUG` - Set to `True` or `False`
- `DJANGO_ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `EMAIL_HOST` - SMTP server
- `EMAIL_PORT` - SMTP port
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password
- `EMAIL_USE_TLS` - `True` or `False`
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `AWS_STORAGE_BUCKET_NAME` - Your S3 bucket name
- `AWS_REGION` - Your S3 region (default: us-east-1)

**Never commit your real `.env` file to version control!**

## Testing

- Use Django Admin or API endpoints to create and monitor jobs
- Start both Django server and Celery worker for full functionality
- Check job status and results via API or admin

## Running Tests

Unit tests are provided for all major job scheduling and file upload features. To run the tests:

```bash
python manage.py test jobs
```

The tests cover:

- Immediate and scheduled job creation (email and file upload)
- Validation for required and future `scheduled_time`
- File size validation for uploads

Test file location: `jobs/test_jobs.py`, `jobs/test_integration.py`

## Integration Tests

Integration tests are provided to verify the end-to-end behavior of job creation, file uploads, and Celery task triggering. These tests use Django's test client and mock Celery tasks to ensure correct system integration without running real background jobs.

To run all tests (unit and integration):

```bash
python manage.py test jobs
```

Integration test file location: `jobs/test_integration.py`

The integration tests cover:

- Creating jobs via the API and verifying database persistence
- Immediate job creation triggers Celery (mocked)
- Immediate file upload creates both the file and the job, and triggers Celery (mocked)
- Scheduled jobs do not trigger Celery immediately

## Dependencies

- Django
- Celery
- django-celery-results
- django-celery-beat
- djangorestframework
- channels
- channels_redis
- redis (for broker and Channels)
- boto3 (for S3 upload)
- drf-yasg (for API docs)
- psycopg2-binary (if using PostgreSQL)

## License

This project is provided as an educational example for background job processing in Django.
