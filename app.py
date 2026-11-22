import streamlit as st
import pandas as pd
import tempfile
import os

from modules.bank_parser import parse_multiple_statements
from modules.money_trail import build_money_trail
from modules.network_graph import (
    build_account_graph,
    get_account_summary,
    find_money_path,
)
from modules.fraud_detection import detect_mule_patterns
from modules.threat_intelligence import analyse_indicators
from modules.case_report import generate_case_report

st.set_page_config(
    page_title="MuleShield Investigator",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ MuleShield Investigator")
st.subheader("AI-Assisted Financial Crime Analysis & Money-Trail Investigation")
st.caption("Financial Investigation Platform | Research Prototype")

st.warning(
    "Prototype for investigative support only. "
    "Alerts are indicators, not proof of criminal activity."
)

# Sidebar
st.sidebar.title("Investigation Workspace")

uploaded_files = st.sidebar.file_uploader(
    "Upload bank statements",
    type=["pdf", "xlsx", "xls"],
    accept_multiple_files=True,
)

analyse_button = st.sidebar.button(
    "Analyse Statements",
    type="primary",
)

if analyse_button:
    if not uploaded_files:
        st.error("Please upload at least one bank statement.")
    else:
        with st.spinner("Analysing uploaded statements..."):
            temp_paths = []

            try:
                for uploaded_file in uploaded_files:
                    suffix = os.path.splitext(uploaded_file.name)[1]

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix
                    ) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_paths.append(temp_file.name)

                transactions = parse_multiple_statements(temp_paths)

                if transactions.empty:
                    st.error("No transactions found in uploaded files.")
                    st.stop()

                st.session_state["transactions"] = transactions
                st.session_state["trail"] = build_money_trail(transactions)
                st.session_state["alerts"] = detect_mule_patterns(
                    transactions
                )
                st.session_state["graph"] = build_account_graph(
                    transactions
                )
                st.success("Statement analysis completed!")

            except Exception as error:
                st.error(f"Analysis failed: {error}")

            finally:
                for path in temp_paths:
                    if os.path.exists(path):
                        os.remove(path)

# Main dashboard
if "transactions" in st.session_state:

    transactions = st.session_state["transactions"]
    trail = st.session_state["trail"]
    alerts = st.session_state["alerts"]
    graph = st.session_state["graph"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview",
        "Transactions",
        "Money Trail",
        "Mule Detection",
        "Threat Intelligence",
    ])

    # Overview
    with tab1:
        st.header("Investigation Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Transactions", len(transactions))
        col2.metric("Accounts", transactions["account_id"].nunique())
        col3.metric("Money Trail Records", len(trail))
        col4.metric("Detection Alerts", len(alerts))

        st.subheader("Account Network")

        if graph.number_of_nodes() > 0:
            summary = get_account_summary(graph)
            st.dataframe(summary, use_container_width=True)

            st.subheader("Network Connections")

            edges = [
                {
                    "Sender": source,
                    "Receiver": target,
                    "Amount": data["total_amount"],
                    "UTRs": ", ".join(data["utrs"]),
                }
                for source, target, data in graph.edges(data=True)
            ]

            if edges:
                st.dataframe(pd.DataFrame(edges), use_container_width=True)
        else:
            st.info("No matched account connections found.")

    # Transactions
    with tab2:
        st.header("Normalized Bank Transactions")
        st.dataframe(transactions, use_container_width=True)

        st.download_button(
            "Download Transactions CSV",
            transactions.to_csv(index=False),
            file_name="muleshield_transactions.csv",
            mime="text/csv",
        )

    # Money Trail
    with tab3:
        st.header("UTR-Based Money Trail")
        st.dataframe(trail, use_container_width=True)

        source = st.text_input("Source account", "ACC001")
        target = st.text_input("Target account", "ACC002")

        if st.button("Find Money Path"):
            result = find_money_path(graph, source, target)
            st.json(result)

    # Mule Detection
    with tab4:
        st.header("Mule Account Pattern Detection")

        if alerts.empty:
            st.success("No patterns detected.")
        else:
            st.dataframe(alerts, use_container_width=True)

            st.download_button(
                "Download Detection Alerts",
                alerts.to_csv(index=False),
                file_name="muleshield_alerts.csv",
                mime="text/csv",
            )

    # Threat Intelligence
    with tab5:
        st.header("Domain & IP Intelligence")

        indicator_input = st.text_area(
            "Enter domains or IP addresses (one per line)",
            "example.com\n192.0.2.10",
        )

        if st.button("Validate Indicators"):
            indicators = [
                value.strip()
                for value in indicator_input.splitlines()
                if value.strip()
            ]

            result = analyse_indicators(indicators)
            st.dataframe(result, use_container_width=True)

            st.info(
                "Validation checks syntax only. "
                "Indicators have not been verified as malicious."
            )

    # Report generation
    st.divider()
    st.header("Investigation Case Report")

    if st.button("Generate PDF Case Report"):
        indicators = analyse_indicators([])

        report_path = generate_case_report(
            transactions,
            trail,
            alerts,
            indicators,
        )

        with open(report_path, "rb") as pdf_file:
            st.download_button(
                "Download Investigation PDF",
                pdf_file.read(),
                file_name="muleshield_case_report.pdf",
                mime="application/pdf",
            )

else:
    st.info(
        "Upload synthetic bank statements from the sidebar "
        "and click Analyse Statements to begin."
    )
