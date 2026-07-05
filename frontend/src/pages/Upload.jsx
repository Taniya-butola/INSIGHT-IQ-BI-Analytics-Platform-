import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { ErrorList } from "../components/ui";
import { uploadDataset } from "../api/datasets";

const ACCEPTED = [".csv", ".xlsx"];

export default function Upload() {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [errors, setErrors] = useState([]);
  const [result, setResult] = useState(null);

  const handleFiles = (fileList) => {
    const picked = fileList?.[0];
    if (!picked) return;
    const ext = "." + picked.name.split(".").pop().toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setErrors([`Unsupported file type "${ext}". Upload a .csv or .xlsx file.`]);
      return;
    }
    setErrors([]);
    setFile(picked);
    setResult(null);
    setStatus("idle");
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, []);

  const onSubmit = async () => {
    if (!file) return;
    setStatus("uploading");
    setErrors([]);
    setProgress(0);
    try {
      const dataset = await uploadDataset(file, setProgress);
      setResult(dataset);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrors(err.response?.data?.errors || ["Upload failed. Please try again."]);
    }
  };

  return (
    <AppShell title="Upload dataset">
      <div className="max-w-2xl">
        <p className="text-ink-muted text-sm mb-6">
          Upload a retail sales dataset as CSV or Excel. INSIGHT IQ checks the file,
          reads its structure, and prepares it for validation and cleaning in the
          next phase.
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`rounded-xl border-2 border-dashed px-6 py-14 text-center cursor-pointer transition-colors
            ${dragOver ? "border-signal bg-signal/5" : "border-border bg-surface hover:border-signal/40"}`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <div className="w-12 h-12 mx-auto mb-4 rounded-lg bg-signal/10 border border-signal/30 flex items-center justify-center">
            <span className="text-signal text-lg">↑</span>
          </div>
          {file ? (
            <>
              <p className="text-ink font-medium">{file.name}</p>
              <p className="text-ink-muted text-xs mt-1 font-mono">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </>
          ) : (
            <>
              <p className="text-ink font-medium">Drag and drop your file here</p>
              <p className="text-ink-muted text-sm mt-1">or click to browse · CSV or XLSX · up to 25MB</p>
            </>
          )}
        </div>

        <div className="mt-4">
          <ErrorList errors={errors} />
        </div>

        {status === "uploading" && (
          <div className="mt-4">
            <div className="h-1.5 rounded-full bg-surface-raised overflow-hidden">
              <div
                className="h-full bg-signal transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-ink-muted mt-2 font-mono">Uploading… {progress}%</p>
          </div>
        )}

        {status === "success" && result && (
          <div className="mt-6 rounded-xl border border-signal/30 bg-signal/5 p-5">
            <p className="text-signal font-medium text-sm mb-3">Upload complete</p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Stat label="Rows" value={result.row_count?.toLocaleString()} />
              <Stat label="Columns" value={result.column_count} />
              <Stat label="File size" value={`${(result.file_size_bytes / 1024).toFixed(1)} KB`} />
              <Stat label="Status" value={result.status} />
            </div>
            <button
              onClick={() => navigate(`/datasets/${result.id}`)}
              className="mt-4 text-sm text-signal hover:underline"
            >
              Run validation & cleaning →
            </button>
          </div>
        )}

        <button
          onClick={onSubmit}
          disabled={!file || status === "uploading"}
          className="mt-6 rounded-lg bg-signal text-[#06110d] font-medium px-5 py-2.5 text-sm
            hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
        >
          {status === "uploading" ? "Uploading…" : "Upload dataset"}
        </button>
      </div>
    </AppShell>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-ink-muted text-xs">{label}</p>
      <p className="text-ink font-mono">{value}</p>
    </div>
  );
}
