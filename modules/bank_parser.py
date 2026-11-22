import re
from pathlib import Path

import pandas as pd
import pymupdf


STANDARD_COLUMNS = [
    "timestamp", "account_id", "transaction_type", "amount",
    "debit", "credit", "balance", "counterparty", "utr",
    "narration", "source_file"
]

COLUMN_ALIASES = {
    "timestamp": ["date", "transaction date", "datetime", "timestamp"],
    "debit": ["debit", "withdrawal", "withdrawals", "dr"],
    "credit": ["credit", "deposit", "deposits", "cr"],
    "balance": ["balance", "closing balance"],
    "account_id": ["account id", "account number", "account no"],
    "counterparty": ["counterparty", "beneficiary", "recipient", "from/to"],
    "utr": ["utr", "reference number", "transaction id", "ref no"],
    "narration": ["narration", "description", "remarks", "particulars"]
}


def clean_column_name(name):
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def find_column(columns, field):
    aliases = COLUMN_ALIASES.get(field, [])
    cleaned = {clean_column_name(col): col for col in columns}

    for alias in aliases:
        if alias in cleaned:
            return cleaned[alias]

    return None


def parse_number(value):
    if pd.isna(value):
        return 0.0

    value = str(value).replace(",", "").replace("₹", "").strip()
    value = re.sub(r"[^\d.\-]", "", value)

    try:
        return float(value) if value else 0.0
    except ValueError:
        return 0.0


def normalise_transactions(raw_df, source_file, account_id=None):
    df = raw_df.copy()
    result = pd.DataFrame(index=df.index)

    for field in STANDARD_COLUMNS:
        source_column = find_column(df.columns, field)

        if source_column:
            result[field] = df[source_column]
        else:
            result[field] = None

    result["timestamp"] = pd.to_datetime(
        result["timestamp"], errors="coerce", dayfirst=True
    )

    if account_id:
        result["account_id"] = account_id

    result["account_id"] = result["account_id"].fillna("UNKNOWN")
    result["account_id"] = result["account_id"].replace("", "UNKNOWN")

    result["debit"] = result["debit"].apply(parse_number)
    result["credit"] = result["credit"].apply(parse_number)
    result["balance"] = result["balance"].apply(parse_number)

    result["amount"] = result.apply(
        lambda row: row["debit"] if row["debit"] > 0 else row["credit"],
        axis=1
    )

    result["transaction_type"] = result.apply(
        lambda row: "DEBIT" if row["debit"] > 0 else
        ("CREDIT" if row["credit"] > 0 else "UNKNOWN"),
        axis=1
    )

    result["source_file"] = str(source_file)

    return result[STANDARD_COLUMNS]


def parse_excel(file_path, account_id=None):
    raw_df = pd.read_excel(file_path)

    if raw_df.empty:
        raise ValueError("Excel statement contains no transactions.")

    return normalise_transactions(
        raw_df, source_file=file_path, account_id=account_id
    )


def parse_pdf(file_path, account_id=None):
    extracted_tables = []
    detected_account_id = account_id

    with pymupdf.open(file_path) as document:
        for page in document:
            page_text = page.get_text()

            if not detected_account_id:
                match = re.search(
                    r"Account\s*(?:ID|Number|No\.?)\s*[:\-]\s*([A-Z0-9]+)",
                    page_text,
                    re.IGNORECASE
                )

                if match:
                    detected_account_id = match.group(1)

            for table in page.find_tables().tables:
                data = table.extract()

                if data and len(data) > 1:
                    headers = [
                        str(h).strip() if h else f"column_{i}"
                        for i, h in enumerate(data[0])
                    ]

                    extracted_tables.append(
                        pd.DataFrame(data[1:], columns=headers)
                    )

    if not extracted_tables:
        raise ValueError(
            "No transaction table detected. Scanned PDFs require OCR."
        )

    raw_df = pd.concat(extracted_tables, ignore_index=True)

    return normalise_transactions(
        raw_df,
        source_file=file_path,
        account_id=detected_account_id
    )


def parse_statement(file_path, account_id=None):
    extension = Path(file_path).suffix.lower()

    if extension in [".xlsx", ".xls"]:
        return parse_excel(file_path, account_id)

    if extension == ".pdf":
        return parse_pdf(file_path, account_id)

    raise ValueError(f"Unsupported file format: {extension}")


def parse_multiple_statements(file_paths):
    all_transactions = []
    errors = []

    for file_path in file_paths:
        try:
            all_transactions.append(parse_statement(file_path))
        except Exception as error:
            errors.append({
                "file": str(file_path),
                "error": str(error)
            })

    if not all_transactions:
        raise ValueError(f"No statements parsed successfully: {errors}")

    combined = pd.concat(all_transactions, ignore_index=True)
    combined = combined.sort_values("timestamp", na_position="last")

    return combined.reset_index(drop=True
)
def detect_duplicate_transactions(df):
    """
    Identify duplicate records using transaction identifiers
    and transaction details.
    """
    result = df.copy()

    result["is_duplicate"] = False

    # Use UTR as the primary identifier when available.
    has_utr = (
        result["utr"].notna()
        & result["utr"].astype(str).str.strip().ne("")
        & result["utr"].astype(str).str.strip().ne("UNKNOWN")
    )

    utr_duplicates = (
        has_utr
        & result.duplicated(
            subset=["account_id", "utr"],
            keep="first"
        )
    )

    # Fallback for transactions without a usable UTR.
    no_utr = ~has_utr

    fallback_duplicates = (
        no_utr
        & result.duplicated(
            subset=[
                "account_id", "timestamp", "amount",
                "transaction_type", "counterparty"
            ],
            keep="first"
        )
    )

    result.loc[utr_duplicates | fallback_duplicates, "is_duplicate"] = True

    return result
