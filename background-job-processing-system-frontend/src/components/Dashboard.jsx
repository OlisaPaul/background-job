import React, { useEffect, useState, useRef } from "react";
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Card from "react-bootstrap/Card";
import "bootstrap/dist/css/bootstrap.min.css";
import JobStatsChart from "./JobStatsChart";

const API_BASE = "http://localhost:8000/api";
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
  const wsRef = useRef(null);

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
        console.log(JSON.parse(msg.id));
        setJobs((prevJobs) =>
          prevJobs.map((job) =>
            job.id === msg.id
              ? { ...job, status: msg.status, result: msg.result }
              : job
          )
        );
      }
    };
    return () => wsRef.current && wsRef.current.close();
    // eslint-disable-next-line
  }, [page]);

  function fetchJobs(pageNum = 1) {
    fetch(`${API_BASE}/jobs/?page=${pageNum}`)
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
            setJobs((prevJobs) => prevJobs.filter((job) => job.id !== id));
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

  return (
    <Container className="mt-32" style={{ maxWidth: 1400 }}>
      <Card className="shadow-sm">
        <Card.Body>
          <Card.Title as="h2" className="mb-4 text-center">
            Job Dashboard
          </Card.Title>
          <div className="row">
            <div className="col-md-8">
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>SNO</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Scheduled Time</th>
                    <th>Action</th>
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
                      <tr key={job.id} className={rowClass}>
                        <td>{sno}</td>
                        <td>{humanizeJobType(job.job_type)}</td>
                        <td>{job.status}</td>
                        <td>
                          {job.scheduled_time
                            ? new Date(job.scheduled_time).toLocaleString()
                            : "-"}
                        </td>
                        <td>
                          <button
                            className="btn btn-danger btn-sm me-2"
                            onClick={() => handleDelete(job.id)}
                          >
                            Delete
                          </button>
                          <button
                            className="btn btn-secondary btn-sm"
                            disabled={job.status !== "failed"}
                            onClick={() => handleRetry(job.id)}
                          >
                            Retry
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
            <div className="col-md-4 d-flex align-items-center justify-content-center">
              <JobStatsChart />
            </div>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
}

export default Dashboard;
