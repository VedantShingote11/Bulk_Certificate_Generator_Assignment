import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Plus, Trash2, Upload, FileText } from "lucide-react";

const EMPTY_RECIPIENT = { name: "", email: "", course_name: "" };

function RecipientRow({ recipient, index, onChange, onRemove, error }) {
  return (
    <div className={`recipient-row ${error ? "invalid" : ""}`}>
      <input
        className="form-input"
        placeholder="Full name *"
        value={recipient.name}
        onChange={(e) => onChange(index, "name", e.target.value)}
      />
      <input
        className="form-input"
        placeholder="Email *"
        type="email"
        value={recipient.email}
        onChange={(e) => onChange(index, "email", e.target.value)}
      />
      <input
        className="form-input"
        placeholder="Course name (optional)"
        value={recipient.course_name}
        onChange={(e) => onChange(index, "course_name", e.target.value)}
      />
      <button
        type="button"
        className="btn btn-danger btn-icon"
        onClick={() => onRemove(index)}
        title="Remove recipient"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

export default function RecipientsEditor({ recipients, onChange }) {
  const [csvError, setCsvError] = useState("");

  const addRow = () => onChange([...recipients, { ...EMPTY_RECIPIENT }]);

  const removeRow = (index) => {
    if (recipients.length <= 1) return;
    onChange(recipients.filter((_, i) => i !== index));
  };

  const updateRow = (index, field, value) => {
    const updated = [...recipients];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const onDrop = useCallback(
    (acceptedFiles) => {
      setCsvError("");
      const file = acceptedFiles[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const lines = e.target.result
            .split("\n")
            .map((l) => l.trim())
            .filter(Boolean);

          const header = lines[0].toLowerCase().split(",").map((h) => h.trim());
          const nameIdx = header.indexOf("name");
          const emailIdx = header.indexOf("email");
          const courseIdx = header.indexOf("course_name");

          if (nameIdx === -1 || emailIdx === -1) {
            setCsvError("CSV must have 'name' and 'email' columns.");
            return;
          }

          const parsed = lines
            .slice(1)
            .map((line) => {
              const cols = line.split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
              return {
                name: cols[nameIdx] || "",
                email: cols[emailIdx] || "",
                course_name: courseIdx !== -1 ? cols[courseIdx] || "" : "",
              };
            })
            .filter((r) => r.name || r.email);

          if (parsed.length === 0) {
            setCsvError("No valid rows found in CSV.");
            return;
          }

          onChange(parsed);
        } catch {
          setCsvError("Failed to parse CSV file.");
        }
      };
      reader.readAsText(file);
    },
    [onChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`drop-zone ${isDragActive ? "active" : ""}`}
        style={{ marginBottom: 16 }}
      >
        <input {...getInputProps()} />
        <div className="drop-zone-icon">
          <Upload size={28} color="var(--gold)" />
        </div>
        <p className="drop-zone-text">
          {isDragActive ? "Drop CSV here..." : "Drag & drop a CSV file, or click to select"}
        </p>
        <p className="drop-zone-hint">
          CSV format: <code>name, email, course_name</code>
        </p>
      </div>

      {csvError && <p className="error-text" style={{ marginBottom: 12 }}>{csvError}</p>}

      <div className="flex items-center justify-between mb-16">
        <span className="text-sm text-muted">
          <FileText size={14} style={{ display: "inline", marginRight: 6 }} />
          {recipients.length} recipient{recipients.length !== 1 ? "s" : ""}
        </span>
        <button type="button" className="btn btn-secondary btn-sm" onClick={addRow}>
          <Plus size={14} /> Add Row
        </button>
      </div>

      <div
        className="recipients-list"
        style={{ maxHeight: 360, overflowY: "auto", paddingRight: 4 }}
      >
        {recipients.map((r, i) => (
          <RecipientRow
            key={i}
            recipient={r}
            index={i}
            onChange={updateRow}
            onRemove={removeRow}
          />
        ))}
      </div>
    </div>
  );
}
