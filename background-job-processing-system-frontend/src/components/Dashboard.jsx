import React, { useEffect, useState, useRef } from "react";
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Card from "react-bootstrap/Card";
import "bootstrap/dist/css/bootstrap.min.css";

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
  const wsRef = useRef(null);

  useEffect(() => {
    fetchJobs();
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
  }, []);

  function fetchJobs() {
    fetch(`${API_BASE}/jobs/`)
      .then((res) => res.json())
      .then((data) => {
        setJobs(data.results || data || []);
      });
  }

  return (
    <Container style={{ maxWidth: 900, marginTop: 32 }}>
      <Card className="shadow-sm">
        <Card.Body>
          <Card.Title as="h2" className="mb-4 text-center">
            Job Dashboard
          </Card.Title>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Scheduled Time</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td>{job.job_type}</td>
                  <td>{job.status}</td>
                  <td>
                    {job.scheduled_time
                      ? new Date(job.scheduled_time).toLocaleString()
                      : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </Container>
  );
}

export default Dashboard;
