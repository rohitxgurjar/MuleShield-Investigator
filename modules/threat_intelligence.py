import ipaddress
import re
from urllib.parse import urlparse

import pandas as pd


def normalise_indicator(value):
    """Extract and normalise a domain or IP address."""

    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()

    # Handle URLs
    if "://" in value:
        value = urlparse(value).hostname or ""

    value = value.lower().strip(".")

    # Check IP address
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        pass

    # Check domain format
    domain_pattern = (
        r"^(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}$"
    )

    if re.match(domain_pattern, value):
        return value

    return None


def classify_indicator(value):
    """Classify a valid indicator as IP or domain."""

    normalised = normalise_indicator(value)

    if normalised is None:
        return "INVALID"

    try:
        ipaddress.ip_address(normalised)
        return "IP"
    except ValueError:
        return "DOMAIN"


def analyse_indicators(indicators):
    """
    Validate a list of domain/IP indicators.
    No active scanning or network probing is performed.
    """

    results = []

    for value in indicators:
        normalised = normalise_indicator(value)
        indicator_type = classify_indicator(value)

        results.append({
            "input": value,
            "indicator": normalised,
            "type": indicator_type,
            "status": (
                "VALID" if normalised else "INVALID"
            ),
            "intelligence_status": "NOT_ENRICHED"
        })

    return pd.DataFrame(results)
