import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./FormStyles.css"; // Import the shared CSS file
import API_BASE from "../api/config";

function EmailJobForm() {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [scheduleType, setScheduleType] = useState("immediate");
  const [scheduledTime, setScheduledTime] = useState("");
  const [frequency, setFrequency] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const data = {
      job_type: "send_email",
      parameters: { recipient, subject, body },
      schedule_type: scheduleType,
    };
    if (scheduleType === "scheduled" || scheduleType === "interval") {
      // Convert local datetime to UTC ISO string
      const local = new Date(scheduledTime);
      data.scheduled_time = local.toISOString();
    }
    if (scheduleType === "interval") {
      data.frequency = frequency;
    }
    try {
      const res = await fetch(`${API_BASE}/jobs/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to create job");
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="app-main-bg"
      style={{
        minHeight: "100vh",
        width: "100vw",
        maxWidth: "100vw",
        padding: 0,
        overflowX: "hidden",
      }}
    >
      <div className="form-container">
        <h2>Send Email Job</h2>
        <form onSubmit={handleSubmit} className="styled-form">
          <div className="form-group">
            <label>Recipient Email:</label>
            <br />
            <input
              type="email"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              required
              className="form-control"
            />
          </div>
          <div className="form-group">
            <label>Subject:</label>
            <br />
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              className="form-control"
            />
          </div>
          <div className="form-group">
            <label>Body:</label>
            <br />
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              className="form-control"
            />
          </div>
          <div className="form-group">
            <label>Schedule:</label>
            <br />
            <select
              value={scheduleType}
              onChange={(e) => {
                setScheduleType(e.target.value);
                setFrequency("");
              }}
              className="form-control"
            >
              <option value="immediate">Immediate</option>
              <option value="scheduled">Scheduled</option>
              <option value="interval">Interval</option>
            </select>
          </div>
          {scheduleType === "scheduled" && (
            <div className="form-group">
              <label>Scheduled Time (your local time):</label>
              <br />
              <input
                type="datetime-local"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                required
                className="form-control"
              />
            </div>
          )}
          {scheduleType === "interval" && (
            <>
              <div className="form-group">
                <label>Frequency:</label>
                <br />
                <select
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  required
                  className="form-control"
                >
                  <option value="">Select Frequency</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="hourly">Hourly</option>
                </select>
              </div>
              <div className="form-group">
                <label>Start Time (your local time):</label>
                <br />
                <input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  required
                  className="form-control"
                />
              </div>
            </>
          )}
          <button
            type="submit"
            disabled={loading}
            style={{ marginTop: 16 }}
            className="btn btn-primary w-100"
          >
            {loading ? "Submitting..." : "Send Email"}
          </button>
          {error && <div style={{ color: "red", marginTop: 8 }}>{error}</div>}
        </form>
      </div>
    </div>
  );
}

export default EmailJobForm;
