# Background Job Processing System

A comprehensive, production-ready background job processing system built with Python and Flask.

## Features

- **Web Interface**: Modern, responsive dashboard for job management
- **Multiple Job Types**: Email sending, image processing, report generation, data fetching, and more
- **Real-time Monitoring**: Live job statistics and progress tracking
- **Retry Logic**: Automatic retry with exponential backoff for failed jobs
- **Priority Queues**: Job prioritization system (1-10 scale)
- **RESTful API**: Complete API for programmatic job management
- **Database Persistence**: SQLite database for job state and history
- **Multi-threaded Processing**: Concurrent job execution with configurable worker count

## Quick Start

1. **Navigate to the project directory:**
   ```bash
   cd background_job_system
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Start the application:**
   ```bash
   python src/main.py
   ```

4. **Access the web interface:**
   Open your browser and go to `http://localhost:5000`

## Available Job Types

1. **send_email** - Send email notifications
2. **process_image** - Process images with various operations
3. **generate_report** - Generate various types of reports
4. **backup_database** - Backup databases with different options
5. **fetch_data** - Fetch data from external APIs
6. **batch_process** - Process large datasets in batches
7. **send_notification** - Send notifications to multiple recipients
8. **cleanup_files** - Clean up old files from directories

## API Endpoints

- `POST /api/jobs` - Create a new job
- `GET /api/jobs` - List jobs (with optional filtering)
- `GET /api/jobs/<id>` - Get specific job details
- `DELETE /api/jobs/<id>` - Delete a job
- `POST /api/jobs/<id>/retry` - Retry a failed job
- `GET /api/jobs/stats` - Get job statistics
- `GET /api/jobs/types` - Get available job types
- `POST /api/jobs/bulk` - Create multiple jobs at once

## Example Usage

### Creating a Job via API

```python
import requests

# Create an email job
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

response = requests.post("http://localhost:5000/api/jobs", json=job_data)
print(response.json())
```

### Creating a Job via Web Interface

1. Open the web interface at `http://localhost:5000`
2. Select a job type from the dropdown
3. Fill in the required parameters
4. Set priority and retry options
5. Click "Create Job"

## Project Structure

```
background_job_system/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── models/
│   │   └── job.py             # Job database model
│   ├── routes/
│   │   └── jobs.py            # API routes for job management
│   ├── background/
│   │   ├── job_processor.py   # Background job processor
│   │   └── job_tasks.py       # Job task implementations
│   ├── static/
│   │   └── index.html         # Web interface
│   └── database/
│       └── app.db             # SQLite database
├── venv/                      # Virtual environment
└── requirements.txt           # Python dependencies
```

## Configuration

The system can be configured by modifying the following in `src/main.py`:

- **Worker Count**: Change `max_workers` in JobProcessor initialization
- **Poll Interval**: Adjust `poll_interval` for job polling frequency
- **Database**: Replace SQLite with PostgreSQL/MySQL for production
- **Secret Key**: Change the Flask secret key for security

## Production Deployment

For production use, consider:

1. **Database**: Use PostgreSQL or MySQL instead of SQLite
2. **Message Broker**: Implement Redis or RabbitMQ for better scalability
3. **WSGI Server**: Use Gunicorn or uWSGI instead of Flask dev server
4. **Monitoring**: Add logging, metrics, and alerting
5. **Security**: Implement authentication and authorization
6. **Load Balancing**: Use multiple worker instances behind a load balancer

## Dependencies

- Flask - Web framework
- Flask-SQLAlchemy - Database ORM
- Flask-CORS - Cross-origin resource sharing
- Requests - HTTP library for external API calls

## License

This project is provided as an educational example for background job processing in Python.

