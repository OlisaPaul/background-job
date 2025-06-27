import React, { useEffect, useState } from "react";
import { Pie } from "react-chartjs-2";
import "chart.js/auto";
import API_BASE from "../api/config";

function JobStatsChart() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/jobs/stats/`)
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load stats");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading stats...</div>;
  if (error) return <div style={{ color: "red" }}>{error}</div>;
  if (!stats) return null;

  const data = {
    labels: ["Pending", "Running", "Completed", "Failed"],
    datasets: [
      {
        data: [stats.pending, stats.running, stats.completed, stats.failed],
        backgroundColor: [
          "#0d6efd", // blue
          "#ffc107", // yellow
          "#198754", // green
          "#dc3545", // red
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div style={{ maxWidth: 350, margin: "0 auto" }}>
      <h5 className="text-center mb-3">Job Status Overview</h5>
      <Pie data={data} />
      <ul style={{ listStyle: "none", padding: 0, marginTop: 16 }}>
        <li>
          <span style={{ color: "#0d6efd" }}>●</span> Pending: {stats.pending}
        </li>
        <li>
          <span style={{ color: "#ffc107" }}>●</span> Running: {stats.running}
        </li>
        <li>
          <span style={{ color: "#198754" }}>●</span> Completed:{" "}
          {stats.completed}
        </li>
        <li>
          <span style={{ color: "#dc3545" }}>●</span> Failed: {stats.failed}
        </li>
        <li>Total: {stats.total}</li>
      </ul>
    </div>
  );
}

export default JobStatsChart;
