import React, { useEffect, useState, useRef } from "react";
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Card from "react-bootstrap/Card";
import "bootstrap/dist/css/bootstrap.min.css";
import JobStatsChart from "./JobStatsChart";
import API_BASE from "../api/config";
import { useNavigate } from "react-router-dom";
import { FaTrash, FaRedo, FaEdit, FaDownload } from "react-icons/fa";

// Dynamically determine WebSocket URL based on current location and fallback to 9000 if 8000 fails
function getWebSocketUrl() {
  const loc = window.location;
  let wsProtocol = loc.protocol === "https:" ? "wss:" : "ws:";
  let wsHost = loc.hostname;
  let wsPort = loc.port || (loc.protocol === "https:" ? "443" : "80");
  // Try 8000 first, fallback to 9000 if needed
  if (wsPort === "5173") wsPort = "8000";
  return `${wsProtocol}//${wsHost}:${wsPort}/ws/jobs/status/`;
}

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [previous, setPrevious] = useState(null);
  const [statsKey, setStatsKey] = useState(0); // For forcing JobStatsChart re-render
  const [jobTypeFilter, setJobTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const wsRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs(page);
    // WebSocket connection
    let wsUrl = getWebSocketUrl();
    wsRef.current = new window.WebSocket(wsUrl);
    wsRef.current.onclose = () => {
      // If connection fails on 8000, try 9000
      if (wsUrl.includes(":8000")) {
        wsUrl = wsUrl.replace(":8000", ":9000");
        wsRef.current = new window.WebSocket(wsUrl);
      }
    };
    wsRef.current.onmessage = (event) => {
      if (event.data) {
        const msg = JSON.parse(event.data);
        setJobs((prevJobs) =>
          prevJobs.map((job) =>
            job.id === msg.id
              ? { ...job, status: msg.status, result: msg.result }
              : job
          )
        );
        setStatsKey((k) => k + 1); // Force JobStatsChart to re-render/fetch
      }
    };
    return () => wsRef.current && wsRef.current.close();
    // eslint-disable-next-line
  }, [page, jobTypeFilter, statusFilter]);

  function fetchJobs(pageNum = 1) {
    let url = `${API_BASE}/jobs/?page=${pageNum}`;
    if (jobTypeFilter) url += `&job_type=${jobTypeFilter}`;
    if (statusFilter) url += `&status=${statusFilter}`;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setJobs(data.results || []);
        setCount(data.count || 0);
        setNext(data.next);
        setPrevious(data.previous);
      });
  }

  // Add handleDelete function
  function handleDelete(id) {
    if (window.confirm("Are you sure you want to delete this job?")) {
      fetch(`${API_BASE}/jobs/${id}/`, { method: "DELETE" })
        .then((res) => {
          if (res.ok) {
            // After delete, refetch jobs for the current page
            fetchJobs(page);
          } else {
            alert("Failed to delete job.");
          }
        })
        .catch(() => alert("Failed to delete job."));
    }
  }

  // Retry job handler
  function handleRetry(id) {
    fetch(`${API_BASE}/jobs/${id}/retry/`, { method: "POST" })
      .then((res) => {
        if (res.ok) {
          fetchJobs(page); // Refresh jobs for current page
        } else {
          res.json().then((data) => {
            alert(data.error || "Failed to retry job.");
          });
        }
      })
      .catch(() => alert("Failed to retry job."));
  }

  // Download file handler for file_upload jobs
  async function handleDownload(job) {
    if (!job.id) return;
    try {
      const res = await fetch(`${API_BASE}/jobs/${job.id}/download-url/`);
      if (!res.ok) throw new Error("Failed to get download URL");
      const data = await res.json();
      if (!data.download_url) throw new Error("No download URL returned");
      const link = document.createElement("a");
      link.href = data.download_url;
      link.download = job.parameters?.file_name || "download";
      link.target = "_blank";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      alert(err.message || "Failed to download file.");
    }
  }

  // Convert job_type to human-friendly string
  function humanizeJobType(type) {
    switch (type) {
      case "send_email":
        return "Send Email";
      case "file_upload":
        return "File Upload";
      default:
        // Convert snake_case to Title Case
        return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }
  }

  // Job type and status options
  const jobTypeOptions = [
    { value: "", label: "All Types" },
    { value: "send_email", label: "Send Email" },
    { value: "upload_file", label: "File Upload" },
  ];
  const statusOptions = [
    { value: "", label: "All Statuses" },
    { value: "pending", label: "Pending" },
    { value: "running", label: "Running" },
    { value: "completed", label: "Completed" },
    { value: "failed", label: "Failed" },
  ];

  return (
    <Container
      fluid
      className="app-main-bg mt-4"
      style={{
        minHeight: "90vh",
        width: "100vw",
        maxWidth: "100vw",
        padding: 0,
        overflowX: "hidden",
      }}
    >
      <Card className="shadow-sm" style={{ border: "none" }}>
        <Card.Body>
          <div className="row flex-column flex-md-row">
            <div className="col-12 col-md-8 pe-md-5 mb-4 mb-md-0">
              {/* Filter controls */}
              <div className="d-flex flex-wrap gap-3 mb-3 align-items-center">
                <select
                  className="form-select"
                  style={{ maxWidth: 200 }}
                  value={jobTypeFilter}
                  onChange={(e) => {
                    setJobTypeFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  {jobTypeOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <select
                  className="form-select"
                  style={{ maxWidth: 200 }}
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  {statusOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>SNO</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Scheduled Type</th>
                    <th>Action</th>
                    <th>Download</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job, idx) => {
                    let rowClass = "text-white";
                    if (job.status === "completed")
                      rowClass += " table-success";
                    else if (job.status === "failed")
                      rowClass += " table-danger";
                    else if (job.status === "running")
                      rowClass += " table-warning";
                    else if (job.status === "pending")
                      rowClass += " table-primary";

                    // Calculate SNO based on page and page size
                    const pageSize =
                      jobs.length > 0
                        ? Math.ceil(count / Math.ceil(count / jobs.length))
                        : 10;
                    const sno = (page - 1) * pageSize + idx + 1;

                    return (
                      <tr
                        key={job.id}
                        className={rowClass}
                        style={{ cursor: "pointer" }}
                        onClick={() => navigate(`/jobs/${job.id}`)}
                      >
                        <td>{sno}</td>
                        <td>
                          {humanizeJobType(job.job_type)
                            .charAt(0)
                            .toUpperCase() +
                            humanizeJobType(job.job_type).slice(1)}
                        </td>
                        <td>
                          {job.status.charAt(0).toUpperCase() +
                            job.status.slice(1)}
                        </td>
                        <td>
                          {job.schedule_type
                            ? job.schedule_type.charAt(0).toUpperCase() +
                              job.schedule_type.slice(1)
                            : ""}
                        </td>
                        <td className="text-center align-middle">
                          <button
                            className="btn btn-primary btn-sm me-2 d-inline-flex align-items-center justify-content-center"
                            title="Edit"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/jobs/${job.id}/edit`);
                            }}
                            disabled={
                              !(
                                (job.status === "pending" ||
                                  job.schedule_type === "scheduled" ||
                                  job.schedule_type === "interval") &&
                                job.schedule_type !== "immediate" &&
                                job.status !== "completed"
                              )
                            }
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="btn btn-secondary btn-sm me-2 d-inline-flex align-items-center justify-content-center"
                            title="Retry"
                            disabled={job.status !== "failed"}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRetry(job.id);
                            }}
                          >
                            <FaRedo />
                          </button>
                          <button
                            className="btn btn-danger btn-sm d-inline-flex align-items-center justify-content-center"
                            title="Delete"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(job.id);
                            }}
                          >
                            <FaTrash />
                          </button>
                        </td>
                        <td className="text-center align-middle">
                          <button
                            className="btn btn-success btn-sm d-inline-flex align-items-center justify-content-center"
                            title="Download"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownload(job);
                            }}
                            disabled={!job.file_url}
                          >
                            <FaDownload />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
              <div className="d-flex justify-content-between align-items-center mt-3">
                <button
                  className="btn btn-outline-primary"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!previous}
                >
                  Previous
                </button>
                <span>
                  Page {page} of{" "}
                  {jobs.length > 0 ? Math.ceil(count / jobs.length) : 1}
                </span>
                <button
                  className="btn btn-outline-primary"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!next}
                >
                  Next
                </button>
              </div>
            </div>
            <div className="col-12 col-md-4 d-flex align-items-center justify-content-center justify-content-md-end ps-md-5">
              <JobStatsChart key={statsKey} />
            </div>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
}

export default Dashboard;
