import React from "react";
import { Routes, Route, Link, Navigate } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import EmailJobForm from "./components/EmailJobForm";
import FileUploadForm from "./components/FileUploadForm";
import JobDetails from "./components/JobDetails";
import BulkEmailJobForm from "./components/BulkEmailJobForm";
import EditJobForm from "./components/EditJobForm";
// Add react-icons
import { FaHome, FaEnvelope, FaUpload, FaUsers } from "react-icons/fa";

function App() {
  return (
    <>
      <nav
        style={{
          position: "sticky",
          top: 0,
          zIndex: 1000,
          background: "#2563eb",
          color: "#fff",
          padding: "1rem",
          borderBottom: "1px solid #1e40af",
          marginBottom: "0.5rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        }}
      >
        <Link
          to="/"
          style={{
            marginRight: 20,
            color: "#fff",
            fontWeight: 600,
            textDecoration: "none",
            fontSize: 18,
            display: "inline-flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <FaHome style={{ marginRight: 2 }} /> Home
        </Link>
        <Link
          to="/send-email"
          style={{
            marginRight: 20,
            color: "#fff",
            fontWeight: 600,
            textDecoration: "none",
            fontSize: 18,
            display: "inline-flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <FaEnvelope style={{ marginRight: 2 }} /> Send Email
        </Link>
        <Link
          to="/upload-file"
          style={{
            color: "#fff",
            fontWeight: 600,
            textDecoration: "none",
            fontSize: 18,
            display: "inline-flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <FaUpload style={{ marginRight: 2 }} /> Upload File
        </Link>
        <Link
          to="/bulk-send-email"
          style={{
            marginLeft: 20,
            color: "#fff",
            fontWeight: 600,
            textDecoration: "none",
            fontSize: 18,
            display: "inline-flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <FaUsers style={{ marginRight: 2 }} /> Bulk Send Email
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/send-email" element={<EmailJobForm />} />
        <Route path="/upload-file" element={<FileUploadForm />} />
        <Route path="/jobs/:id" element={<JobDetails />} />
        <Route path="/jobs/:id/edit" element={<EditJobForm />} />
        <Route path="/bulk-send-email" element={<BulkEmailJobForm />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;
