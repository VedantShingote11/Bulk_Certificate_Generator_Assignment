import { X } from "lucide-react";
import { StatusBadge, ProgressBar } from "./StatusBadge";
import { useQuery } from "@tanstack/react-query";
import { getJob, getJobCertificates, downloadCertificate } from "../api/client";
import { Download, RefreshCw } from "lucide-react";

export default function JobDetailModal({ jobId, onClose }) {
  const { data: jobData, isLoading: jobLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId).then((r) => r.data),
    refetchInterval: (data) =>
      data?.status === "pending" || data?.status === "processing" ? 2000 : false,
  });

  const { data: certs, isLoading: certsLoading } = useQuery({
    queryKey: ["job-certs", jobId],
    queryFn: () => getJobCertificates(jobId).then((r) => r.data),
    refetchInterval: jobData?.status === "processing" ? 2000 : false,
    enabled: !!jobId,
  });

  const job = jobData;

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <h2 className="modal-title">{job?.event_name || "Loading..."}</h2>
            {job && (
              <p className="text-sm text-muted mt-4">
                {job.total_recipients} recipients · Issued by {job.issued_by} · {job.issue_date}
              </p>
            )}
          </div>
          <button className="btn btn-secondary btn-icon" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {jobLoading ? (
            <div className="empty-state">
              <div className="spinner" />
            </div>
          ) : job ? (
            <>
              {/* Job Summary */}
              <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
                <div className="stat-card">
                  <span className="stat-label">Status</span>
                  <StatusBadge status={job.status} />
                </div>
                <div className="stat-card stat-green">
                  <span className="stat-label">Completed</span>
                  <span className="stat-value">{job.completed_count}</span>
                </div>
                <div className="stat-card stat-red">
                  <span className="stat-label">Failed</span>
                  <span className="stat-value">{job.failed_count}</span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">Total</span>
                  <span className="stat-value">{job.total_recipients}</span>
                </div>
              </div>

              {(job.status === "processing" || job.status === "pending") && (
                <div style={{ marginBottom: 20 }}>
                  <ProgressBar percent={job.progress_percent} />
                </div>
              )}

              {/* Certificates Table */}
              <h3 className="card-title" style={{ marginBottom: 12 }}>
                Certificates
              </h3>

              {certsLoading ? (
                <div className="empty-state"><div className="spinner" /></div>
              ) : certs?.length > 0 ? (
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th>Recipient</th>
                        <th>Email</th>
                        <th>Course</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {certs.map((cert) => (
                        <tr key={cert.id}>
                          <td style={{ fontWeight: 500 }}>{cert.recipient_name}</td>
                          <td className="text-muted text-sm">{cert.recipient_email}</td>
                          <td className="text-sm">{cert.course_name || "—"}</td>
                          <td>
                            <StatusBadge status={cert.status} />
                            {cert.error_message && (
                              <p className="error-text" title={cert.error_message}>
                                {cert.error_message.slice(0, 50)}...
                              </p>
                            )}
                          </td>
                          <td>
                            {cert.status === "completed" && (
                              <a
                                href={downloadCertificate(cert.id)}
                                target="_blank"
                                rel="noreferrer"
                                className="btn btn-primary btn-sm"
                              >
                                <Download size={12} /> PDF
                              </a>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <span className="empty-state-icon">📄</span>
                  <p className="empty-state-text">No certificates found</p>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
