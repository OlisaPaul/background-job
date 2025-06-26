import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://localhost:8000/api";

function EmailJobForm() {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [scheduleType, setScheduleType] = useState("immediate");
  const [scheduledTime, setScheduledTime] = useState("");
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
    if (scheduleType === "scheduled") {
      data.scheduled_time = scheduledTime;
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
    <div style={{ maxWidth: 500, margin: "0 auto" }}>
      <h2>Send Email Job</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Recipient Email:</label>
          <br />
          <input
            type="email"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            required
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label>Subject:</label>
          <br />
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label>Body:</label>
          <br />
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            required
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label>Schedule:</label>
          <br />
          <select
            value={scheduleType}
            onChange={(e) => setScheduleType(e.target.value)}
          >
            <option value="immediate">Immediate</option>
            <option value="scheduled">Scheduled</option>
          </select>
        </div>
        {scheduleType === "scheduled" && (
          <div>
            <label>Scheduled Time (UTC):</label>
            <br />
            <input
              type="datetime-local"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              required
            />
          </div>
        )}
        <button type="submit" disabled={loading} style={{ marginTop: 16 }}>
          {loading ? "Submitting..." : "Send Email"}
        </button>
        {error && <div style={{ color: "red", marginTop: 8 }}>{error}</div>}
      </form>
    </div>
  );
}

export default EmailJobForm;
