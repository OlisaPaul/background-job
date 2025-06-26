import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://localhost:8000/api";

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
      formData.append("scheduled_time", scheduledTime);
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
    <div style={{ maxWidth: 500, margin: "0 auto" }}>
      <h2>Upload File Job</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>File:</label>
          <br />
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            required
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
          {loading ? "Submitting..." : "Upload File"}
        </button>
        {error && <div style={{ color: "red", marginTop: 8 }}>{error}</div>}
      </form>
    </div>
  );
}

export default FileUploadForm;
