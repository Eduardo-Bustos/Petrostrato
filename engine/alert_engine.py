def check_alerts(signal, sg, cp):
    
    alerts = []

    if sg > 0.8:
        alerts.append("CRITICAL: SG above threshold")

    if cp > 0.7:
        alerts.append("CHOKEPOINT PRESSURE HIGH")

    if signal["signal"] == "RISK_OFF":
        alerts.append("MARKET REGIME SHIFT")

    return alerts
