// src/api/config.js

const API_BASE =
  import.meta.env.MODE === "production"
    ? "https://your-production-domain.com/api"
    : "http://localhost:8000/api";

export default API_BASE;
