import { useQuery } from "@tanstack/react-query";
import { listJobs } from "../api/client";
import { StatusBadge, ProgressBar } from "../components/StatusBadge";
import { TrendingUp, CheckCircle, XCircle, Clock, Award, Zap } from "lucide-react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["jobs", 0, 100],
    queryFn: () => listJobs(0, 100).then((r) => r.data),
    refetchInterval: 5000,
  });

  const jobs = data?.jobs || [];
  const total = data?.total || 0;
  const completed = jobs.filter((j) => j.status === "completed").length;
  const failed = jobs.filter((j) => j.status === "failed").length;
  const processing = jobs.filter((j) => j.status === "processing" || j.status === "pending").length;
  const totalCerts = jobs.reduce((s, j) => s + j.total_recipients, 0);
  const completedCerts = jobs.reduce((s, j) => s + j.completed_count, 0);

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Overview of all certificate generation activity</p>
        </div>
        <Link to="/create" className="btn btn-primary">
          <Award size={14} /> New Job
        </Link>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Jobs</div>
          <div className="stat-value">{total}</div>
          <div className="text-sm text-muted mt-4" style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <TrendingUp size={12} /> All time
          </div>
        </div>
        <div className="stat-card stat-green">
          <div className="stat-label">Completed</div>
          <div className="stat-value">{completed}</div>
          <div className="text-sm mt-4" style={{ color: "var(--green)", display: "flex", alignItems: "center", gap: 4 }}>
            <CheckCircle size={12} /> Successful jobs
          </div>
        </div>
        <div className="stat-card stat-blue">
          <div className="stat-label">In Progress</div>
          <div className="stat-value">{processing}</div>
          <div className="text-sm mt-4" style={{ color: "var(--blue)", display: "flex", alignItems: "center", gap: 4 }}>
            <Zap size={12} /> Active / Pending
          </div>
        </div>
        <div className="stat-card stat-red">
          <div className="stat-label">Failed</div>
          <div className="stat-value">{failed}</div>
          <div className="text-sm mt-4" style={{ color: "var(--red)", display: "flex", alignItems: "center", gap: 4 }}>
            <XCircle size={12} /> Need attention
          </div>
        </div>
        <div className="stat-card stat-gold">
          <div className="stat-label">Certificates Issued</div>
          <div className="stat-value">{completedCerts.toLocaleString()}</div>
          <div className="text-sm text-muted mt-4">of {totalCerts.toLocaleString()} total</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          <Clock size={16} color="var(--blue)" />
          Recent Jobs
        </div>

        {isLoading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🏅</span>
            <p className="empty-state-text">No jobs yet — create your first certificate batch!</p>
            <Link to="/create" className="btn btn-primary btn-sm" style={{ marginTop: 12 }}>
              Get Started
            </Link>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Results</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {jobs.slice(0, 6).map((job) => (
                  <tr key={job.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{job.event_name}</div>
                      <div className="text-sm text-muted">{job.issued_by}</div>
                    </td>
                    <td><StatusBadge status={job.status} /></td>
                    <td style={{ minWidth: 140 }}>
                      <ProgressBar percent={job.progress_percent} />
                    </td>
                    <td className="text-sm">
                      <span style={{ color: "var(--green)", fontWeight: 600 }}>{job.completed_count}</span>
                      <span className="text-muted"> / </span>
                      <span className="text-muted">{job.total_recipients}</span>
                      {job.failed_count > 0 && (
                        <span style={{ color: "var(--red)" }}> · {job.failed_count} failed</span>
                      )}
                    </td>
                    <td className="text-sm text-muted">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
