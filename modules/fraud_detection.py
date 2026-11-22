import pandas as pd


def detect_mule_patterns(transactions):
    """
    Identify suspicious transaction patterns for investigation.
    These are indicators, not proof of fraud.
    """

    required = [
        "account_id", "transaction_type", "amount",
        "timestamp", "balance", "counterparty"
    ]

    missing = [col for col in required if col not in transactions.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = transactions.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce")

    df["transaction_type"] = (
        df["transaction_type"].fillna("").astype(str).str.upper().str.strip()
    )

    alerts = []

    for account, group in df.groupby("account_id"):
        group = group.sort_values("timestamp")

        credits = group[group["transaction_type"] == "CREDIT"]
        debits = group[group["transaction_type"] == "DEBIT"]

        total_credit = credits["amount"].sum()
        total_debit = debits["amount"].sum()

        # Pattern 1: High outgoing transaction count
        if len(debits) >= 3:
            alerts.append({
                "account_id": account,
                "pattern": "MULTIPLE_OUTGOING_TRANSFERS",
                "details": f"{len(debits)} debit transactions detected",
                "risk_level": "MEDIUM"
            })

        # Pattern 2: Incoming funds followed by rapid outgoing transfers
        for _, credit in credits.iterrows():
            later_debits = debits[
                (debits["timestamp"] > credit["timestamp"])
                & (
                    debits["timestamp"]
                    <= credit["timestamp"] + pd.Timedelta(hours=24)
                )
            ]

            outgoing_total = later_debits["amount"].sum()

            if (
                credit["amount"] > 0
                and outgoing_total >= 0.8 * credit["amount"]
            ):
                alerts.append({
                    "account_id": account,
                    "pattern": "RAPID_FUND_MOVEMENT",
                    "details": (
                        f"₹{outgoing_total:.2f} debited within 24 hours "
                        f"after ₹{credit['amount']:.2f} credit"
                    ),
                    "risk_level": "HIGH"
                })

        # Pattern 3: High outgoing-to-incoming ratio
        if total_credit > 0:
            ratio = total_debit / total_credit

            if ratio >= 0.8:
                alerts.append({
                    "account_id": account,
                    "pattern": "HIGH_OUTGOING_RATIO",
                    "details": f"Outgoing/incoming ratio: {ratio:.2f}",
                    "risk_level": "MEDIUM"
                })

        # Pattern 4: Very low remaining balance after debit
        for _, debit in debits.iterrows():
            if (
                pd.notna(debit["balance"])
                and debit["amount"] > 0
                and debit["balance"] <= 1
            ):
                alerts.append({
                    "account_id": account,
                    "pattern": "BALANCE_DRAIN",
                    "details": (
                        f"₹{debit['amount']:.2f} debit left "
                        f"balance at ₹{debit['balance']:.2f}"
                    ),
                    "risk_level": "HIGH"
                })

    return pd.DataFrame(
        alerts,
        columns=["account_id", "pattern", "details", "risk_level"]
    )
