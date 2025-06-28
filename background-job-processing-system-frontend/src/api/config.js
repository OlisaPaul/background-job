// src/api/config.js

const API_BASE =
  import.meta.env.MODE === "production"
    ? "https://background-job-l5e8.onrender.com/api"
    : "http://localhost:8000/api";

export default API_BASE;
