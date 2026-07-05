const TONE_STYLES = {
  positive: { border: "border-signal/30", bg: "bg-signal/5", badge: "text-signal bg-signal/10 border-signal/20", icon: "▲" },
  warning: { border: "border-danger/30", bg: "bg-danger/5", badge: "text-danger bg-danger/10 border-danger/20", icon: "▼" },
  opportunity: { border: "border-amber/30", bg: "bg-amber/5", badge: "text-amber bg-amber/10 border-amber/20", icon: "✦" },
  neutral: { border: "border-border", bg: "bg-surface", badge: "text-ink-muted bg-surface-raised border-border", icon: "●" },
};

export default function InsightsTab({ report, onRun, busy }) {
  if (!report) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center max-w-md">
        <p className="text-ink font-medium mb-1">No insights generated yet</p>
        <p className="text-ink-muted text-sm mb-4">
          Turn this dataset's numbers into plain-language findings: revenue trends, top and
          bottom products, regional performance, customer behavior, and more.
        </p>
        <button
          onClick={onRun}
          disabled={busy}
          className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90 disabled:opacity-50"
        >
          {busy ? "Generating…" : "Generate insights"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <span className="text-xs font-mono px-2.5 py-1 rounded-full border border-signal/30 bg-signal/10 text-signal">
        generated from {report.source_stage} data
      </span>

      <div className="grid md:grid-cols-2 gap-4">
        {report.insights.map((insight, i) => (
          <InsightCard key={i} insight={insight} />
        ))}
      </div>

      {report.unavailable_notes?.length > 0 && (
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-xs font-mono uppercase tracking-wide text-ink-muted mb-2">
            Not enough data for
          </p>
          <ul className="space-y-1">
            {report.unavailable_notes.map((note, i) => (
              <li key={i} className="text-sm text-ink-muted">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function InsightCard({ insight }) {
  const style = TONE_STYLES[insight.tone] || TONE_STYLES.neutral;
  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-5`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-xs font-mono px-2 py-0.5 rounded-full border ${style.badge}`}>
          {style.icon} {insight.category}
        </span>
      </div>
      <p className="text-ink font-medium text-sm mb-1.5">{insight.title}</p>
      <p className="text-ink-muted text-sm leading-relaxed">{insight.message}</p>
    </div>
  );
}
