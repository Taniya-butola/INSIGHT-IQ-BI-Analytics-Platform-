import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import PipelineStepper from "../components/PipelineStepper";
import { listDatasets, deleteDataset } from "../api/datasets";

export default function Datasets() {
  const [datasets, setDatasets] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    listDatasets()
      .then(setDatasets)
      .catch(() => setError("Could not load your datasets."));
  };

  useEffect(load, []);

  const onDelete = async (id) => {
    if (!confirm("Delete this dataset? This cannot be undone.")) return;
    await deleteDataset(id);
    load();
  };

  return (
    <AppShell title="My datasets">
      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      {datasets === null && !error && (
        <p className="text-ink-muted text-sm">Loading datasets…</p>
      )}

      {datasets?.length === 0 && (
        <div className="rounded-xl border border-border bg-surface p-8 text-center max-w-md">
          <p className="text-ink font-medium mb-1">No datasets yet</p>
          <p className="text-ink-muted text-sm mb-4">
            Upload your first sales file to start building your dashboard.
          </p>
          <Link
            to="/upload"
            className="inline-block rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90"
          >
            Upload dataset
          </Link>
        </div>
      )}

      {datasets && datasets.length > 0 && (
        <div className="rounded-xl border border-border bg-surface overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-ink-muted">
                <th className="px-4 py-3 font-normal">File</th>
                <th className="px-4 py-3 font-normal">Rows</th>
                <th className="px-4 py-3 font-normal">Columns</th>
                <th className="px-4 py-3 font-normal">Size</th>
                <th className="px-4 py-3 font-normal">Status</th>
                <th className="px-4 py-3 font-normal">Uploaded</th>
                <th className="px-4 py-3 font-normal"></th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.id} className="border-b border-border last:border-0 hover:bg-surface-raised/50">
                  <td className="px-4 py-3 text-ink">
                    <Link to={`/datasets/${d.id}`} className="hover:text-signal hover:underline">
                      {d.original_filename}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-mono text-ink-muted">
                    {d.row_count?.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-ink-muted">{d.column_count}</td>
                  <td className="px-4 py-3 font-mono text-ink-muted">
                    {(d.file_size_bytes / 1024).toFixed(1)} KB
                  </td>
                  <td className="px-4 py-3">
                    <PipelineStepper status={d.status} compact />
                  </td>
                  <td className="px-4 py-3 text-ink-muted">
                    {new Date(d.uploaded_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onDelete(d.id)}
                      className="text-ink-muted hover:text-danger text-xs"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
