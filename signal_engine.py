from __future__ import annotations

from typing import Dict


def classify_regime(
    sg: float,
    sg_fragile: float = 0.40,
    sg_transmission: float = 0.70,
) -> str:
    if sg >= sg_transmission:
        return "TRANSMISSION"
    if sg >= sg_fragile:
        return "FRAGILE"
    return "ABSORPTION"


def generate_signal(
    sg: float,
    cp: float,
    theta_eff: float,
    contagion_peak: float,
    negotiation: Dict[str, float | str],
    thresholds: dict,
) -> Dict[str, float | str]:
    regime = classify_regime(
        sg=sg,
        sg_fragile=thresholds["sg_fragile"],
        sg_transmission=thresholds["sg_transmission"],
    )

    if (
        regime == "TRANSMISSION"
        and cp >= thresholds["cp_high"]
        and theta_eff <= thresholds["theta_low"]
        and contagion_peak >= thresholds["contagion_peak_high"]
    ):
        return {
            "signal": "RISK_OFF",
            "confidence": 0.90,
            "regime": regime,
            "message": "System in transmission regime with elevated contagion pressure.",
        }

    if float(negotiation.get("p_execution", 0.0)) >= 0.60 and regime != "TRANSMISSION":
        return {
            "signal": "RELIEF_RALLY",
            "confidence": 0.72,
            "regime": regime,
            "message": "Execution probability improving while systemic stress remains contained.",
        }

    if regime == "FRAGILE":
        return {
            "signal": "WATCH",
            "confidence": 0.65,
            "regime": regime,
            "message": "Fragile regime: system still functioning, but under narrowing admissible paths.",
        }

    return {
        "signal": "NEUTRAL",
        "confidence": 0.50,
        "regime": regime,
        "message": "No dominant directional signal. Continue monitoring synchronization conditions.",
    }
