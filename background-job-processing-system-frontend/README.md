# React Frontend for Django Background Job System

This is a React frontend (Vite + React) for the Django background job processing system.

## Features

- **Dashboard (Home):** Paginated, filterable list of all jobs with real-time status updates via WebSocket. Includes contextual row coloring, SNO, human-friendly job type, and actions (Delete, Retry, Download).
- **Send Email:** Form to send an email (subject, recipient, body, immediate, scheduled, or interval with frequency). Supports interval jobs (daily, weekly, monthly, hourly).
- **Upload File:** Form to upload a file (immediate or scheduled).
- **Job Details:** View all job info, download file (if available), and delete job. Download uses a secure endpoint and returns user to previous page after download starts.
- **Job Stats Chart:** Pie chart of job statuses, updates in real time.
- **Responsive UI:** Modern, mobile-friendly design using React Bootstrap and react-icons for navigation.
- **Environment-specific API config.**

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. The app will be available at `http://localhost:5173` (default Vite port).

## Configuration

- Update the API base URL and WebSocket URL in `src/api/config.js` if your backend is not running on `localhost:8000`.
- The backend must be running and accessible for API and WebSocket features to work.

## Project Structure

- `src/` - Main React source code
- `src/components/` - React components (Dashboard, EmailJobForm, FileUploadForm, JobDetails, JobStatsChart, etc.)
- `src/api/` - API utility functions

## Job Creation API Examples

### Send Email Job (JSON)

POST `/api/jobs/`

```json
{
  "job_type": "send_email",
  "parameters": {
    "recipient": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email."
  },
  "schedule_type": "immediate" // or "scheduled" or "interval"
  // "scheduled_time": "2025-06-27T15:00:00Z" (if scheduled or interval)
  // "frequency": "daily" (if interval)
}
```

### File Upload Job (multipart/form-data)

POST `/api/jobs/upload-file/`

- `file`: (the file itself)
- `schedule_type`: "immediate", "scheduled"
- `scheduled_time`: "2025-06-27T15:00:00Z" (if scheduled)
- `priority`: "normal" (optional)

## Requirements

- Node.js 18+
- Backend Django system running (see backend README)

## License

MIT
