# React Frontend for Django Background Job System

This is a React frontend (Vite + React) for the Django background job processing system.

## Features

- Dashboard: Paginated list of all jobs with real-time status updates via WebSocket
- Send Email: Form to send an email (subject, recipient, body, immediate or scheduled)
- Upload File: Form to upload a file (immediate or scheduled)
- After job creation, user is routed to the dashboard
- Real-time job status updates using the backend WebSocket endpoint

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

- Update the API base URL and WebSocket URL in the frontend code if your backend is not running on `localhost:8000`.
- The backend must be running and accessible for API and WebSocket features to work.

## Project Structure

- `src/` - Main React source code
- `src/components/` - React components (Dashboard, JobForm, FileUploadForm, etc.)
- `src/api/` - API utility functions

## Requirements

- Node.js 18+
- Backend Django system running (see backend README)

## License

MIT
