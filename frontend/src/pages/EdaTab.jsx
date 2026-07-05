import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const PALETTE = ["#2DD4A7", "#F4B740", "#5B8DEF", "#F0576B", "#A78BFA", "#34D399", "#FB923C", "#38BDF8"];

const axisProps = {
  tick: { fill: "var(--color-ink-muted)", fontSize: 11 },
  stroke: "var(--color-border)",
};

const tooltipStyle = {
  contentStyle: {
    background: "var(--color-surface-raised)",
    border: "1px solid var(--color-border)",
    borderRadius: 8,
    fontSize: 12,
    color: "var(--color-ink)",
  },
  labelStyle: { color: "var(--color-ink-muted)" },
};

export default function EdaTab({ report, canRun, onRun, busy }) {
  if (!report) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center max-w-md">
        <p className="text-ink font-medium mb-1">No analysis run yet</p>
        <p className="text-ink-muted text-sm mb-4">
          {canRun
            ? "Generate dataset summary, descriptive statistics, correlations, distributions, and charts."
            : "Upload and clean this dataset first for the most reliable analysis — you can still analyze raw data if you'd rather skip cleaning."}
        </p>
        <button
          onClick={onRun}
          disabled={busy}
          className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90 disabled:opacity-50"
        >
          {busy ? "Analyzing…" : "Run analysis"}
        </button>
      </div>
    );
  }

  const { dataset_summary, descriptive_statistics, missing_value_report, correlation_matrix, charts } = report;

  return (
    <div className="space-y-10">
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono px-2.5 py-1 rounded-full border border-signal/30 bg-signal/10 text-signal">
          analyzed from {report.source_stage} data
        </span>
      </div>

      {/* Dataset summary */}
      <div>
        <h3 className="font-display font-semibold text-ink mb-3">Dataset summary</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Stat label="Rows" value={dataset_summary.rows.toLocaleString()} />
          <Stat label="Columns" value={dataset_summary.columns} />
          <Stat label="Numeric fields" value={dataset_summary.numeric_columns.length} />
          <Stat label="Categorical fields" value={dataset_summary.categorical_columns.length} />
          <Stat label="Date fields" value={dataset_summary.date_columns.length} />
          <Stat label="Duplicate rows" value={dataset_summary.duplicate_rows} />
          <Stat label="Memory" value={`${dataset_summary.memory_kb} KB`} />
        </div>
      </div>

      {/* Descriptive statistics */}
      {Object.keys(descriptive_statistics).length > 0 && (
        <div>
          <h3 className="font-display font-semibold text-ink mb-3">Descriptive statistics</h3>
          <div className="rounded-xl border border-border bg-surface overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="border-b border-border text-left text-ink-muted">
                  <th className="px-4 py-2.5 font-normal">Column</th>
                  <th className="px-4 py-2.5 font-normal">Count</th>
                  <th className="px-4 py-2.5 font-normal">Mean</th>
                  <th className="px-4 py-2.5 font-normal">Std Dev</th>
                  <th className="px-4 py-2.5 font-normal">Min</th>
                  <th className="px-4 py-2.5 font-normal">P25</th>
                  <th className="px-4 py-2.5 font-normal">Median</th>
                  <th className="px-4 py-2.5 font-normal">P75</th>
                  <th className="px-4 py-2.5 font-normal">Max</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(descriptive_statistics).map(([col, s]) => (
                  <tr key={col} className="border-b border-border last:border-0">
                    <td className="px-4 py-2.5 text-ink whitespace-nowrap">{col}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.count}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.mean}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.std}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.min}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.p25}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.median}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.p75}</td>
                    <td className="px-4 py-2.5 font-mono text-ink-muted">{s.max}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Correlation matrix */}
      {correlation_matrix && (
        <div>
          <h3 className="font-display font-semibold text-ink mb-1">Correlation matrix</h3>
          <p className="text-ink-muted text-sm mb-3">
            Pearson correlation between numeric fields, from -1 (opposite) to 1 (moves together).
          </p>
          <CorrelationHeatmap matrix={correlation_matrix} />
        </div>
      )}

      {/* Missing value report */}
      <div>
        <h3 className="font-display font-semibold text-ink mb-3">Missing value report</h3>
        <div className="rounded-xl border border-border bg-surface overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-ink-muted">
                <th className="px-4 py-2.5 font-normal">Column</th>
                <th className="px-4 py-2.5 font-normal">Missing</th>
                <th className="px-4 py-2.5 font-normal">Percentage</th>
              </tr>
            </thead>
            <tbody>
              {missing_value_report.map((row) => (
                <tr key={row.column} className="border-b border-border last:border-0">
                  <td className="px-4 py-2.5 text-ink">{row.column}</td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted">{row.missing_count}</td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted">
                    {row.missing_percentage === 0 ? (
                      <span className="text-signal/70">0%</span>
                    ) : (
                      `${row.missing_percentage}%`
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div>
        <h3 className="font-display font-semibold text-ink mb-4">Visualizations</h3>
        <div className="grid lg:grid-cols-2 gap-6">
          {charts.bar && <ChartCard title={charts.bar.title}><BarChartView data={charts.bar} /></ChartCard>}
          {charts.line && <ChartCard title={charts.line.title}><LineChartView data={charts.line} /></ChartCard>}
          {charts.pie && <ChartCard title={charts.pie.title}><PieChartView data={charts.pie} /></ChartCard>}
          {charts.histogram && (
            <ChartCard title={charts.histogram.title}><HistogramView data={charts.histogram} /></ChartCard>
          )}
          {charts.scatter && (
            <ChartCard title={charts.scatter.title}><ScatterChartView data={charts.scatter} /></ChartCard>
          )}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-ink-muted text-xs">{label}</p>
      <p className="font-mono text-ink text-lg mt-1">{value}</p>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-sm text-ink-muted mb-3">{title}</p>
      <div className="h-64">{children}</div>
    </div>
  );
}

function CorrelationHeatmap({ matrix }) {
  const { columns, matrix: rows } = matrix;
  const colorFor = (v) => {
    if (v === null) return "transparent";
    const intensity = Math.min(Math.abs(v), 1);
    return v >= 0
      ? `rgba(45, 212, 167, ${0.12 + intensity * 0.55})`
      : `rgba(240, 87, 107, ${0.12 + intensity * 0.55})`;
  };
  return (
    <div className="rounded-xl border border-border bg-surface overflow-x-auto p-4">
      <table className="text-sm">
        <thead>
          <tr>
            <th className="p-2"></th>
            {columns.map((c) => (
              <th key={c} className="p-2 text-ink-muted font-normal text-xs whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={columns[i]}>
              <th className="p-2 text-ink-muted font-normal text-xs text-left whitespace-nowrap">
                {columns[i]}
              </th>
              {row.map((v, j) => (
                <td
                  key={j}
                  className="p-2 text-center font-mono text-xs text-ink w-16"
                  style={{ backgroundColor: colorFor(v) }}
                >
                  {v ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BarChartView({ data }) {
  const rows = data.categories.map((cat, i) => ({ name: cat, value: data.values[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="name" {...axisProps} interval={0} angle={-20} textAnchor="end" height={50} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="value" fill="#2DD4A7" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function LineChartView({ data }) {
  const rows = data.x.map((x, i) => ({ x, y: data.y[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="x" {...axisProps} tickFormatter={(v) => v.slice(5)} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Line type="monotone" dataKey="y" stroke="#2DD4A7" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function PieChartView({ data }) {
  const rows = data.labels.map((label, i) => ({ name: label, value: data.values[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie data={rows} dataKey="value" nameKey="name" outerRadius={80} label={{ fontSize: 11, fill: "var(--color-ink-muted)" }}>
          {rows.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11, color: "var(--color-ink-muted)" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

function HistogramView({ data }) {
  const rows = data.labels.map((label, i) => ({ name: label, count: data.counts[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="name" {...axisProps} interval={0} angle={-30} textAnchor="end" height={60} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="count" fill="#F4B740" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ScatterChartView({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis type="number" dataKey="x" name={data.x_label} {...axisProps} />
        <YAxis type="number" dataKey="y" name={data.y_label} {...axisProps} />
        <Tooltip cursor={{ strokeDasharray: "3 3" }} {...tooltipStyle} />
        <Scatter data={data.points} fill="#5B8DEF" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
