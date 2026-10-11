import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listJobs } from "../api/client";
import { StatusBadge, ProgressBar } from "../components/StatusBadge";
import JobDetailModal from "../components/JobDetailModal";
import { Eye, RefreshCw, FilePlus } from "lucide-react";
import { Link } from "react-router-dom";

const PAGE_SIZE = 10;

export default function JobList() {
  const [page, setPage] = useState(0);
  const [selectedJobId, setSelectedJobId] = useState(null);

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["jobs", page],
    queryFn: () => listJobs(page * PAGE_SIZE, PAGE_SIZE).then((r) => r.data),
    refetchInterval: 5000,
  });

  const jobs = data?.jobs || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">All Jobs</h1>
          <p className="page-subtitle">Track and manage all certificate generation jobs</p>
        </div>
        <div className="flex gap-8">
          <button
            className="btn btn-secondary"
            onClick={() => refetch()}
            title="Refresh"
          >
            <RefreshCw size={15} className={isFetching ? "pulse" : ""} />
            Refresh
          </button>
          <Link to="/create" className="btn btn-primary">
            <FilePlus size={15} /> New Job
          </Link>
        </div>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🏅</span>
            <p className="empty-state-text">No certificate jobs yet</p>
            <Link to="/create" className="btn btn-primary btn-sm" style={{ marginTop: 12 }}>
              <FilePlus size={14} /> Create First Job
            </Link>
          </div>
        ) : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Issued By</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Success / Fail / Total</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.id}>
                      <td>
                        <div style={{ fontWeight: 500 }}>{job.event_name}</div>
                        <div
                          className="text-sm text-muted font-mono"
                          style={{ fontSize: 11, marginTop: 2 }}
                        >
                          {job.id.slice(0, 8)}…
                        </div>
                      </td>
                      <td className="text-sm">{job.issued_by}</td>
                      <td><StatusBadge status={job.status} /></td>
                      <td style={{ minWidth: 130 }}>
                        <ProgressBar percent={job.progress_percent} />
                      </td>
                      <td className="text-sm">
                        <span className="text-green">{job.completed_count}</span>
                        {" / "}
                        <span className="text-red">{job.failed_count}</span>
                        {" / "}
                        <span className="text-muted">{job.total_recipients}</span>
                      </td>
                      <td className="text-sm text-muted">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setSelectedJobId(job.id)}
                        >
                          <Eye size={13} /> View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <span className="text-sm text-muted">{total} jobs total</span>
                {Array.from({ length: totalPages }, (_, i) => (
                  <button
                    key={i}
                    className={`page-btn ${i === page ? "active" : ""}`}
                    onClick={() => setPage(i)}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {selectedJobId && (
        <JobDetailModal jobId={selectedJobId} onClose={() => setSelectedJobId(null)} />
      )}
    </div>
  );
}
