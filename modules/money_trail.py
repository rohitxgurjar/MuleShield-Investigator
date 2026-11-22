import pandas as pd


def build_money_trail(df):
    required_columns = [
        "timestamp", "account_id", "transaction_type",
        "amount", "utr", "counterparty"
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    transactions = df.copy()

    transactions["utr"] = (
        transactions["utr"].fillna("").astype(str).str.strip()
    )
    transactions["transaction_type"] = (
        transactions["transaction_type"]
        .fillna("").astype(str).str.upper().str.strip()
    )

    transactions = transactions[
        (transactions["utr"] != "")
        & (transactions["utr"].str.lower() != "nan")
    ]

    results = []

    for utr, group in transactions.groupby("utr"):
        debits = group[group["transaction_type"] == "DEBIT"]
        credits = group[group["transaction_type"] == "CREDIT"]

        if len(debits) == 1 and len(credits) == 1:
            debit = debits.iloc[0]
            credit = credits.iloc[0]

            sent = float(debit["amount"])
            received = float(credit["amount"])

            if debit["account_id"] == credit["account_id"]:
                status = "REVIEW_REQUIRED"
            elif abs(sent - received) < 0.01:
                status = "MATCHED"
            else:
                status = "AMOUNT_MISMATCH"

            results.append({
                "utr": utr,
                "sender_account": debit["account_id"],
                "receiver_account": credit["account_id"],
                "amount_sent": sent,
                "amount_received": received,
                "timestamp_sent": debit["timestamp"],
                "timestamp_received": credit["timestamp"],
                "amount_difference": round(sent - received, 2),
                "status": status
            })

        elif len(debits) > 1 or len(credits) > 1:
            results.append({
                "utr": utr,
                "sender_account": ", ".join(debits["account_id"].astype(str)),
                "receiver_account": ", ".join(credits["account_id"].astype(str)),
                "amount_sent": debits["amount"].sum(),
                "amount_received": credits["amount"].sum(),
                "timestamp_sent": None,
                "timestamp_received": None,
                "amount_difference": None,
                "status": "MULTIPLE_CANDIDATES"
            })

        elif len(debits) == 1:
            debit = debits.iloc[0]
            results.append({
                "utr": utr,
                "sender_account": debit["account_id"],
                "receiver_account": debit["counterparty"],
                "amount_sent": debit["amount"],
                "amount_received": 0,
                "timestamp_sent": debit["timestamp"],
                "timestamp_received": None,
                "amount_difference": None,
                "status": "UNMATCHED_DEBIT"
            })

        elif len(credits) == 1:
            credit = credits.iloc[0]
            results.append({
                "utr": utr,
                "sender_account": credit["counterparty"],
                "receiver_account": credit["account_id"],
                "amount_sent": 0,
                "amount_received": credit["amount"],
                "timestamp_sent": None,
                "timestamp_received": credit["timestamp"],
                "amount_difference": None,
                "status": "UNMATCHED_CREDIT"
            })

    return pd.DataFrame(results)
