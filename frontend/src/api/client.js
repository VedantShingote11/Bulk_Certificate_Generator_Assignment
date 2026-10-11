import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

export const createJob = (payload) => api.post("/certificates/jobs", payload);
export const listJobs = (skip = 0, limit = 20) =>
  api.get(`/certificates/jobs?skip=${skip}&limit=${limit}`);
export const getJob = (jobId) => api.get(`/certificates/jobs/${jobId}`);
export const getJobCertificates = (jobId, status = "") =>
  api.get(
    `/certificates/jobs/${jobId}/certificates${status ? `?status=${status}` : ""}`
  );
export const downloadCertificate = (certId) =>
  `http://localhost:8000/api/v1/certificates/${certId}/download`;

export default api;
