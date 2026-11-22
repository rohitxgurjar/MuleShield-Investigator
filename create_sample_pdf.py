from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

file_path = "sample_data/test_statement.pdf"

doc = SimpleDocTemplate(file_path, pagesize=A4)
styles = getSampleStyleSheet()
elements = []

elements.append(Paragraph(
    "SYNTHETIC BANK STATEMENT",
    styles["Title"]
))
elements.append(Spacer(1, 15))

elements.append(Paragraph(
    "Account ID: ACC001 | Dataset: Synthetic / Test Only",
    styles["Normal"]
))
elements.append(Spacer(1, 20))

data = [
    ["Date", "Debit", "Credit", "Balance", "Counterparty", "UTR", "Narration"],
    ["20-11-2026 10:00", "0", "50000", "50000", "ACC001", "UTR001", "Victim transfer"],
    ["20-11-2026 10:05", "50000", "0", "0", "ACC002", "UTR002", "UPI transfer"],
    ["20-11-2026 10:15", "0", "20000", "20000", "ACC003", "UTR003", "UPI credit"],
    ["20-11-2026 10:30", "10000", "0", "10000", "ACC004", "UTR004", "UPI transfer"],
]

table = Table(data, repeatRows=1)

table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("PADDING", (0, 0), (-1, -1), 6),
]))

elements.append(table)
doc.build(elements)

print("Synthetic PDF created:", file_path)
