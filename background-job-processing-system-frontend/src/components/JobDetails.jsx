import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Card from "react-bootstrap/Card";
import Button from "react-bootstrap/Button";
import API_BASE from "../api/config";

function JobDetails() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API_BASE}/jobs/${id}/`)
      .then((res) => {
        if (!res.ok) throw new Error("Job not found");
        return res.json();
      })
      .then((data) => {
        setJob(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  function handleDelete() {
    if (!window.confirm("Are you sure you want to delete this job?")) return;
    setDeleting(true);
    fetch(`${API_BASE}/jobs/${id}/`, { method: "DELETE" })
      .then((res) => {
        if (res.ok) {
          navigate("/");
        } else {
          setError("Failed to delete job.");
        }
      })
      .catch(() => setError("Failed to delete job."))
      .finally(() => setDeleting(false));
  }

  // Helper to humanize job type
  function humanizeJobType(type) {
    if (!type) return "-";
    return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  if (loading) return <div className="text-center mt-5">Loading...</div>;
  if (error) return <div className="text-danger text-center mt-5">{error}</div>;
  if (!job) return null;

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
      <div
        className="d-flex justify-content-center align-items-center"
        style={{ minHeight: "80vh" }}
      >
        <Card
          style={{
            minWidth: 400,
            maxWidth: 600,
            width: "100%",
            position: "relative",
          }}
          className="shadow"
        >
          <Button
            variant="danger"
            style={{
              position: "absolute",
              top: 16,
              right: 16,
              zIndex: 2,
            }}
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? "Deleting..." : "Delete"}
          </Button>
          <Card.Body>
            <Card.Title as="h3" className="mb-3 text-center">
              Job Details
            </Card.Title>
            {/* <div className="mb-3">
              <strong>ID:</strong> {job.id}
            </div> */}
            <div className="mb-3">
              <strong>Type:</strong> {humanizeJobType(job.job_type)}
            </div>
            <div className="mb-3">
              <strong>Status:</strong> {job.status}
            </div>
            <div className="mb-3">
              <strong>Created At:</strong>{" "}
              {job.created_at ? new Date(job.created_at).toLocaleString() : "-"}
            </div>
            <div className="mb-3">
              <strong>Updated At:</strong>{" "}
              {job.updated_at ? new Date(job.updated_at).toLocaleString() : "-"}
            </div>
            <div className="mb-3">
              <strong>Scheduled Time:</strong>{" "}
              {job.scheduled_time
                ? new Date(job.scheduled_time).toLocaleString()
                : "-"}
            </div>
            <div className="mb-3">
              <strong>Schedule Type:</strong> {job.schedule_type}
            </div>
            <div className="mb-3">
              <strong>Priority:</strong> {job.priority}
            </div>
            <div className="mb-3">
              <strong>Retries:</strong> {job.retries} / {job.max_retries}
            </div>
            {job.file_url && (
              <div className="mb-3">
                <strong>File URL:</strong>{" "}
                <a
                  href={job.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Download
                </a>
              </div>
            )}
            <Button
              variant="secondary"
              className="w-100 mt-3"
              onClick={() => navigate(-1)}
            >
              Back
            </Button>
          </Card.Body>
        </Card>
      </div>
    </div>
  );
}

export default JobDetails;
