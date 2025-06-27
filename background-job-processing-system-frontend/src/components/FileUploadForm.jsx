import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./FormStyles.css"; // Import the shared CSS file
import API_BASE from "../api/config";

function FileUploadForm() {
  const [file, setFile] = useState(null);
  const [scheduleType, setScheduleType] = useState("immediate");
  const [scheduledTime, setScheduledTime] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("schedule_type", scheduleType);
    if (scheduleType === "scheduled") {
      // Convert local datetime to UTC ISO string
      const local = new Date(scheduledTime);
      formData.append("scheduled_time", local.toISOString());
    }
    try {
      const res = await fetch(`${API_BASE}/jobs/upload-file/`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Failed to create file upload job");
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
        <h2>Upload File Job</h2>
        <form onSubmit={handleSubmit} className="styled-form">
          <div className="form-group">
            <label>File:</label>
            <br />
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              required
              className="form-control"
            />
          </div>
          <div className="form-group">
            <label>Schedule:</label>
            <br />
            <select
              value={scheduleType}
              onChange={(e) => setScheduleType(e.target.value)}
              className="form-control"
            >
              <option value="immediate">Immediate</option>
              <option value="scheduled">Scheduled</option>
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
              <div style={{ fontSize: "0.9em", color: "#555" }}>
                This will be converted to UTC when submitted. Your current
                timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}
              </div>
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            style={{ marginTop: 16 }}
            className="btn btn-primary w-100"
          >
            {loading ? "Submitting..." : "Upload File"}
          </button>
          {error && <div style={{ color: "red", marginTop: 8 }}>{error}</div>}
        </form>
      </div>
    </div>
  );
}

export default FileUploadForm;
