import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { createJob } from "../api/client";
import RecipientsEditor from "../components/RecipientsEditor";
import { Send, Info, CalendarDays, Building2, Trophy } from "lucide-react";

const EMPTY_RECIPIENT = { name: "", email: "", course_name: "" };

export default function CreateJob() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    event_name: "",
    issued_by: "",
    issue_date: new Date().toISOString().slice(0, 10),
  });
  const [recipients, setRecipients] = useState([{ ...EMPTY_RECIPIENT }]);
  const [errors, setErrors] = useState({});

  const mutation = useMutation({
    mutationFn: createJob,
    onSuccess: (res) => {
      toast.success(`Job created! Processing ${res.data.total_recipients} certificates.`);
      navigate("/jobs");
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        toast.error(detail.map((d) => d.msg).join(", "));
      } else {
        toast.error(typeof detail === "string" ? detail : "Failed to create job");
      }
    },
  });

  const validate = () => {
    const errs = {};
    if (!form.event_name.trim()) errs.event_name = "Event name is required";
    if (!form.issued_by.trim()) errs.issued_by = "Issuing organisation is required";
    if (!form.issue_date.trim()) errs.issue_date = "Issue date is required";

    const validRecipients = recipients.filter((r) => r.name.trim() || r.email.trim());
    if (validRecipients.length === 0) errs.recipients = "At least one recipient is required";

    const invalidEmail = validRecipients.some(
      (r) => r.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(r.email)
    );
    if (invalidEmail) errs.recipients = "Some email addresses are invalid";

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    const cleanRecipients = recipients
      .filter((r) => r.name.trim() && r.email.trim())
      .map((r) => ({
        name: r.name.trim(),
        email: r.email.trim(),
        ...(r.course_name?.trim() ? { course_name: r.course_name.trim() } : {}),
      }));

    mutation.mutate({ ...form, recipients: cleanRecipients });
  };

  const setField = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    setErrors((er) => ({ ...er, [field]: undefined }));
  };

  const validCount = recipients.filter((r) => r.name.trim() && r.email.trim()).length;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Create Certificate Job</h1>
        <p className="page-subtitle">
          Define the event details and add recipients — each gets a personalised PDF certificate
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Event details card */}
        <div className="card mb-24">
          <div className="card-title">
            <Trophy size={16} color="var(--blue)" />
            Event Details
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">
                Event Name <span className="required">*</span>
              </label>
              <input
                className="form-input"
                placeholder="e.g. Python Bootcamp 2026"
                value={form.event_name}
                onChange={setField("event_name")}
              />
              {errors.event_name && <p className="error-text">{errors.event_name}</p>}
            </div>

            <div className="form-group">
              <label className="form-label">
                Issued By <span className="required">*</span>
              </label>
              <div style={{ position: "relative" }}>
                <Building2
                  size={14}
                  style={{
                    position: "absolute", left: 10, top: "50%",
                    transform: "translateY(-50%)", color: "var(--text-muted)",
                    pointerEvents: "none",
                  }}
                />
                <input
                  className="form-input"
                  style={{ paddingLeft: 30 }}
                  placeholder="e.g. Tech Academy"
                  value={form.issued_by}
                  onChange={setField("issued_by")}
                />
              </div>
              {errors.issued_by && <p className="error-text">{errors.issued_by}</p>}
            </div>
          </div>

          <div className="form-group" style={{ maxWidth: 240 }}>
            <label className="form-label">
              Issue Date <span className="required">*</span>
            </label>
            <div style={{ position: "relative" }}>
              <CalendarDays
                size={14}
                style={{
                  position: "absolute", left: 10, top: "50%",
                  transform: "translateY(-50%)", color: "var(--text-muted)",
                  pointerEvents: "none",
                }}
              />
              <input
                className="form-input"
                style={{ paddingLeft: 30 }}
                type="date"
                value={form.issue_date}
                onChange={setField("issue_date")}
              />
            </div>
            {errors.issue_date && <p className="error-text">{errors.issue_date}</p>}
          </div>
        </div>

        {/* Recipients card */}
        <div className="card mb-24">
          <div className="card-title">
            <Send size={16} color="var(--blue)" />
            Recipients
          </div>

          <div className="info-banner mb-16">
            <Info size={13} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>
              Add recipients manually or import a <strong>CSV</strong> file with columns:{" "}
              <code style={{ background: "rgba(37,99,235,.1)", padding: "1px 5px", borderRadius: 3 }}>name</code>,{" "}
              <code style={{ background: "rgba(37,99,235,.1)", padding: "1px 5px", borderRadius: 3 }}>email</code>,{" "}
              <code style={{ background: "rgba(37,99,235,.1)", padding: "1px 5px", borderRadius: 3 }}>course_name</code> (optional).
            </span>
          </div>

          <RecipientsEditor recipients={recipients} onChange={setRecipients} />
          {errors.recipients && <p className="error-text mt-8">{errors.recipients}</p>}
        </div>

        {/* Submit row */}
        <div
          style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            background: "var(--bg-white)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "14px 20px",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <div className="text-sm text-muted">
            {validCount > 0 ? (
              <span>
                <strong style={{ color: "var(--text-primary)" }}>{validCount}</strong> valid recipient{validCount !== 1 ? "s" : ""} ready to process
              </span>
            ) : (
              "No valid recipients yet"
            )}
          </div>
          <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? (
              <><div className="spinner" style={{ borderTopColor: "#fff" }} /> Submitting…</>
            ) : (
              <><Send size={14} /> Generate Certificates</>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
