import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const PALETTE = ["#2DD4A7", "#F4B740", "#5B8DEF", "#F0576B", "#A78BFA"];

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

export default function PredictiveTab({ report, onRun, busy }) {
  if (!report) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center max-w-md">
        <p className="text-ink font-medium mb-1">No predictive models run yet</p>
        <p className="text-ink-muted text-sm mb-4">
          Train four models on this dataset: sales prediction, revenue forecasting, customer
          segmentation, and churn prediction.
        </p>
        <button
          onClick={onRun}
          disabled={busy}
          className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90 disabled:opacity-50"
        >
          {busy ? "Training models…" : "Run predictive analytics"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <span className="text-xs font-mono px-2.5 py-1 rounded-full border border-signal/30 bg-signal/10 text-signal">
        modeled from {report.source_stage} data
      </span>

      <ModuleSection title="1. Sales Prediction" subtitle="Predicts per-order revenue from quantity, price, region, category, and date.">
        <SalesPrediction data={report.sales_prediction} />
      </ModuleSection>

      <ModuleSection title="2. Revenue Forecasting" subtitle="Projects monthly revenue forward using a trend line fit on historical months.">
        <RevenueForecast data={report.revenue_forecast} />
      </ModuleSection>

      <ModuleSection title="3. Customer Segmentation" subtitle="Groups customers by spend, order frequency, and recency using KMeans clustering.">
        <CustomerSegmentation data={report.customer_segmentation} />
      </ModuleSection>

      <ModuleSection title="4. Customer Churn Prediction" subtitle="Flags customers likely to stop purchasing, based on their own purchase cadence.">
        <ChurnPrediction data={report.churn_prediction} />
      </ModuleSection>
    </div>
  );
}

function ModuleSection({ title, subtitle, children }) {
  return (
    <div>
      <h3 className="font-display font-semibold text-ink mb-1">{title}</h3>
      <p className="text-ink-muted text-sm mb-4">{subtitle}</p>
      {children}
    </div>
  );
}

function Unavailable({ reason }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <p className="text-ink-muted text-sm">{reason}</p>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-ink-muted text-xs">{label}</p>
      <p className="font-mono text-ink text-lg mt-1">{value}</p>
    </div>
  );
}

function ChartCard({ title, children, height = 256 }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      {title && <p className="text-sm text-ink-muted mb-3">{title}</p>}
      <div style={{ height }}>{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 1. Sales Prediction
// ---------------------------------------------------------------------------

function SalesPrediction({ data }) {
  if (!data.available) return <Unavailable reason={data.reason} />;

  const importanceRows = data.feature_importance.map((f) => ({ name: f.feature, value: f.importance }));
  const sampleRows = data.sample_predictions.map((s, i) => ({ index: `#${i + 1}`, actual: s.actual, predicted: s.predicted }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard label="R² score" value={data.metrics.r2} />
        <MetricCard label="MAE" value={data.metrics.mae?.toLocaleString()} />
        <MetricCard label="RMSE" value={data.metrics.rmse?.toLocaleString()} />
        <MetricCard label="Rows used" value={data.rows_used} />
      </div>
      <p className="text-xs text-ink-muted font-mono">
        {data.model} · validated via {data.validation_method}
      </p>
      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title="Feature importance">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={importanceRows} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" {...axisProps} />
              <YAxis type="category" dataKey="name" {...axisProps} width={110} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="value" fill="#2DD4A7" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Actual vs predicted (sample)">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sampleRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="index" {...axisProps} />
              <YAxis {...axisProps} />
              <Tooltip {...tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 11, color: "var(--color-ink-muted)" }} />
              <Bar dataKey="actual" fill="#5B8DEF" radius={[3, 3, 0, 0]} />
              <Bar dataKey="predicted" fill="#2DD4A7" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2. Revenue Forecast
// ---------------------------------------------------------------------------

function RevenueForecast({ data }) {
  if (!data.available) return <Unavailable reason={data.reason} />;

  const rows = [
    ...data.history.x.map((x, i) => ({ x, history: data.history.y[i], forecast: null })),
    ...data.forecast.x.map((x, i) => ({
      x,
      history: null,
      forecast: i === 0 ? data.history.y[data.history.y.length - 1] : data.forecast.y[i - 1] ?? data.forecast.y[i],
    })),
  ];
  // fix first forecast point to bridge cleanly from last history point
  if (rows.length > data.history.x.length) {
    rows[data.history.x.length].forecast = data.forecast.y[0];
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <MetricCard label="R² (on history)" value={data.metrics.r2_on_history} />
        <MetricCard label="MAE (on history)" value={data.metrics.mae_on_history?.toLocaleString()} />
        <MetricCard label="Months of history" value={data.months_of_history} />
      </div>
      {data.note && (
        <div className="rounded-xl border border-amber/30 bg-amber/5 p-3">
          <p className="text-xs text-amber">{data.note}</p>
        </div>
      )}
      <ChartCard title={`${data.method} — solid: actual, dashed: forecast`} height={288}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey="x" {...axisProps} />
            <YAxis {...axisProps} />
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 11, color: "var(--color-ink-muted)" }} />
            <Line type="monotone" dataKey="history" name="Actual" stroke="#2DD4A7" strokeWidth={2} dot={{ r: 3 }} connectNulls />
            <Line
              type="monotone"
              dataKey="forecast"
              name="Forecast"
              stroke="#F4B740"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={{ r: 3 }}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 3. Customer Segmentation
// ---------------------------------------------------------------------------

function CustomerSegmentation({ data }) {
  if (!data.available) return <Unavailable reason={data.reason} />;

  const clusterColor = (cluster) => PALETTE[cluster % PALETTE.length];

  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-3 gap-4">
        {data.segments.map((seg) => (
          <div key={seg.cluster} className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: clusterColor(seg.cluster) }} />
              <p className="text-ink font-medium text-sm">{seg.label}</p>
            </div>
            <p className="text-ink-muted text-xs">{seg.size} customers</p>
            <div className="mt-2 space-y-1 text-xs text-ink-muted">
              <p>Avg revenue: <span className="text-ink font-mono">₹{seg.avg_total_revenue?.toLocaleString()}</span></p>
              <p>Avg orders: <span className="text-ink font-mono">{seg.avg_order_count}</span></p>
              {seg.avg_recency_days != null && (
                <p>Avg recency: <span className="text-ink font-mono">{seg.avg_recency_days} days</span></p>
              )}
            </div>
          </div>
        ))}
      </div>
      {data.silhouette_score != null && (
        <p className="text-xs text-ink-muted font-mono">
          Silhouette score: {data.silhouette_score} (higher = more distinct clusters, max 1.0)
        </p>
      )}
      <ChartCard title="Customers by revenue and order frequency" height={320}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis type="number" dataKey="total_revenue" name="Total revenue" {...axisProps} />
            <YAxis type="number" dataKey="order_count" name="Orders" {...axisProps} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 11, color: "var(--color-ink-muted)" }} />
            {data.segments.map((seg) => (
              <Scatter
                key={seg.cluster}
                name={seg.label}
                data={data.scatter.filter((p) => p.cluster === seg.cluster)}
                fill={clusterColor(seg.cluster)}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 4. Churn Prediction
// ---------------------------------------------------------------------------

function ChurnPrediction({ data }) {
  if (!data.available) return <Unavailable reason={data.reason} />;

  const importanceRows = data.feature_importance.map((f) => ({ name: f.feature, value: f.importance }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        <MetricCard label="Churn rate" value={`${data.churn_rate_percent}%`} />
        <MetricCard label="Accuracy" value={data.metrics.accuracy} />
        <MetricCard label="Precision" value={data.metrics.precision} />
        <MetricCard label="Recall" value={data.metrics.recall} />
        <MetricCard label="F1 score" value={data.metrics.f1} />
      </div>

      <div className="rounded-xl border border-border bg-surface p-4">
        <p className="text-xs text-ink-muted">{data.churn_definition}</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title="Feature importance">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={importanceRows} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" {...axisProps} />
              <YAxis type="category" dataKey="name" {...axisProps} width={130} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="value" fill="#F0576B" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-sm text-ink-muted mb-3">Confusion matrix</p>
          <ConfusionMatrix matrix={data.confusion_matrix} />
        </div>
      </div>

      <div>
        <p className="text-sm text-ink-muted mb-3">Highest churn-risk customers</p>
        <div className="rounded-xl border border-border bg-surface overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-ink-muted">
                <th className="px-4 py-2.5 font-normal">Customer</th>
                <th className="px-4 py-2.5 font-normal">Churn probability</th>
                <th className="px-4 py-2.5 font-normal">Days since last order</th>
                <th className="px-4 py-2.5 font-normal">Total revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.at_risk_customers.map((c) => (
                <tr key={c.customer} className="border-b border-border last:border-0">
                  <td className="px-4 py-2.5 text-ink">{c.customer}</td>
                  <td className="px-4 py-2.5 font-mono text-danger">{(c.churn_probability * 100).toFixed(1)}%</td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted">{c.recency_days}</td>
                  <td className="px-4 py-2.5 font-mono text-ink-muted">
                    {c.total_revenue != null ? `₹${c.total_revenue.toLocaleString()}` : "—"}
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

function ConfusionMatrix({ matrix }) {
  const [[tn, fp], [fn, tp]] = matrix;
  const cellClass = "rounded-lg p-4 text-center";
  return (
    <div className="grid grid-cols-2 gap-2 max-w-xs">
      <div className={`${cellClass} bg-signal/10 border border-signal/20`}>
        <p className="text-ink-muted text-xs mb-1">True Negative</p>
        <p className="font-mono text-ink text-lg">{tn}</p>
      </div>
      <div className={`${cellClass} bg-danger/10 border border-danger/20`}>
        <p className="text-ink-muted text-xs mb-1">False Positive</p>
        <p className="font-mono text-ink text-lg">{fp}</p>
      </div>
      <div className={`${cellClass} bg-danger/10 border border-danger/20`}>
        <p className="text-ink-muted text-xs mb-1">False Negative</p>
        <p className="font-mono text-ink text-lg">{fn}</p>
      </div>
      <div className={`${cellClass} bg-signal/10 border border-signal/20`}>
        <p className="text-ink-muted text-xs mb-1">True Positive</p>
        <p className="font-mono text-ink text-lg">{tp}</p>
      </div>
    </div>
  );
}
