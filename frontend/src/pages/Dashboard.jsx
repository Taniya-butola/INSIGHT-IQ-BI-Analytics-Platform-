import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../context/AuthContext";
import { listDatasets, getDashboard, getDashboardFilters } from "../api/datasets";
import { ChartCard, RevenueTrendChart, LabeledBarChart, RevenueVsProfitChart } from "./DashboardCharts";

const EMPTY_FILTERS = { region: "", category: "", date_from: "", date_to: "" };

export default function Dashboard() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listDatasets()
      .then((list) => {
        setDatasets(list);
        if (list.length > 0) setSelectedId(list[0].id);
      })
      .catch(() => setDatasets([]));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setFilters(EMPTY_FILTERS);
    getDashboardFilters(selectedId)
      .then((r) => setFilterOptions(r.filters))
      .catch(() => setFilterOptions(null));
  }, [selectedId]);

  const loadDashboard = useCallback(() => {
    if (!selectedId) return;
    setLoading(true);
    setError("");
    getDashboard(selectedId, filters)
      .then(setData)
      .catch(() => setError("Could not load the dashboard for this dataset."))
      .finally(() => setLoading(false));
  }, [selectedId, filters]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const hasActiveFilters = useMemo(
    () => Object.values(filters).some((v) => v),
    [filters]
  );

  if (datasets === null) {
    return (
      <AppShell title="Dashboard">
        <p className="text-ink-muted text-sm">Loading…</p>
      </AppShell>
    );
  }

  if (datasets.length === 0) {
    return (
      <AppShell title="Dashboard">
        <p className="text-ink-muted text-sm mb-6">
          Welcome, <span className="text-ink">{user?.full_name}</span>. Upload a dataset to see
          your business KPIs here.
        </p>
        <div className="rounded-xl border border-signal/30 bg-signal/5 p-6 flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="text-ink font-medium">Upload your first dataset</p>
            <p className="text-ink-muted text-sm mt-1">
              Bring a retail sales CSV or Excel file to start building your dashboard.
            </p>
          </div>
          <Link
            to="/upload"
            className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90 whitespace-nowrap"
          >
            Upload dataset
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="Dashboard">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <label className="text-xs text-ink-muted block mb-1">Dataset</label>
          <select
            value={selectedId || ""}
            onChange={(e) => setSelectedId(Number(e.target.value))}
            className="rounded-lg bg-surface-raised border border-border px-3 py-2 text-sm text-ink outline-none focus:border-signal min-w-[220px]"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename}
              </option>
            ))}
          </select>
        </div>
        <Link to={`/datasets/${selectedId}`} className="text-sm text-signal hover:underline">
          View pipeline & analysis →
        </Link>
      </div>

      {filterOptions && (
        <FilterBar
          filters={filters}
          setFilters={setFilters}
          options={filterOptions}
          hasActiveFilters={hasActiveFilters}
        />
      )}

      {error && <p className="text-danger text-sm mb-4">{error}</p>}
      {loading && <p className="text-ink-muted text-sm mb-4">Loading dashboard…</p>}

      {data && !loading && (
        <div className="space-y-8">
          {data.unavailable_notes?.length > 0 && (
            <div className="rounded-xl border border-amber/30 bg-amber/5 p-4">
              <p className="text-xs font-mono uppercase tracking-wide text-amber mb-2">
                Limited data
              </p>
              <ul className="space-y-1">
                {data.unavailable_notes.map((note, i) => (
                  <li key={i} className="text-sm text-amber">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-semibold text-ink">Business KPIs</h3>
              <span className="text-xs text-ink-muted font-mono">
                {data.row_count.toLocaleString()} rows in view
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <KpiCard label="Total Revenue" value={formatCurrency(data.kpis.total_revenue)} />
              <KpiCard label="Total Orders" value={data.kpis.total_orders?.toLocaleString()} />
              <KpiCard label="Total Customers" value={data.kpis.total_customers?.toLocaleString() ?? "—"} />
              <KpiCard
                label="Profit Margin"
                value={data.kpis.profit_margin_percent != null ? `${data.kpis.profit_margin_percent}%` : "—"}
              />
              <KpiCard label="Avg Order Value" value={formatCurrency(data.kpis.average_order_value)} />
              <KpiCard
                label="Monthly Growth"
                value={data.kpis.monthly_growth_percent != null ? `${data.kpis.monthly_growth_percent}%` : "—"}
                trend={data.kpis.monthly_growth_percent}
              />
            </div>
          </div>

          <div>
            <h3 className="font-display font-semibold text-ink mb-3">Analytics</h3>
            <div className="grid lg:grid-cols-2 gap-6">
              {data.analytics.revenue_trend && (
                <ChartCard title="Revenue trend">
                  <RevenueTrendChart data={data.analytics.revenue_trend} />
                </ChartCard>
              )}
              {data.analytics.regional_sales && (
                <ChartCard title="Regional sales">
                  <LabeledBarChart data={data.analytics.regional_sales} color="#2DD4A7" />
                </ChartCard>
              )}
              {data.analytics.customer_distribution && (
                <ChartCard title="Customer distribution (top spenders)">
                  <LabeledBarChart data={data.analytics.customer_distribution} color="#5B8DEF" angled />
                </ChartCard>
              )}
              {data.analytics.revenue_vs_profit && (
                <ChartCard title="Revenue vs profit">
                  <RevenueVsProfitChart data={data.analytics.revenue_vs_profit} />
                </ChartCard>
              )}
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {data.analytics.top_selling_products && (
              <ProductTable title="Top selling products" rows={data.analytics.top_selling_products} tone="signal" />
            )}
            {data.analytics.low_performing_products && (
              <ProductTable title="Low performing products" rows={data.analytics.low_performing_products} tone="danger" />
            )}
          </div>

          {data.analytics.inventory_status && (
            <div>
              <h3 className="font-display font-semibold text-ink mb-3">Inventory status</h3>
              <div className="grid sm:grid-cols-3 gap-4 mb-4">
                <KpiCard
                  label="Total units in stock"
                  value={data.analytics.inventory_status.total_units_in_stock?.toLocaleString()}
                />
                <KpiCard label="Low-stock products" value={data.analytics.inventory_status.low_stock_count} />
              </div>
              {data.analytics.inventory_status.low_stock_items.length > 0 && (
                <div className="rounded-xl border border-border bg-surface overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-ink-muted">
                        <th className="px-4 py-2.5 font-normal">Product</th>
                        <th className="px-4 py-2.5 font-normal">Stock remaining</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.analytics.inventory_status.low_stock_items.map((item) => (
                        <tr key={item.name} className="border-b border-border last:border-0">
                          <td className="px-4 py-2.5 text-ink">{item.name}</td>
                          <td className="px-4 py-2.5 font-mono text-danger">{item.stock}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="rounded-xl border border-signal/30 bg-signal/5 p-6 mt-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="font-display font-semibold text-ink mb-1">All 8 phases are live</p>
          <p className="text-ink-muted text-sm">
            Auth, upload, validation, cleaning, analysis, this dashboard, predictive models,
            business insights, downloadable reports, and Ask INSIGHT IQ.
          </p>
        </div>
        {selectedId && (
          <Link
            to={`/datasets/${selectedId}`}
            className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2 text-sm hover:opacity-90 whitespace-nowrap"
          >
            Try Ask INSIGHT IQ →
          </Link>
        )}
      </div>
    </AppShell>
  );
}

function FilterBar({ filters, setFilters, options, hasActiveFilters }) {
  const update = (key) => (e) => setFilters({ ...filters, [key]: e.target.value });

  return (
    <div className="rounded-xl border border-border bg-surface p-4 mb-6 flex items-end gap-4 flex-wrap">
      {options.regions.length > 0 && (
        <FilterSelect label="Region" value={filters.region} onChange={update("region")} options={options.regions} />
      )}
      {options.categories.length > 0 && (
        <FilterSelect
          label="Category"
          value={filters.category}
          onChange={update("category")}
          options={options.categories}
        />
      )}
      {options.date_min && (
        <>
          <DateField label="From" value={filters.date_from} onChange={update("date_from")} min={options.date_min} max={options.date_max} />
          <DateField label="To" value={filters.date_to} onChange={update("date_to")} min={options.date_min} max={options.date_max} />
        </>
      )}
      {hasActiveFilters && (
        <button
          onClick={() => setFilters(EMPTY_FILTERS)}
          className="text-xs text-ink-muted hover:text-danger mb-0.5"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <label className="block">
      <span className="text-xs text-ink-muted block mb-1">{label}</span>
      <select
        value={value}
        onChange={onChange}
        className="rounded-lg bg-surface-raised border border-border px-3 py-1.5 text-sm text-ink outline-none focus:border-signal"
      >
        <option value="">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}

function DateField({ label, value, onChange, min, max }) {
  return (
    <label className="block">
      <span className="text-xs text-ink-muted block mb-1">{label}</span>
      <input
        type="date"
        value={value}
        onChange={onChange}
        min={min}
        max={max}
        className="rounded-lg bg-surface-raised border border-border px-3 py-1.5 text-sm text-ink outline-none focus:border-signal"
      />
    </label>
  );
}

function KpiCard({ label, value, trend }) {
  const trendColor = trend > 0 ? "text-signal" : trend < 0 ? "text-danger" : "text-ink-muted";
  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-panel">
      <p className="text-ink-muted text-xs">{label}</p>
      <p className={`font-mono text-lg mt-2 ${trend !== undefined ? trendColor : "text-ink"}`}>
        {value ?? "—"}
      </p>
    </div>
  );
}

function ProductTable({ title, rows, tone }) {
  const accentClass = tone === "signal" ? "text-signal" : "text-danger";
  return (
    <div>
      <h3 className="font-display font-semibold text-ink mb-3">{title}</h3>
      <div className="rounded-xl border border-border bg-surface overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-ink-muted">
              <th className="px-4 py-2.5 font-normal">Product</th>
              {"revenue" in (rows[0] || {}) && <th className="px-4 py-2.5 font-normal">Revenue</th>}
              {"units_sold" in (rows[0] || {}) && <th className="px-4 py-2.5 font-normal">Units sold</th>}
              {"orders" in (rows[0] || {}) && <th className="px-4 py-2.5 font-normal">Orders</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const nameKey = Object.keys(row).find(
                (k) => !["revenue", "units_sold", "orders"].includes(k)
              );
              return (
                <tr key={i} className="border-b border-border last:border-0">
                  <td className="px-4 py-2.5 text-ink">{row[nameKey]}</td>
                  {"revenue" in row && (
                    <td className={`px-4 py-2.5 font-mono ${accentClass}`}>{formatCurrency(row.revenue)}</td>
                  )}
                  {"units_sold" in row && <td className="px-4 py-2.5 font-mono text-ink-muted">{row.units_sold}</td>}
                  {"orders" in row && <td className="px-4 py-2.5 font-mono text-ink-muted">{row.orders}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatCurrency(value) {
  if (value === null || value === undefined) return "—";
  return `₹${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
