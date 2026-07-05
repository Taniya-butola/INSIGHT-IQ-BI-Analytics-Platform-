import { useEffect, useState } from "react";
import { listReportTypes, downloadReport } from "../api/datasets";

const DESCRIPTIONS = {
  "executive-summary": "KPIs, top insights, and top performers in one page.",
  sales: "Revenue trend, regional sales, and top/low performing products.",
  "customer-analytics": "Top customers, segments, and churn risk (if modeled).",
  financial: "Revenue, profit margin, and revenue vs. profit over time.",
  inventory: "Stock levels and low-stock alerts.",
};

export default function ReportsTab({ datasetId, filenameHint }) {
  const [reportTypes, setReportTypes] = useState(null);
  const [downloading, setDownloading] = useState(null); // `${slug}:${format}` or null
  const [error, setError] = useState("");

  useEffect(() => {
    listReportTypes()
      .then(setReportTypes)
      .catch(() => setError("Could not load report types."));
  }, []);

  const handleDownload = async (slug, format) => {
    setDownloading(`${slug}:${format}`);
    setError("");
    try {
      await downloadReport(datasetId, slug, format, filenameHint);
    } catch {
      setError("Could not generate that report. Try again in a moment.");
    } finally {
      setDownloading(null);
    }
  };

  if (!reportTypes) {
    return <p className="text-ink-muted text-sm">{error || "Loading report types…"}</p>;
  }

  return (
    <div className="space-y-4">
      <p className="text-ink-muted text-sm">
        Reports are generated on the spot from this dataset's cleaned data (or raw data if not
        yet cleaned), plus any insights or predictive models you've already run.
      </p>
      {error && <p className="text-danger text-sm">{error}</p>}

      <div className="grid md:grid-cols-2 gap-4">
        {reportTypes.map(({ slug, label }) => (
          <div key={slug} className="rounded-xl border border-border bg-surface p-5">
            <p className="text-ink font-medium text-sm mb-1">{label}</p>
            <p className="text-ink-muted text-sm mb-4">{DESCRIPTIONS[slug]}</p>
            <div className="flex gap-2">
              <DownloadButton
                label="PDF"
                busy={downloading === `${slug}:pdf`}
                disabled={downloading !== null}
                onClick={() => handleDownload(slug, "pdf")}
              />
              <DownloadButton
                label="Excel"
                busy={downloading === `${slug}:xlsx`}
                disabled={downloading !== null}
                onClick={() => handleDownload(slug, "xlsx")}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DownloadButton({ label, busy, disabled, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="text-sm rounded-lg border border-border text-ink-muted px-4 py-2 hover:text-ink hover:border-signal/40 disabled:opacity-40 transition-colors"
    >
      {busy ? "Generating…" : `Download ${label}`}
    </button>
  );
}
