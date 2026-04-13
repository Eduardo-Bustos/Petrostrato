from __future__ import annotations

from typing import List, Dict


def check_alerts(
    signal: Dict[str, float | str],
    sg: float,
    cp: float,
    theta_eff: float,
    contagion_peak: float,
    thresholds: dict,
) -> List[dict]:
    alerts: List[dict] = []

    if sg >= thresholds["sg_transmission"]:
        alerts.append(
            {
                "severity": "CRITICAL",
                "title": "SG above transmission threshold",
                "message": f"SG={sg:.3f} indicates system has moved into transmissive territory.",
            }
        )

    if cp >= thresholds["cp_high"]:
        alerts.append(
            {
                "severity": "HIGH",
                "title": "Constraint pressure elevated",
                "message": f"CP={cp:.3f} suggests chokepoint stress remains active.",
            }
        )

    if theta_eff <= thresholds["theta_low"]:
        alerts.append(
            {
                "severity": "HIGH",
                "title": "Theta_eff weakened",
                "message": f"Theta_eff={theta_eff:.3f} signals diminished closure capacity.",
            }
        )

    if contagion_peak >= thresholds["contagion_peak_high"]:
        alerts.append(
            {
                "severity": "HIGH",
                "title": "Contagion peak elevated",
                "message": f"Peak infection={contagion_peak:.3f} implies expanding network stress.",
            }
        )

    if signal["signal"] == "RISK_OFF":
        alerts.append(
            {
                "severity": "CRITICAL",
                "title": "Market regime shift",
                "message": str(signal["message"]),
            }
        )

    if not alerts:
        alerts.append(
            {
                "severity": "INFO",
                "title": "No critical alerts",
                "message": "System remains under observation without threshold breach.",
            }
        )

    return alerts
