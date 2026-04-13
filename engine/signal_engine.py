def generate_signal(sg, cp, theta_eff, contagion_peak, negotiation):
    
    # Regímenes
    if sg > 0.7 and theta_eff < 0.3:
        regime = "TRANSMISSION"
    elif sg > 0.4:
        regime = "FRAGILE"
    else:
        regime = "ABSORPTION"

    # Señales
    if regime == "TRANSMISSION" and contagion_peak > 3:
        return {
            "signal": "RISK_OFF",
            "confidence": 0.85,
            "message": "System in propagation phase"
        }

    if negotiation["p_execution"] > 0.6:
        return {
            "signal": "RELIEF_RALLY",
            "confidence": 0.7,
            "message": "Execution probability rising"
        }

    return {
        "signal": "NEUTRAL",
        "confidence": 0.5,
        "message": "No dominant regime"
    }
