# INSIGHT IQ — Business Intelligence & Analytics Platform

**All 8 phases complete: Auth, Upload, Validation, Cleaning, EDA, Dashboard, Predictive Analytics, Business Insights, Reports & Ask INSIGHT IQ**

This is real, runnable code — not a mockup — covering:

- User registration, login, logout, and JWT-protected routes
- Profile management (update name/company, change password)
- Dataset upload (CSV/XLSX) with structural validation and metadata capture
- **Data validation**: missing columns, duplicate records, invalid values,
  data type mismatches, per-column issue reports
- **Data cleaning**: missing value imputation, duplicate removal, outlier
  capping (IQR), type correction, text formatting — with a full
  human-readable summary of every action taken
- **Exploratory Data Analysis**: dataset summary, descriptive statistics,
  correlation matrix, missing-value report, feature distributions, and
  five chart types (bar, line, pie, histogram, scatter)
- **Interactive Dashboard**: six business KPIs (revenue, orders,
  customers, profit margin, average order value, monthly growth),
  filterable by region/category/date range, plus revenue trend, regional
  sales, top/low performing products, customer distribution, revenue vs.
  profit, and inventory status — computed live on every filter change
- **Predictive Analytics**: four scikit-learn models — sales prediction
  (RandomForestRegressor), revenue forecasting (linear trend
  regression), customer segmentation (KMeans), and churn prediction
  (RandomForestClassifier) — each reporting accuracy metrics, feature
  importance, and degrading gracefully with a plain-language reason when
  the dataset lacks the columns or row count for a trustworthy model
- **Business Insights**: nine plain-language findings generated from the
  same aggregations as the dashboard — revenue trends, best/worst
  performing products, regional performance, customer purchasing
  behavior, high-value customer concentration, growth opportunities,
  inventory alerts, and seasonal sales trends — each with a tone
  (positive/warning/opportunity/neutral) and a real number behind it
- **Report Generation**: five downloadable report types (Executive
  Summary, Sales, Customer Analytics, Financial, Inventory), each in PDF
  and Excel, generated on demand from the same dashboard/insights/
  predictive data — the Excel version also ships a raw data sheet as a
  named Excel Table plus a couple of genuinely live formulas
- **Ask INSIGHT IQ**: a conversational assistant (Claude, via the
  Anthropic API) that answers questions about a specific dataset using
  its actual computed KPIs, insights, and predictive results — not the
  raw file alone — with persisted per-dataset chat history
- A dashboard shell with sidebar navigation, dark/light mode, and a
  per-dataset pipeline view (Uploaded → Validated → Cleaned → Analyzed)

Everything below has been tested end-to-end: registration → login →
protected requests → file upload → parsing → validation → cleaning →
EDA → dashboard KPIs/charts → filtering → predictive models → business
insights → all 10 report combinations (5 types × PDF/Excel, including
formula verification with LibreOffice recalculation) → Ask INSIGHT IQ
(context assembly, conversation history, and every failure path — no
API key, empty question, service errors) → graceful degradation on
small/incomplete datasets → before/after preview → listing → deletion,
and a production frontend build.

---

## Stack

| Layer    | Choice |
|----------|--------|
| Frontend | React 18, Vite, React Router, Tailwind CSS, Axios, Recharts |
| Backend  | Flask 3, Flask-JWT-Extended, Flask-Bcrypt, SQLAlchemy |
| Database | MySQL (production) or SQLite (zero-setup local dev) |
| Data     | Pandas / NumPy / openpyxl for reading, cleaning, and analyzing files |
| ML       | scikit-learn (RandomForest, KMeans, LinearRegression) |
| Reports  | reportlab (PDF), openpyxl (Excel) |
| AI       | Anthropic API (Claude) for Ask INSIGHT IQ |

---

## Project structure

```
insight-iq/
├── backend/
│   ├── app.py                 # Flask app factory
│   ├── config.py               # Env-driven configuration
│   ├── extensions.py           # db, bcrypt, jwt singletons
│   ├── models.py               # User, Dataset, ChatMessage (SQLAlchemy)
│   ├── schema.sql               # MySQL DDL (optional, manual setup)
│   ├── routes/
│   │   ├── auth.py             # /api/auth/*
│   │   ├── profile.py          # /api/profile*
│   │   ├── datasets.py         # /api/datasets* (upload, validate, clean, preview, dashboard, reports)
│   │   └── chat.py             # /api/datasets/<id>/ask, /messages (Phase 8)
│   ├── utils/
│   │   ├── validators.py       # registration/login/file validation
│   │   ├── schema_hints.py     # retail column-name recognition
│   │   ├── validation.py       # Phase 2 — validation engine
│   │   ├── cleaning.py         # Phase 2 — cleaning engine
│   │   ├── eda.py              # Phase 3 — exploratory analysis engine
│   │   ├── dashboard.py        # Phase 4 — KPIs, analytics, filtering
│   │   ├── predictive.py       # Phase 5 — sales/forecast/segmentation/churn models
│   │   ├── insights.py         # Phase 6 — plain-language business insights
│   │   ├── reports_data.py     # Phase 7 — shared context assembler for reports
│   │   ├── reports_pdf.py      # Phase 7 — PDF report builder (reportlab)
│   │   ├── reports_xlsx.py     # Phase 7 — Excel report builder (openpyxl)
│   │   ├── ask_context.py      # Phase 8 — dataset context assembler for the AI assistant
│   │   └── anthropic_client.py # Phase 8 — thin Anthropic Messages API wrapper
│   ├── assets/fonts/            # Bundled DejaVu Sans (Unicode-safe PDF text, e.g. ₹)
│   ├── uploads/                 # uploaded + cleaned files land here (gitignored)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── pages/               # Login, Register, Dashboard (KPIs & filters),
    │   │                        # DashboardCharts, Upload, Datasets,
    │   │                        # DatasetDetail (validation/cleaning/preview/EDA/predictive/insights/reports/ask tabs),
    │   │                        # EdaTab (charts), PredictiveTab (models), InsightsTab (findings),
    │   │                        # ReportsTab (downloads), AskTab (chat), Profile
    │   ├── components/          # AppShell, Sidebar, Topbar, AuthLayout, PulseLine,
    │   │                        # PipelineStepper, ui.jsx
    │   ├── context/              # AuthContext, ThemeContext
    │   └── api/                  # axios client + endpoint wrappers
    ├── tailwind.config.js        # design tokens (colors, fonts)
    └── .env.example
```

---

## Running it locally

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Default .env uses SQLite — no database install needed to try it out.
# For MySQL instead, edit DATABASE_URL in .env, e.g.:
#   DATABASE_URL=mysql+pymysql://insightiq_user:password@localhost:3306/insightiq
# and create the DB first:
#   mysql -u root -p -e "CREATE DATABASE insightiq CHARACTER SET utf8mb4;"
#
# To use Ask INSIGHT IQ (Phase 8), also set ANTHROPIC_API_KEY in .env —
# get one at https://console.anthropic.com/settings/keys. Everything else
# in the app works fine without it; only the Ask tab needs it.

python3 app.py
# → running on http://localhost:5000
```

Tables are created automatically on first run (`db.create_all()`). If you'd
rather create them by hand against MySQL, run `schema.sql`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_URL=http://localhost:5000/api
npm run dev
# → running on http://localhost:5173
```

Open `http://localhost:5173`, register an account, and upload a `.csv` or
`.xlsx` retail sales file to see it parsed and listed.

---

## API reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|--------------|
| POST | `/api/auth/register` | – | Create account, returns JWT |
| POST | `/api/auth/login` | – | Log in, returns JWT |
| POST | `/api/auth/logout` | ✓ | Stateless logout |
| GET  | `/api/auth/me` | ✓ | Current user |
| GET  | `/api/profile` | ✓ | Get profile |
| PUT  | `/api/profile` | ✓ | Update name/company |
| PUT  | `/api/profile/password` | ✓ | Change password |
| POST | `/api/datasets/upload` | ✓ | Upload CSV/XLSX (multipart `file`) |
| GET  | `/api/datasets` | ✓ | List your datasets |
| GET  | `/api/datasets/<id>` | ✓ | Get one dataset |
| DELETE | `/api/datasets/<id>` | ✓ | Delete a dataset |
| POST | `/api/datasets/<id>/validate` | ✓ | Run validation, store report |
| GET  | `/api/datasets/<id>/validation` | ✓ | Get the stored validation report |
| POST | `/api/datasets/<id>/clean` | ✓ | Run cleaning (requires validation first) |
| GET  | `/api/datasets/<id>/cleaning` | ✓ | Get the stored cleaning summary |
| GET  | `/api/datasets/<id>/preview?stage=raw\|cleaned` | ✓ | Row preview (first 25 rows) |
| POST | `/api/datasets/<id>/eda` | ✓ | Run EDA (uses cleaned data if available) |
| GET  | `/api/datasets/<id>/eda` | ✓ | Get the stored EDA report |
| GET  | `/api/datasets/<id>/dashboard/filters` | ✓ | Available region/category/date filter values |
| GET  | `/api/datasets/<id>/dashboard?region=&category=&date_from=&date_to=` | ✓ | KPIs + analytics, computed live with optional filters |
| POST | `/api/datasets/<id>/predictive` | ✓ | Run all 4 ML models |
| GET  | `/api/datasets/<id>/predictive` | ✓ | Get the stored predictive report |
| POST | `/api/datasets/<id>/insights` | ✓ | Generate plain-language business insights |
| GET  | `/api/datasets/<id>/insights` | ✓ | Get the stored insights report |
| GET  | `/api/datasets/report-types` | ✓ | List the 5 available report types |
| GET  | `/api/datasets/<id>/reports/<type>?format=pdf\|xlsx` | ✓ | Download a report (type: executive-summary, sales, customer-analytics, financial, inventory) |
| POST | `/api/datasets/<id>/ask` | ✓ | Ask a question about this dataset (requires `ANTHROPIC_API_KEY`) |
| GET  | `/api/datasets/<id>/messages` | ✓ | Get this dataset's chat history |
| DELETE | `/api/datasets/<id>/messages` | ✓ | Clear this dataset's chat history |

Send the JWT as `Authorization: Bearer <token>` on protected routes.

---

## Security notes

- Passwords are hashed with bcrypt, never stored in plain text.
- Registration enforces an 8+ character password with upper, lower, and
  numeric characters; email format is validated server-side.
- Uploaded files are renamed to a random UUID on disk (the original name
  is kept only as metadata) and stored per-user, avoiding path collisions
  and traversal.
- Only `.csv` and `.xlsx` extensions are accepted, and the file is opened
  with Pandas server-side to confirm it actually parses as tabular data
  before being accepted — not just a trusted file extension check.
- All dataset and profile routes require a valid JWT and are scoped to
  the authenticated user's own `user_id`.

Full request validation, duplicate/outlier detection, and a cleaning
pipeline are the explicit scope of **Phase 2**.

---

## How validation & cleaning work

**Validation** (`backend/utils/validation.py`) re-reads the original
uploaded file and reports, without changing anything:
- Structural issues: unnamed/duplicate columns, empty file
- Retail schema recognition: fuzzy-matches columns against expected
  fields (order id, date, customer, product, category, region, quantity,
  unit price, revenue, profit) so later dashboard phases know what's
  available
- Duplicate full rows, and duplicate values in a detected order-id column
- Per column: missing value count, inferred type, unique values, and
  issues such as unparseable dates, non-numeric text, negative amounts,
  and statistical outliers (IQR method)

**Cleaning** (`backend/utils/cleaning.py`) takes the raw data and applies
conservative, explainable fixes, writing the result to a separate
`_cleaned.csv` file so the original upload is never overwritten:
- Removes exact duplicate rows and duplicate order-ids
- Drops columns that are mostly empty (≥60% missing)
- Converts currency-formatted text (`"3,499"`, `"$499"`) to numbers, and
  text dates to a standardized `YYYY-MM-DD` format
- Fills missing numeric values with the column median, missing
  categorical values with the column mode
- **Caps** (rather than deletes) statistical outliers to the IQR bounds,
  so no real sales are silently discarded
- Trims whitespace and title-cases categorical text (region, product,
  category, customer)

Every action is logged into a `cleaning_summary` with before/after row
and column counts, so the UI can show exactly what changed and why.

**Exploratory Data Analysis** (`backend/utils/eda.py`) runs on the cleaned
file when one exists, falling back to the raw upload otherwise, and never
mutates data — it only computes and reports:
- Dataset summary: row/column counts, which columns are numeric,
  categorical, or dates, duplicate rows, memory footprint
- Descriptive statistics (count, mean, std dev, min/25/50/75/max) for
  every numeric column — order/invoice IDs are excluded since they're
  identifiers, not measures
- A Pearson correlation matrix across numeric fields
- A missing-value report per column
- Feature distributions: histogram bins for numeric columns, top values
  for categorical columns
- Five ready-to-render charts built from the detected retail schema:
  revenue by region/category (bar), revenue over time (line), category
  share (pie), a numeric distribution (histogram), and quantity vs.
  revenue (scatter) — each falls back to sensible generic columns if the
  retail-specific ones aren't present

The frontend renders all five chart types with Recharts, plus a
correlation heatmap and statistics tables, on the dataset detail page's
"EDA" tab.

**Interactive Dashboard** (`backend/utils/dashboard.py`) computes fresh
on every request — nothing is persisted, so filters apply live without
needing to store every combination:
- Six KPIs: total revenue, total orders, total customers, profit margin,
  average order value, and month-over-month revenue growth
- Filtering by region, category, and date range, all applied to the
  dataframe before any KPI or chart is computed
- Analytics: monthly revenue trend, revenue by region, top and bottom
  performing products (by revenue and units sold), customer distribution
  by spend, revenue vs. profit over time, and inventory status (total
  stock, low-stock alerts) when a stock/inventory column is detected
- Every KPI and chart that depends on a column INSIGHT IQ couldn't find
  (e.g. no profit column) returns `null` with a plain-language note
  instead of guessing a number — the frontend surfaces these as a
  "Limited data" banner rather than hiding the gap

The frontend's main Dashboard page lets you pick a dataset, filter it,
and see KPI cards, four charts, product tables, and inventory status all
update together — the same building blocks the "Ask INSIGHT IQ" and
report phases will reuse later.

**Predictive Analytics** (`backend/utils/predictive.py`) runs four
independent scikit-learn models on the cleaned dataset (falling back to
raw), each returning `{"available": false, "reason": "..."}` instead of
a number when the data can't support it:

- **Sales Prediction** — a `RandomForestRegressor` predicts per-order
  revenue from quantity, unit price, region, category, and order
  month/day-of-week. Reports R², MAE, RMSE, and feature importance.
  Uses a held-out 25% test set when there are ≥30 rows, otherwise trains
  on the full sample and says so.
- **Revenue Forecasting** — fits a `LinearRegression` trend line on
  monthly revenue history and extrapolates 3 months forward. If the
  historical trend is declining steeply enough that the raw projection
  goes negative, forecasted months are floored at 0 with an explicit
  note explaining why, rather than showing a fabricated positive number
  or a silent zero.
- **Customer Segmentation** — aggregates each customer's total revenue,
  order count, average order value, and recency, standardizes them, and
  runs `KMeans` (3 clusters if ≥9 customers, else 2). Clusters are
  labeled by their own characteristics (highest revenue → "High-Value
  Customers", highest recency → "At-Risk Customers") rather than fixed
  IDs, and a silhouette score reports how distinct the segments actually
  are.
- **Customer Churn Prediction** — labels a customer "churned" using a
  *relative* cutoff (the 70th percentile of recency across all
  customers in that dataset) rather than a fixed day count, so it adapts
  to any business's actual purchase cadence. A `RandomForestClassifier`
  then predicts churn from spend, order frequency, tenure, and average
  days between orders, reporting accuracy/precision/recall/F1, a
  confusion matrix, feature importance, and the highest-risk customers
  by predicted probability.

Every module needs a minimum amount of data to run responsibly (e.g. 10+
rows for sales prediction, 6+ customers for segmentation, 10+ customers
for churn) — below that threshold it explains what's missing instead of
producing an unreliable model.

**Business Insights** (`backend/utils/insights.py`) turns the same
aggregations used elsewhere in the app into short, plain-language
sentences with real numbers, not templated filler:
- **Revenue trend** — month-over-month change, e.g. "Revenue grew 12.3%
  in March 2026, moving from ₹40,000 to ₹44,920."
- **Best/worst-selling products** — which product led on revenue, and
  which lagged, with a concrete recommendation for the laggard
- **Regional performance** — leading vs. lagging region by revenue share
- **Customer purchasing behavior** — repeat-purchase rate and average
  order value
- **High-value customers** — top-customer contribution and what share of
  revenue the top 20% of customers represent
- **Growth opportunities** — a category or region with a high average
  order value but below-median order count, i.e. an under-promoted
  segment worth pushing harder
- **Inventory alerts** — which products are below the low-stock
  threshold, or a positive note when none are
- **Seasonal trends** — which month was the peak and which was the low,
  worded as a planning cue for inventory and staffing

Each of the nine generators returns nothing (with a logged reason, e.g.
"No region column detected") rather than writing a sentence around a
guessed number when the dataset can't support that particular insight —
the same honesty principle as validation, cleaning, dashboard, and
predictive analytics.

**Report Generation** (`backend/utils/reports_data.py`,
`reports_pdf.py`, `reports_xlsx.py`) produces five report types, each in
PDF and Excel, entirely on demand — nothing is stored:

- **Executive Summary** — KPIs, top business-insight highlights, top
  product/region, and a churn-risk note if predictive analytics has run
- **Sales Report** — revenue trend, regional sales, top and low
  performing products
- **Customer Analytics Report** — top customers by revenue, customer
  segments and churn risk if predictive analytics has already run
- **Financial Report** — revenue, profit margin, average order value,
  monthly growth, and revenue vs. profit over time
- **Inventory Report** — stock levels and low-stock alerts

Reports reuse the dashboard engine's aggregations directly (so the
numbers in a report always match what you'd see on the Dashboard page)
and pull in the insights/predictive reports only if you've already
generated them — otherwise that section says so explicitly rather than
silently omitting it or blocking the whole report.

Two implementation details worth knowing about:
- **PDFs bundle their own font.** reportlab's built-in Helvetica can't
  render the Rupee sign (₹) — it shows up as a black box. Rather than
  reformatting every currency string to "Rs.", the app bundles DejaVu
  Sans (`backend/assets/fonts/`, permissively licensed, included) and
  registers it as the document font, so PDFs render correctly regardless
  of what fonts happen to be installed on the machine running the
  backend.
- **Excel reports ship a raw "Data" sheet** (the actual cleaned
  transaction rows, as a named Excel Table) alongside a "Summary" sheet.
  Most Summary figures are written as values so they always match the
  PDF version of the same report, but Total Revenue also gets a
  `(verify, live formula)` cell using a structured reference like
  `=SUM(sales_data[Revenue])` — a genuine formula that recalculates if
  you edit the Data sheet, verified against LibreOffice's recalculation
  engine to confirm it always matches the reported value exactly.

**Ask INSIGHT IQ** (`backend/utils/ask_context.py`, `anthropic_client.py`,
`routes/chat.py`) is a conversational assistant backed by the Anthropic
API, scoped to one dataset at a time:

- **It never sees the raw file.** Context is built from the same
  condensed numbers the rest of the app already trusts — dashboard KPIs,
  business insights (if generated), predictive results (if run), and a
  5-row sample for grounding on formatting/values — plus a system prompt
  that instructs the model to answer only from that context and say so
  plainly when something isn't covered, rather than guess.
- **Conversation history is persisted per dataset** (`ChatMessage`
  model), so leaving and coming back keeps the thread; the last 20
  messages are sent back to the model on each new question so follow-ups
  ("what about the worst one?") work.
- **Every failure mode has a specific message**, not a generic 500: no
  API key configured, an invalid/rejected key, rate limiting, a timeout,
  or an empty question — each returns something the user can actually
  act on.
- The feature is fully optional. Without `ANTHROPIC_API_KEY` set, every
  other part of the app works exactly the same; only the Ask tab
  explains what's missing and how to fix it.

## Design system

The UI uses a dark "analytics terminal" palette by default (deep navy
`#0B1220` base, signal-teal `#2DD4A7` accent, amber `#F4B740` for
secondary emphasis) with a light mode toggle, `Space Grotesk` for
headings, `Inter` for body text, and `JetBrains Mono` for data figures.
Tokens live in `frontend/tailwind.config.js` and
`frontend/src/styles/index.css` — change them there to reskin the app.

---

## Status

All 8 phases from the original spec are complete: authentication and
dataset upload, validation and cleaning, exploratory data analysis, the
interactive dashboard, predictive analytics, business insights, report
generation, and Ask INSIGHT IQ. Each phase was built, tested end-to-end
against real (and deliberately messy) sample data, and cleaned up before
being handed over — see the section for each phase above for exactly
what was verified.

Natural next steps beyond the original spec, if useful: the Admin Panel
mentioned in the original brief (manage users, monitor platform-wide
usage) wasn't part of the 8 phases and hasn't been built; streaming
responses for Ask INSIGHT IQ instead of a single request/response;
and background job processing (Celery/RQ) if predictive analytics needs
to run on datasets much larger than this demo scale.
