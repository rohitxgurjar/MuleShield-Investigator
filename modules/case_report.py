from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_case_report(
    transactions,
    money_trail,
    alerts,
    indicators,
    output_path="outputs/muleshield_case_report.pdf",
    case_id="MS-SYNTHETIC-001",
):
    """Generate a PDF report from supplied synthetic investigation data."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
    ))

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    def add_table(data, widths=None):
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))

    story.append(Paragraph(
        "MULESHIELD — FINANCIAL INVESTIGATION REPORT",
        styles["ReportTitle"]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"Case ID: {case_id}", styles["Normal"]))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
        styles["Normal"]
    ))
    story.append(Paragraph(
        "Dataset: Synthetic demonstration data only",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # Transaction summary
    story.append(Paragraph("1. Transaction Summary", styles["Heading2"]))

    total_debit = transactions["debit"].sum()
    total_credit = transactions["credit"].sum()

    add_table([
        ["Metric", "Value"],
        ["Total transactions", str(len(transactions))],
        ["Unique accounts", str(transactions["account_id"].nunique())],
        ["Total debit", f"INR {total_debit:,.2f}"],
        ["Total credit", f"INR {total_credit:,.2f}"],
    ], [75 * mm, 85 * mm])

    # Money trail
    story.append(Paragraph("2. UTR Money Trail", styles["Heading2"]))

    trail_data = [[
        "UTR", "Sender", "Receiver", "Amount", "Status"
    ]]

    for _, row in money_trail.iterrows():
        trail_data.append([
            str(row["utr"]),
            str(row["sender_account"]),
            str(row["receiver_account"]),
            f"{row['amount_sent']:,.2f}",
            str(row["status"]),
        ])

    if len(trail_data) == 1:
        trail_data.append(["No records", "-", "-", "-", "-"])

    add_table(trail_data, [28 * mm, 30 * mm, 30 * mm, 35 * mm, 37 * mm])

    # Alerts
    story.append(Paragraph("3. Suspicious Pattern Alerts", styles["Heading2"]))

    alert_data = [["Account", "Pattern", "Risk", "Details"]]

    for _, row in alerts.iterrows():
        alert_data.append([
            str(row["account_id"]),
            str(row["pattern"]),
            str(row["risk_level"]),
            str(row["details"]),
        ])

    if len(alert_data) == 1:
        alert_data.append(["No alerts", "-", "-", "-"])

    add_table(alert_data, [25 * mm, 42 * mm, 20 * mm, 73 * mm])

    # Digital indicators
    story.append(Paragraph("4. Domain and IP Indicators", styles["Heading2"]))

    indicator_data = [["Indicator", "Type", "Validation", "Enrichment"]]

    for _, row in indicators.iterrows():
        indicator_data.append([
            str(row["indicator"]),
            str(row["type"]),
            str(row["status"]),
            str(row["intelligence_status"]),
        ])

    if len(indicator_data) == 1:
        indicator_data.append(["No indicators", "-", "-", "-"])

    add_table(indicator_data, [55 * mm, 25 * mm, 35 * mm, 45 * mm])

    # Limitations
    story.append(Paragraph("5. Limitations and Disclaimer", styles["Heading2"]))
    story.append(Paragraph(
        "This report is generated from synthetic demonstration data. "
        "Automated alerts are indicators requiring human review and do not "
        "establish criminal activity. Domain/IP validation does not establish "
        "maliciousness. No bank account access, freezing, subscriber lookup, "
        "or active network scanning was performed.",
        styles["Normal"]
    ))

    doc.build(story)

    return str(output)
