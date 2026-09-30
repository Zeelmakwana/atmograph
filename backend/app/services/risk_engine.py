from typing import Any


EVENT_TYPE_WEIGHTS = {
    "port_strike": 90,
    "supply_chain_disruption": 85,
    "port_closure": 95,
    "weather_disruption": 75,
    "factory_shutdown": 90,
    "transport_disruption": 80,
    "geopolitical_disruption": 95,
    "labor_strike": 85,
}

SEVERITY_WEIGHTS = {
    "low": 25,
    "medium": 50,
    "high": 80,
    "critical": 100,
}


def calculate_risk(
    event_type: str | None,
    severity: str | None,
    status: str | None,
) -> dict[str, Any]:

    event_type = (event_type or "unknown").lower()
    severity = (severity or "medium").lower()
    status = (status or "active").lower()

    event_score = EVENT_TYPE_WEIGHTS.get(event_type, 50)
    severity_score = SEVERITY_WEIGHTS.get(severity, 50)

    status_multiplier = {
        "active": 1.0,
        "ongoing": 1.0,
        "resolved": 0.25,
        "inactive": 0.25,
    }.get(status, 1.0)

    raw_score = (
        (event_score * 0.55)
        + (severity_score * 0.45)
    )

    final_score = round(
        min(raw_score * status_multiplier, 100),
        2,
    )

    if final_score >= 80:
        risk_level = "critical"
    elif final_score >= 60:
        risk_level = "high"
    elif final_score >= 35:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "event_type_score": event_score,
        "severity_score": severity_score,
        "status_multiplier": status_multiplier,
    }