"""
Phase 7 — PDF report builder.

Renders the context dict from reports_data.py into a formatted PDF using
reportlab. One shared visual theme and a handful of layout helpers are
reused across all five report types so they feel like one product.
"""
import io
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# Register a bundled Unicode-capable font (DejaVu Sans) instead of relying on
# reportlab's built-in Helvetica, whose WinAnsi encoding can't render currency
# symbols like the Rupee sign (₹) — those would otherwise show up as solid
# black boxes. Bundling the font also keeps rendering identical across
# whatever OS this backend is deployed on.
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
_REGULAR_FONT = "DejaVuSans"
_BOLD_FONT = "DejaVuSans-Bold"

pdfmetrics.registerFont(TTFont(_REGULAR_FONT, os.path.join(_FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont(_BOLD_FONT, os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")))

NAVY = colors.HexColor("#101728")
TEAL = colors.HexColor("#0F9E7A")
MUTED = colors.HexColor("#5B6478")
DANGER = colors.HexColor("#B4243C")
LIGHT_ROW = colors.HexColor("#F5F7FB")
BORDER = colors.HexColor("#E2E8F3")

_styles = getSampleStyleSheet()
for _style_name in ("Title", "Normal", "Heading1", "Heading2", "Heading3", "BodyText"):
    _styles[_style_name].fontName = _REGULAR_FONT
_styles.add(ParagraphStyle("ReportTitle", parent=_styles["Title"], fontName=_BOLD_FONT, textColor=NAVY, fontSize=22, spaceAfter=4))
_styles.add(ParagraphStyle("ReportMeta", parent=_styles["Normal"], textColor=MUTED, fontSize=9, spaceAfter=2))
_styles.add(ParagraphStyle("SectionHeading", parent=_styles["Heading2"], fontName=_BOLD_FONT, textColor=TEAL, fontSize=13, spaceBefore=14, spaceAfter=6))
_styles.add(ParagraphStyle("Body", parent=_styles["Normal"], fontSize=10, leading=14, textColor=NAVY))
_styles.add(ParagraphStyle("MutedBody", parent=_styles["Normal"], fontSize=9.5, leading=13, textColor=MUTED))
_styles.add(ParagraphStyle("InsightBullet", parent=_styles["Normal"], fontSize=10, leading=14, textColor=NAVY, leftIndent=12, bulletIndent=0))


def _header(context):
    story = [
        Paragraph("INSIGHT IQ", ParagraphStyle("Brand", parent=_styles["Normal"], textColor=TEAL, fontSize=10, fontName=_BOLD_FONT)),
        Paragraph(context["report_title"], _styles["ReportTitle"]),
        Paragraph(f"Dataset: {context['dataset_filename']} &nbsp;&middot;&nbsp; {context['row_count']:,} rows ({context['source_stage']} data)", _styles["ReportMeta"]),
        Paragraph(f"Generated {context['generated_at']}", _styles["ReportMeta"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=BORDER),
        Spacer(1, 10),
    ]
    return story


def _section(title):
    return [Paragraph(title, _styles["SectionHeading"])]


def _money(value):
    if value is None:
        return "—"
    return f"₹{value:,.0f}"


def _kpi_grid(kpis):
    def fmt_pct(v):
        return f"{v}%" if v is not None else "—"

    rows = [
        ["Total Revenue", _money(kpis.get("total_revenue")), "Total Orders", f"{kpis.get('total_orders'):,}" if kpis.get("total_orders") is not None else "—"],
        ["Total Customers", f"{kpis.get('total_customers'):,}" if kpis.get("total_customers") is not None else "—", "Avg Order Value", _money(kpis.get("average_order_value"))],
        ["Profit Margin", fmt_pct(kpis.get("profit_margin_percent")), "Monthly Growth", fmt_pct(kpis.get("monthly_growth_percent"))],
    ]
    table = Table(rows, colWidths=[100, 80, 100, 80], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), _REGULAR_FONT),
                ("FONTNAME", (0, 0), (0, -1), _BOLD_FONT),
                ("FONTNAME", (2, 0), (2, -1), _BOLD_FONT),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
            ]
        )
    )
    return table


def _data_table(headers, rows, col_widths=None):
    data = [headers] + rows
    table = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), _BOLD_FONT),
        ("FONTNAME", (0, 1), (-1, -1), _REGULAR_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
        ("TEXTCOLOR", (0, 1), (-1, -1), NAVY),
    ]
    for i in range(1, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_ROW))
    table.setStyle(TableStyle(style))
    return table


def _unavailable(text):
    return Paragraph(f"<i>{text}</i>", _styles["MutedBody"])


def _bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{item}", _styles["InsightBullet"]) for item in items]


# ---------------------------------------------------------------------------
# Per-report-type story builders
# ---------------------------------------------------------------------------


def _build_executive_summary(context):
    story = []
    story += _section("Key Business Metrics")
    story.append(_kpi_grid(context["kpis"]))
    story.append(Spacer(1, 4))

    story += _section("Highlights")
    if context["has_insights"] and context["highlights"]:
        story += _bullets(context["highlights"])
    else:
        story.append(_unavailable("Run Business Insights on this dataset to populate highlights here."))

    story += _section("Top Performers")
    lines = []
    if context["top_product"]:
        keys = list(context["top_product"].keys())
        name_key = keys[0]
        lines.append(f"Top product: <b>{context['top_product'][name_key]}</b>")
    if context["top_region"]:
        lines.append(f"Top region: <b>{context['top_region']['name']}</b> ({_money(context['top_region']['value'])})")
    if lines:
        story.append(Paragraph("<br/>".join(lines), _styles["Body"]))
    else:
        story.append(_unavailable("Product or region columns were not detected in this dataset."))

    if context["predictive_note"]:
        story += _section("Predictive Outlook")
        story.append(Paragraph(context["predictive_note"], _styles["Body"]))
    elif not context["has_predictive"]:
        story += _section("Predictive Outlook")
        story.append(_unavailable("Run Predictive Analytics on this dataset to include churn risk here."))

    return story


def _build_sales_report(context):
    story = []
    story += _section("Revenue Trend")
    trend = context["revenue_trend"]
    if trend:
        rows = [[x, _money(y)] for x, y in zip(trend["x"], trend["y"])]
        story.append(_data_table(["Month", "Revenue"], rows, col_widths=[200, 150]))
    else:
        story.append(_unavailable("No order date or revenue column detected — revenue trend unavailable."))

    story += _section("Regional Sales")
    regional = context["regional_sales"]
    if regional:
        rows = [[label, _money(v)] for label, v in zip(regional["labels"], regional["values"])]
        story.append(_data_table(["Region", "Revenue"], rows, col_widths=[200, 150]))
    else:
        story.append(_unavailable("No region column detected — regional breakdown unavailable."))

    story += _section("Top Selling Products")
    if context["top_products"]:
        keys = list(context["top_products"][0].keys())
        name_key = keys[0]
        rows = [
            [str(p[name_key])] + [_money(p[k]) if k == "revenue" else str(p[k]) for k in keys[1:]]
            for p in context["top_products"]
        ]
        story.append(_data_table(["Product"] + [k.replace("_", " ").title() for k in keys[1:]], rows))
    else:
        story.append(_unavailable("No product column detected — product performance unavailable."))

    story += _section("Low Performing Products")
    if context["low_products"]:
        keys = list(context["low_products"][0].keys())
        name_key = keys[0]
        rows = [
            [str(p[name_key])] + [_money(p[k]) if k == "revenue" else str(p[k]) for k in keys[1:]]
            for p in context["low_products"]
        ]
        story.append(_data_table(["Product"] + [k.replace("_", " ").title() for k in keys[1:]], rows))
    else:
        story.append(_unavailable("No product column detected — product performance unavailable."))

    return story


def _build_customer_analytics_report(context):
    story = []
    story += _section("Customer Overview")
    rows = [
        ["Total Customers", f"{context['total_customers']:,}" if context["total_customers"] is not None else "—"],
        ["Average Order Value", _money(context["average_order_value"])],
    ]
    story.append(_data_table(["Metric", "Value"], rows, col_widths=[220, 150]))

    story += _section("Top Customers by Revenue")
    dist = context["customer_distribution"]
    if dist:
        rows = [[label, _money(v)] for label, v in zip(dist["labels"], dist["values"])]
        story.append(_data_table(["Customer", "Total Revenue"], rows, col_widths=[220, 150]))
    else:
        story.append(_unavailable("No customer column detected — customer ranking unavailable."))

    story += _section("Customer Segments")
    if context["segmentation"]:
        rows = [
            [s["label"], str(s["size"]), _money(s["avg_total_revenue"]), str(s["avg_order_count"])]
            for s in context["segmentation"]["segments"]
        ]
        story.append(_data_table(["Segment", "Customers", "Avg Revenue", "Avg Orders"], rows))
    elif not context["predictive_available"]:
        story.append(_unavailable("Run Predictive Analytics on this dataset to include customer segments here."))
    else:
        story.append(_unavailable("Not enough distinct customers in this dataset to segment."))

    story += _section("Churn Risk")
    if context["churn"]:
        churn = context["churn"]
        story.append(Paragraph(f"Estimated churn rate: <b>{churn['churn_rate_percent']}%</b>", _styles["Body"]))
        story.append(Spacer(1, 4))
        rows = [
            [c["customer"], f"{c['churn_probability'] * 100:.1f}%", str(c["recency_days"])]
            for c in churn["at_risk_customers"][:10]
        ]
        story.append(_data_table(["Customer", "Churn Probability", "Days Since Last Order"], rows))
    elif not context["predictive_available"]:
        story.append(_unavailable("Run Predictive Analytics on this dataset to include churn risk here."))
    else:
        story.append(_unavailable("Not enough purchase history in this dataset to estimate churn."))

    return story


def _build_financial_report(context):
    story = []
    story += _section("Financial Summary")
    rows = [
        ["Total Revenue", _money(context["total_revenue"])],
        [
            "Profit Margin",
            f"{context['profit_margin_percent']}%" if context["profit_margin_percent"] is not None else "Not available — no profit column detected",
        ],
        ["Average Order Value", _money(context["average_order_value"])],
        [
            "Monthly Growth",
            f"{context['monthly_growth_percent']}%" if context["monthly_growth_percent"] is not None else "Not available — need order dates",
        ],
    ]
    story.append(_data_table(["Metric", "Value"], rows, col_widths=[220, 260]))

    story += _section("Revenue vs. Profit")
    rvp = context["revenue_vs_profit"]
    if rvp:
        rows = [[x, _money(r), _money(p)] for x, r, p in zip(rvp["x"], rvp["revenue"], rvp["profit"])]
        story.append(_data_table(["Month", "Revenue", "Profit"], rows))
    else:
        story.append(_unavailable("No profit column and/or order date detected — revenue vs. profit unavailable."))

    return story


def _build_inventory_report(context):
    story = []
    inv = context["inventory_status"]
    story += _section("Inventory Overview")
    if inv:
        rows = [
            ["Total Units In Stock", f"{inv['total_units_in_stock']:,}"],
            ["Low-Stock Products", str(inv["low_stock_count"])],
        ]
        story.append(_data_table(["Metric", "Value"], rows, col_widths=[220, 150]))

        story += _section("Low Stock Items")
        if inv["low_stock_items"]:
            rows = [[item["name"], str(item["stock"])] for item in inv["low_stock_items"]]
            story.append(_data_table(["Product", "Stock Remaining"], rows, col_widths=[300, 150]))
        else:
            story.append(Paragraph("No products are below the low-stock threshold.", _styles["Body"]))
    else:
        story.append(_unavailable("No stock/inventory column detected in this dataset."))

    if context.get("inventory_insight"):
        story += _section("Note")
        story.append(Paragraph(context["inventory_insight"], _styles["Body"]))

    return story


_BUILDERS = {
    "executive-summary": _build_executive_summary,
    "sales": _build_sales_report,
    "customer-analytics": _build_customer_analytics_report,
    "financial": _build_financial_report,
    "inventory": _build_inventory_report,
}


def build_pdf(context: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=context["report_title"],
    )

    story = _header(context)
    story += _BUILDERS[context["report_type"]](context)

    if context.get("notes"):
        story += _section("Data Notes")
        story += _bullets(context["notes"])

    doc.build(story)
    return buffer.getvalue()
