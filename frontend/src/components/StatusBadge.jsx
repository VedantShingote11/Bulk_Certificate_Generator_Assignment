export function StatusBadge({ status }) {
  const labels = {
    pending: "Pending",
    processing: "Processing",
    completed: "Completed",
    failed: "Failed",
    partial: "Partial",
    generating: "Generating",
  };

  return (
    <span className={`badge badge-${status}`}>
      {status === "processing" || status === "generating" ? (
        <span className="spinner" style={{ width: 8, height: 8, borderWidth: 1.5, borderTopColor: "var(--blue)", borderColor: "var(--blue-border)" }} />
      ) : null}
      {labels[status] || status}
    </span>
  );
}

export function ProgressBar({ percent }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div className="progress-bar-track" style={{ flex: 1 }}>
        <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="text-sm text-muted" style={{ minWidth: 36 }}>
        {percent.toFixed(0)}%
      </span>
    </div>
  );
}
