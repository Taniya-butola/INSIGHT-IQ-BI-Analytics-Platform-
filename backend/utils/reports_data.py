"""
Phase 7 — Report Generation: data assembly.

Reports don't recompute analytics from scratch. They reuse whatever the
dashboard engine (fast, always available) and the predictive/insights
engines (only if the user already ran them) have already produced, and
assemble a single plain-dict "context" per report type. Both the PDF and
XLSX builders consume the exact same context, so the two formats can
never drift apart in content.
"""
from datetime import datetime, timezone

REPORT_TYPES = {
    "executive-summary": "Executive Summary",
    "sales": "Sales Report",
    "customer-analytics": "Customer Analytics Report",
    "financial": "Financial Report",
    "inventory": "Inventory Report",
}


def _top_n(rows, n=10):
    return (rows or [])[:n]


def build_report_context(report_type, dashboard_data, insights_report, predictive_report, dataset_meta):
    """
    dashboard_data: output of utils.dashboard.build_dashboard(df, {})
    insights_report: dataset.insights_report (dict or None)
    predictive_report: dataset.predictive_report (dict or None)
    dataset_meta: {"filename": ..., "row_count": ..., "source_stage": ...}
    """
    base = {
        "report_type": report_type,
        "report_title": REPORT_TYPES[report_type],
        "dataset_filename": dataset_meta["filename"],
        "source_stage": dataset_meta["source_stage"],
        "row_count": dashboard_data["row_count"],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "kpis": dashboard_data["kpis"],
        "notes": list(dashboard_data.get("unavailable_notes", [])),
    }

    builder = _BUILDERS[report_type]
    base.update(builder(dashboard_data, insights_report, predictive_report))
    return base


def _executive_summary(dashboard_data, insights_report, predictive_report):
    analytics = dashboard_data["analytics"]
    highlights = []
    if insights_report:
        highlights = [i["message"] for i in insights_report.get("insights", [])[:5]]
    else:
        highlights = []

    top_product = (analytics.get("top_selling_products") or [None])[0]
    top_region = None
    if analytics.get("regional_sales") and analytics["regional_sales"]["labels"]:
        top_region = {
            "name": analytics["regional_sales"]["labels"][0],
            "value": analytics["regional_sales"]["values"][0],
        }

    predictive_note = None
    if predictive_report:
        churn = predictive_report.get("churn_prediction", {})
        if churn.get("available"):
            predictive_note = (
                f"Predictive model estimates a {churn['churn_rate_percent']}% customer churn rate, "
                f"with {len(churn['at_risk_customers'])} customers flagged as highest-risk."
            )

    return {
        "highlights": highlights,
        "top_product": top_product,
        "top_region": top_region,
        "predictive_note": predictive_note,
        "has_insights": insights_report is not None,
        "has_predictive": predictive_report is not None,
    }


def _sales_report(dashboard_data, insights_report, predictive_report):
    analytics = dashboard_data["analytics"]
    return {
        "revenue_trend": analytics.get("revenue_trend"),
        "regional_sales": analytics.get("regional_sales"),
        "top_products": _top_n(analytics.get("top_selling_products")),
        "low_products": _top_n(analytics.get("low_performing_products")),
    }


def _customer_analytics_report(dashboard_data, insights_report, predictive_report):
    analytics = dashboard_data["analytics"]
    segmentation = None
    churn = None
    if predictive_report:
        seg = predictive_report.get("customer_segmentation", {})
        if seg.get("available"):
            segmentation = seg
        ch = predictive_report.get("churn_prediction", {})
        if ch.get("available"):
            churn = ch

    return {
        "customer_distribution": analytics.get("customer_distribution"),
        "total_customers": dashboard_data["kpis"].get("total_customers"),
        "average_order_value": dashboard_data["kpis"].get("average_order_value"),
        "segmentation": segmentation,
        "churn": churn,
        "predictive_available": predictive_report is not None,
    }


def _financial_report(dashboard_data, insights_report, predictive_report):
    analytics = dashboard_data["analytics"]
    return {
        "revenue_vs_profit": analytics.get("revenue_vs_profit"),
        "profit_margin_percent": dashboard_data["kpis"].get("profit_margin_percent"),
        "total_revenue": dashboard_data["kpis"].get("total_revenue"),
        "average_order_value": dashboard_data["kpis"].get("average_order_value"),
        "monthly_growth_percent": dashboard_data["kpis"].get("monthly_growth_percent"),
    }


def _inventory_report(dashboard_data, insights_report, predictive_report):
    analytics = dashboard_data["analytics"]
    inventory_insight = None
    if insights_report:
        for i in insights_report.get("insights", []):
            if i["category"] == "Inventory Alerts":
                inventory_insight = i["message"]
                break
    return {
        "inventory_status": analytics.get("inventory_status"),
        "inventory_insight": inventory_insight,
    }


_BUILDERS = {
    "executive-summary": _executive_summary,
    "sales": _sales_report,
    "customer-analytics": _customer_analytics_report,
    "financial": _financial_report,
    "inventory": _inventory_report,
}
