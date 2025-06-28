import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./FormStyles.css";
import API_BASE from "../api/config";

const frequencyOptions = [
  { value: "", label: "Select Frequency" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "hourly", label: "Hourly" },
];

function BulkEmailJobForm() {
  const [emails, setEmails] = useState([{ recipient: "", name: "" }]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [scheduleType, setScheduleType] = useState("immediate");
  const [scheduledTime, setScheduledTime] = useState("");
  const [frequency, setFrequency] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleEmailChange = (idx, field, value) => {
    setEmails((prev) =>
      prev.map((e, i) => (i === idx ? { ...e, [field]: value } : e))
    );
  };

  const addEmail = () => {
    setEmails((prev) => [...prev, { recipient: "", name: "" }]);
  };

  const removeEmail = (idx) => {
    setEmails((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    // Format emails for backend
    const formattedEmails = emails.map((e) => ({
      recipient: e.recipient,
      subject,
      body: body.replace(/\{\{name\}\}/g, e.name || ""),
    }));
    const data = {
      emails: formattedEmails,
      schedule_type: scheduleType,
    };
    if (scheduleType === "scheduled" || scheduleType === "interval") {
      const local = new Date(scheduledTime);
      data.scheduled_time = local.toISOString();
    }
    if (scheduleType === "interval") {
      data.frequency = frequency;
    }
    try {
      const res = await fetch(`${API_BASE}/jobs/send-email/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to create bulk email job");
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
        <h2>Bulk Send Email Job</h2>
        <form onSubmit={handleSubmit} className="styled-form">
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
            <label>
              Body
              <span
                style={{
                  fontWeight: 400,
                  fontSize: 13,
                  color: "#555",
                  marginLeft: 8,
                }}
              >
                (for personalization, click{" "}
                <button
                  type="button"
                  style={{
                    border: "none",
                    background: "none",
                    color: "#2563eb",
                    textDecoration: "underline",
                    cursor: "pointer",
                    fontFamily: "monospace",
                    fontSize: 13,
                    padding: 0,
                  }}
                  onClick={() => {
                    const textarea =
                      document.getElementById("bulk-body-textarea");
                    if (!textarea) return;
                    const start = textarea.selectionStart;
                    const end = textarea.selectionEnd;
                    const value = body;
                    const insert = "{{name}}";
                    const newValue =
                      value.slice(0, start) + insert + value.slice(end);
                    setBody(newValue);
                    setTimeout(() => {
                      textarea.focus();
                      textarea.selectionStart = textarea.selectionEnd =
                        start + insert.length;
                    }, 0);
                  }}
                >
                  {"{{name}}"}
                </button>{" "}
                to insert the recipient's name)
              </span>
              :
            </label>
            <br />
            <textarea
              id="bulk-body-textarea"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              className="form-control"
              rows={4}
            />
          </div>
          <div className="form-group">
            <label>Recipients:</label>
            {emails.map((e, idx) => (
              <div key={idx} className="d-flex align-items-center mb-2 gap-2">
                <input
                  type="email"
                  placeholder="Recipient Email"
                  value={e.recipient}
                  onChange={(ev) =>
                    handleEmailChange(idx, "recipient", ev.target.value)
                  }
                  required
                  className="form-control"
                  style={{ maxWidth: 220 }}
                />
                <input
                  type="text"
                  placeholder="Name (for {{name}})"
                  value={e.name}
                  onChange={(ev) =>
                    handleEmailChange(idx, "name", ev.target.value)
                  }
                  className="form-control"
                  style={{ maxWidth: 160 }}
                />
                {emails.length > 1 && (
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={() => removeEmail(idx)}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              className="btn btn-secondary btn-sm mt-2"
              onClick={addEmail}
            >
              Add Recipient
            </button>
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
                  {frequencyOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
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
            {loading ? "Submitting..." : "Send Bulk Emails"}
          </button>
          {error && <div style={{ color: "red", marginTop: 8 }}>{error}</div>}
        </form>
      </div>
    </div>
  );
}

export default BulkEmailJobForm;
