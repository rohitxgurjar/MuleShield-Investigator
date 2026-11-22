import networkx as nx
import pandas as pd

from modules.money_trail import build_money_trail


def build_account_graph(transactions):
    """
    Build a directed account network from matched UTR transfers.
    """

    trail = build_money_trail(transactions)

    graph = nx.DiGraph()

    matched = trail[trail["status"] == "MATCHED"]

    for _, row in matched.iterrows():
        sender = str(row["sender_account"])
        receiver = str(row["receiver_account"])

        graph.add_node(sender)
        graph.add_node(receiver)

        if graph.has_edge(sender, receiver):
            graph[sender][receiver]["total_amount"] += float(
                row["amount_sent"]
            )
            graph[sender][receiver]["transaction_count"] += 1
            graph[sender][receiver]["utrs"].append(str(row["utr"]))
        else:
            graph.add_edge(
                sender,
                receiver,
                total_amount=float(row["amount_sent"]),
                transaction_count=1,
                utrs=[str(row["utr"])]
            )

    return graph


def get_account_summary(graph):
    """
    Return basic incoming and outgoing account statistics.
    """

    summary = []

    for account in graph.nodes():
        outgoing = list(graph.out_edges(account, data=True))
        incoming = list(graph.in_edges(account, data=True))

        total_sent = sum(
            data["total_amount"] for _, _, data in outgoing
        )
        total_received = sum(
            data["total_amount"] for _, _, data in incoming
        )

        summary.append({
            "account_id": account,
            "total_sent": total_sent,
            "total_received": total_received,
            "outgoing_accounts": len(outgoing),
            "incoming_accounts": len(incoming),
            "net_flow": total_received - total_sent
        })

    return pd.DataFrame(summary)


def find_money_path(graph, source, target):
    """
    Find a directed path between two accounts.
    """

    if source not in graph:
        return {"status": "SOURCE_NOT_FOUND", "path": []}

    if target not in graph:
        return {"status": "TARGET_NOT_FOUND", "path": []}

    try:
        path = nx.shortest_path(
            graph,
            source=source,
            target=target
        )

        return {
            "status": "PATH_FOUND",
            "path": path,
            "hops": len(path) - 1
        }

    except nx.NetworkXNoPath:
        return {"status": "NO_PATH_FOUND", "path": []}
