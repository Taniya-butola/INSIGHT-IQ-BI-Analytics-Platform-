import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import PipelineStepper from "../components/PipelineStepper";
import EdaTab from "./EdaTab";
import PredictiveTab from "./PredictiveTab";
import InsightsTab from "./InsightsTab";
import ReportsTab from "./ReportsTab";
import AskTab from "./AskTab";
import {
  getDataset,
  validateDataset,
  getValidation,
  cleanDataset,
  getCleaning,
  previewDataset,
  runEda,
  getEda,
  runPredictive,
  getPredictive,
  runInsights,
  getInsights,
} from "../api/datasets";

const TABS = ["Validation", "Cleaning", "Data Preview", "EDA", "Predictive", "Insights", "Reports", "Ask INSIGHT IQ"];

export default function DatasetDetail() {
  const { id } = useParams();

  const [dataset, setDataset] = useState(null);
  const [validation, setValidation] = useState(null);
  const [cleaning, setCleaning] = useState(null);
  const [eda, setEda] = useState(null);
  const [predictive, setPredictive] = useState(null);
  const [insights, setInsights] = useState(null);
  const [tab, setTab] = useState("Validation");
  const [busy, setBusy] = useState(null); // 'validate' | 'clean' | 'eda' | 'predictive' | 'insights' | null
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const d = await getDataset(id);
      setDataset(d);
      if (d.has_validation_report) {
        getValidation(id).then((r) => setValidation(r.validation_report));
      }
      if (d.has_cleaning_summary) {
        getCleaning(id).then((r) => setCleaning(r.cleaning_summary));
      }
      if (d.has_eda_report) {
        getEda(id).then((r) => setEda(r.eda_report));
      }
      if (d.has_predictive_report) {
        getPredictive(id).then((r) => setPredictive(r.predictive_report));
      }
      if (d.has_insights_report) {
        getInsights(id).then((r) => setInsights(r.insights_report));
      }
    } catch {
      setError("Could not load this dataset.");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const runValidate = async () => {
    setBusy("validate");
    setError("");
    try {
      const res = await validateDataset(id);
      setDataset(res.dataset);
      setValidation(res.validation_report);
      setTab("Validation");
    } catch {
      setError("Validation failed to run.");
    } finally {
      setBusy(null);
    }
  };

  const runClean = async () => {
    setBusy("clean");
    setError("");
    try {
      const res = await cleanDataset(id);
      setDataset(res.dataset);
      setCleaning(res.cleaning_summary);
      setTab("Cleaning");
    } catch (err) {
      setError(err.response?.data?.errors?.[0] || "Cleaning failed to run.");
    } finally {
      setBusy(null);
    }
  };

  const runAnalysis = async () => {
    setBusy("eda");
    setError("");
    try {
      const res = await runEda(id);
      setDataset(res.dataset);
      setEda(res.eda_report);
      setTab("EDA");
    } catch (err) {
      setError(err.response?.data?.errors?.[0] || "Analysis failed to run.");
    } finally {
      setBusy(null);
    }
  };

  const runPredictiveAnalysis = async () => {
    setBusy("predictive");
    setError("");
    try {
      const res = await runPredictive(id);
      setDataset(res.dataset);
      setPredictive(res.predictive_report);
      setTab("Predictive");
    } catch (err) {
      setError(err.response?.data?.errors?.[0] || "Predictive models failed to run.");
    } finally {
      setBusy(null);
    }
  };

  const runInsightsGeneration = async () => {
    setBusy("insights");
    setError("");
    try {
      const res = await runInsights(id);
      setDataset(res.dataset);
      setInsights(res.insights_report);
      setTab("Insights");
    } catch (err) {
      setError(err.response?.data?.errors?.[0] || "Insights failed to generate.");
    } finally {
      setBusy(null);
    }
  };

  if (!dataset) {
    return (
      <AppShell title="Dataset">
        {error ? <p className="text-danger text-sm">{error}</p> : <p className="text-ink-muted text-sm">Loading…</p>}
      </AppShell>
    );
  }

  return (
    <AppShell title={dataset.original_filename}>
      <Link to="/datasets" className="text-sm text-ink-muted hover:text-ink">
        ← All datasets
      </Link>

      <div className="flex items-center justify-between flex-wrap gap-4 mt-4 mb-6">
        <PipelineStepper status={dataset.status} />
        <div className="flex gap-2">
          <button
            onClick={runValidate}
            disabled={busy !== null}
            className="text-sm rounded-lg border border-signal/40 text-signal px-4 py-2 hover:bg-signal/10 disabled:opacity-40 transition-colors"
          >
            {busy === "validate" ? "Validating…" : dataset.has_validation_report ? "Re-run validation" : "Run validation"}
          </button>
          <button
            onClick={runClean}
            disabled={busy !== null || !dataset.has_validation_report}
            title={!dataset.has_validation_report ? "Run validation first" : ""}
            className="text-sm rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
          >
            {busy === "clean" ? "Cleaning…" : dataset.has_cleaning_summary ? "Re-run cleaning" : "Run cleaning"}
          </button>
          <button
            onClick={runAnalysis}
            disabled={busy !== null}
            className="text-sm rounded-lg border border-border text-ink-muted px-4 py-2 hover:text-ink hover:border-signal/40 disabled:opacity-40 transition-colors"
          >
            {busy === "eda" ? "Analyzing…" : dataset.has_eda_report ? "Re-run analysis" : "Run analysis"}
          </button>
          <button
            onClick={runPredictiveAnalysis}
            disabled={busy !== null}
            className="text-sm rounded-lg border border-border text-ink-muted px-4 py-2 hover:text-ink hover:border-signal/40 disabled:opacity-40 transition-colors"
          >
            {busy === "predictive" ? "Training…" : dataset.has_predictive_report ? "Re-run predictive" : "Run predictive"}
          </button>
          <button
            onClick={runInsightsGeneration}
            disabled={busy !== null}
            className="text-sm rounded-lg border border-border text-ink-muted px-4 py-2 hover:text-ink hover:border-signal/40 disabled:opacity-40 transition-colors"
          >
            {busy === "insights" ? "Generating…" : dataset.has_insights_report ? "Re-run insights" : "Run insights"}
          </button>
        </div>
      </div>

      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <MetaStat label="Rows" value={dataset.row_count?.toLocaleString()} />
        <MetaStat label="Columns" value={dataset.column_count} />
        <MetaStat label="File size" value={`${(dataset.file_size_bytes / 1024).toFixed(1)} KB`} />
        <MetaStat label="Uploaded" value={new Date(dataset.uploaded_at).toLocaleDateString()} />
      </div>

      <div className="flex gap-1 border-b border-border mb-6">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-signal text-ink"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Validation" && <ValidationTab report={validation} onRun={runValidate} busy={busy === "validate"} />}
      {tab === "Cleaning" && (
        <CleaningTab
          summary={cleaning}
          canClean={dataset.has_validation_report}
          onRun={runClean}
          busy={busy === "clean"}
        />
      )}
      {tab === "Data Preview" && <PreviewTab datasetId={id} hasCleaned={dataset.has_cleaning_summary} />}
      {tab === "EDA" && (
        <EdaTab report={eda} canRun={true} onRun={runAnalysis} busy={busy === "eda"} />
      )}
      {tab === "Predictive" && (
        <PredictiveTab report={predictive} onRun={runPredictiveAnalysis} busy={busy === "predictive"} />
      )}
      {tab === "Insights" && (
        <InsightsTab report={insights} onRun={runInsightsGeneration} busy={busy === "insights"} />
      )}
      {tab === "Reports" && (
        <ReportsTab datasetId={id} filenameHint={dataset.original_filename.replace(/\.[^/.]+$/, "")} />
      )}
      {tab === "Ask INSIGHT IQ" && <AskTab datasetId={id} />}
    </AppShell>
  );
}

function MetaStat({ label, value }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-ink-muted text-xs">{label}</p>
      <p className="font-mono text-ink mt-1">{value}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------

function StatusPill({ status }) {
  const map = {
    passed: { label: "Passed", cls: "bg-signal/10 text-signal border-signal/30" },
    passed_with_warnings: { label: "Passed with warnings", cls: "bg-amber/10 text-amber border-amber/30" },
    failed: { label: "Failed", cls: "bg-danger/10 text-danger border-danger/30" },
  };
  const info = map[status] || map.passed_with_warnings;
  return (
    <span className={`text-xs font-mono px-2.5 py-1 rounded-full border ${info.cls}`}>
      {info.label}
    </span>
  );
}

function ValidationTab({ report, onRun, busy }) {
  if (!report) {
    return (
      <EmptyState
        title="No validation run yet"
        detail="Check for missing columns, duplicate records, invalid values, and data types before cleaning."
        actionLabel={busy ? "Validating…" : "Run validation"}
        onAction={onRun}
        busy={busy}
      />
    );
  }

  const schemaEntries = Object.entries(report.schema_match || {});

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <StatusPill status={report.overall_status} />
        <span className="text-ink-muted text-sm">
          {report.row_count.toLocaleString()} rows · {report.column_count} columns
        </span>
      </div>

      {(report.errors?.length > 0 || report.warnings?.length > 0) && (
        <div className="grid sm:grid-cols-2 gap-4">
          {report.errors?.length > 0 && (
            <MessageList title="Errors" items={report.errors} tone="danger" />
          )}
          {report.warnings?.length > 0 && (
            <MessageList title="Warnings" items={report.warnings} tone="amber" />
          )}
        </div>
      )}

      <div>
        <h3 className="font-display font-semibold text-ink mb-1">Retail schema detection</h3>
        <p className="text-ink-muted text-sm mb-3">
          Which standard retail-sales fields INSIGHT IQ recognized in your columns.
        </p>
        <div className="rounded-xl border border-border bg-surface overflow-hidden">
          <div className="grid grid-cols-2 sm:grid-cols-3">
            {schemaEntries.map(([field, col]) => (
              <div key={field} className="px-4 py-3 border-b border-r border-border">
                <p className="text-xs text-ink-muted font-mono">{field}</p>
                <p className={`text-sm mt-0.5 ${col ? "text-ink" : "text-ink-muted/50"}`}>
                  {col || "not detected"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-ink-muted text-xs">Duplicate rows</p>
          <p className="font-mono text-ink text-lg mt-1">
            {report.duplicate_rows.count} ({report.duplicate_rows.percentage}%)
          </p>
        </div>
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-ink-muted text-xs">Duplicate key values</p>
          <p className="font-mono text-ink text-lg mt-1">
            {report.duplicate_key ? `${report.duplicate_key.duplicate_count} in ${report.duplicate_key.key_column}` : "no key column"}
          </p>
        </div>
      </div>

      <div>
        <h3 className="font-display font-semibold text-ink mb-3">Column-by-column</h3>
        <div className="rounded-xl border border-border bg-surface overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="border-b border-border text-left text-ink-muted">
                <th className="px-4 py-2.5 font-normal">Column</th>
                <th className="px-4 py-2.5 font-normal">Type</th>
                <th className="px-4 py-2.5 font-normal">Missing</th>
                <th className="px-4 py-2.5 font-normal">Unique</th>
                <th className="px-4 py-2.5 font-normal">Issues</th>
              </tr>
            </thead>
            <tbody>
              {report.columns.map((col) => (
                <tr key={col.name} className="border-b border-border last:border-0 align-top">
                  <td className="px-4 py-2.5 text-ink whitespace-nowrap">{col.name}</td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted whitespace-nowrap">
                    {col.inferred_type}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted whitespace-nowrap">
                    {col.missing_percentage}%
                  </td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted whitespace-nowrap">
                    {col.unique_count}
                  </td>
                  <td className="px-4 py-2.5 text-ink-muted">
                    {col.issues.length === 0 ? (
                      <span className="text-signal/70">clean</span>
                    ) : (
                      <ul className="space-y-0.5">
                        {col.issues.map((issue, i) => (
                          <li key={i} className="text-xs">
                            {issue}
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function CleaningTab({ summary, canClean, onRun, busy }) {
  if (!summary) {
    return (
      <EmptyState
        title="No cleaning run yet"
        detail={
          canClean
            ? "Fill missing values, remove duplicates, cap outliers, and standardize formatting."
            : "Run validation first — cleaning uses the validation report to decide what to fix."
        }
        actionLabel={busy ? "Cleaning…" : "Run cleaning"}
        onAction={canClean ? onRun : undefined}
        busy={busy}
      />
    );
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetaStat label="Rows before" value={summary.rows_before} />
        <MetaStat label="Rows after" value={summary.rows_after} />
        <MetaStat label="Columns before" value={summary.columns_before} />
        <MetaStat label="Columns after" value={summary.columns_after} />
      </div>

      <div>
        <h3 className="font-display font-semibold text-ink mb-3">What was cleaned</h3>
        <div className="rounded-xl border border-border bg-surface p-4">
          {summary.actions.length === 0 ? (
            <p className="text-ink-muted text-sm">Nothing needed fixing — the data was already clean.</p>
          ) : (
            <ul className="space-y-2">
              {summary.actions.map((action, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink">
                  <span className="text-signal mt-0.5">✓</span>
                  {action}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {Object.keys(summary.missing_values_filled || {}).length > 0 && (
        <SummaryTable
          title="Missing values filled"
          rows={Object.entries(summary.missing_values_filled).map(([col, info]) => [
            col,
            `${info.count} filled`,
            `${info.method} → ${info.fill_value}`,
          ])}
          headers={["Column", "Count", "Fill method"]}
        />
      )}

      {Object.keys(summary.outliers_capped || {}).length > 0 && (
        <SummaryTable
          title="Outliers capped (IQR bounds)"
          rows={Object.entries(summary.outliers_capped).map(([col, count]) => [col, `${count} value(s)`])}
          headers={["Column", "Capped"]}
        />
      )}

      {Object.keys(summary.type_conversions || {}).length > 0 && (
        <SummaryTable
          title="Type corrections"
          rows={Object.entries(summary.type_conversions).map(([col, conv]) => [col, conv])}
          headers={["Column", "Conversion"]}
        />
      )}

      {summary.dropped_columns?.length > 0 && (
        <div>
          <h3 className="font-display font-semibold text-ink mb-2">Dropped columns</h3>
          <p className="text-ink-muted text-sm">
            {summary.dropped_columns.join(", ")} — removed for being mostly empty.
          </p>
        </div>
      )}
    </div>
  );
}

function SummaryTable({ title, rows, headers }) {
  return (
    <div>
      <h3 className="font-display font-semibold text-ink mb-3">{title}</h3>
      <div className="rounded-xl border border-border bg-surface overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-ink-muted">
              {headers.map((h) => (
                <th key={h} className="px-4 py-2.5 font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className={`px-4 py-2.5 ${j === 0 ? "text-ink" : "font-mono text-ink-muted"}`}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PreviewTab({ datasetId, hasCleaned }) {
  const [stage, setStage] = useState(hasCleaned ? "cleaned" : "raw");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    previewDataset(datasetId, stage)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [datasetId, stage]);

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <TabPill active={stage === "raw"} onClick={() => setStage("raw")}>
          Raw
        </TabPill>
        <TabPill active={stage === "cleaned"} onClick={() => setStage("cleaned")} disabled={!hasCleaned}>
          Cleaned
        </TabPill>
      </div>

      {loading && <p className="text-ink-muted text-sm">Loading preview…</p>}

      {!loading && data && (
        <>
          <p className="text-ink-muted text-xs mb-3 font-mono">
            Showing {data.shown_rows} of {data.total_rows.toLocaleString()} rows
          </p>
          <div className="rounded-xl border border-border bg-surface overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-ink-muted">
                  {data.columns.map((c) => (
                    <th key={c} className="px-4 py-2.5 font-normal whitespace-nowrap">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    {data.columns.map((c) => (
                      <td key={c} className="px-4 py-2.5 text-ink-muted whitespace-nowrap font-mono">
                        {row[c] === null ? <span className="text-ink-muted/40">—</span> : String(row[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function TabPill({ children, active, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`text-xs font-mono px-3 py-1.5 rounded-full border transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${
        active ? "border-signal/40 text-signal bg-signal/10" : "border-border text-ink-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

function MessageList({ title, items, tone }) {
  const cls = tone === "danger" ? "border-danger/30 bg-danger/5 text-danger" : "border-amber/30 bg-amber/5 text-amber";
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <p className="text-xs font-mono uppercase tracking-wide mb-2 opacity-80">{title}</p>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-sm">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function EmptyState({ title, detail, actionLabel, onAction, busy }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-8 text-center max-w-md">
      <p className="text-ink font-medium mb-1">{title}</p>
      <p className="text-ink-muted text-sm mb-4">{detail}</p>
      {onAction && (
        <button
          onClick={onAction}
          disabled={busy}
          className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90 disabled:opacity-50"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
