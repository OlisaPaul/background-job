import React from "react";
import { Routes, Route, Link, Navigate } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import EmailJobForm from "./components/EmailJobForm";
import FileUploadForm from "./components/FileUploadForm";

function App() {
  return (
    <>
      <nav
        style={{
          padding: "1rem",
          borderBottom: "1px solid #eee",
          marginBottom: "2rem",
        }}
      >
        <Link to="/" style={{ marginRight: 16 }}>
          Dashboard
        </Link>
        <Link to="/send-email" style={{ marginRight: 16 }}>
          Send Email
        </Link>
        <Link to="/upload-file">Upload File</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/send-email" element={<EmailJobForm />} />
        <Route path="/upload-file" element={<FileUploadForm />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;
