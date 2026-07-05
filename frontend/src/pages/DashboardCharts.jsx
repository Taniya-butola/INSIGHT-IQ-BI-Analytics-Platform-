import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

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

export function ChartCard({ title, children }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-sm text-ink-muted mb-3">{title}</p>
      <div className="h-64">{children}</div>
    </div>
  );
}

export function RevenueTrendChart({ data }) {
  const rows = data.x.map((x, i) => ({ x, y: data.y[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="x" {...axisProps} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Line type="monotone" dataKey="y" name="Revenue" stroke="#2DD4A7" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function LabeledBarChart({ data, color = "#2DD4A7", angled = false }) {
  const rows = data.labels.map((label, i) => ({ name: label, value: data.values[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: angled ? 16 : 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis
          dataKey="name"
          {...axisProps}
          interval={0}
          angle={angled ? -25 : 0}
          textAnchor={angled ? "end" : "middle"}
          height={angled ? 55 : 30}
        />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function RevenueVsProfitChart({ data }) {
  const rows = data.x.map((x, i) => ({ x, revenue: data.revenue[i], profit: data.profit[i] }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="x" {...axisProps} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11, color: "var(--color-ink-muted)" }} />
        <Line type="monotone" dataKey="revenue" stroke="#2DD4A7" strokeWidth={2} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="profit" stroke="#F4B740" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
