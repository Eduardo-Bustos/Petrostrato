from __future__ import annotations

from typing import Dict, Any
import numpy as np

from engine.data_realtime import build_realtime_frame
from engine.signal_engine import generate_signal
from engine.alert_engine import check_alerts
from engine.behavior_engine import decision_bias_vector, agent_decision_state
from engine.negotiation_engine import negotiation_output
from engine.contagion_engine import (
    ContagionConfig,
    build_weighted_adjacency,
    simulate_network_sir,
)


def derive_stratum_state_from_market(snapshot: dict, defaults: dict) -> dict:
    """
    Placeholder operational mapping.
    Replace later with calibrated econometric outputs from Stratum core.
    """
    brent = snapshot.get("brent")
    vix = snapshot.get("vix")
    dxy = snapshot.get("dxy")

    sg = defaults["sg"]
    cp = defaults["cp"]
    theta_eff = defaults["theta_eff"]
    divergence = defaults["divergence"]

    if brent is not None and vix is not None:
        sg = min(1.5, max(0.0, 0.0025 * brent + 0.015 * vix))
        cp = min(1.5, max(0.0, 0.0018 * brent + 0.010 * vix))
        theta_eff = max(0.0, min(1.0, 1.0 - 0.012 * vix))
        divergence = max(0.0, min(1.0, abs(0.0015 * brent - 0.008 * vix)))

    if dxy is not None:
        sg = min(1.5, sg + 0.001 * max(dxy - 100, 0))
        cp = min(1.5, cp + 0.0008 * max(dxy - 100, 0))

    p_break = float(1.0 / (1.0 + np.exp(-(1.10 * sg + 0.85 * cp - 1.20 * theta_eff))))

    return {
        "sg": float(sg),
        "cp": float(cp),
        "theta_eff": float(theta_eff),
        "divergence": float(divergence),
        "p_break": float(p_break),
    }


def run_stratum_cycle(settings: dict) -> Dict[str, Any]:
    market_cfg = settings["market"]
    defaults = settings["stratum"]["defaults"]
    thresholds = settings["stratum"]["thresholds"]

    realtime_df = build_realtime_frame(
        assets=market_cfg["assets"],
        history_period=market_cfg["history_period"],
        interval=market_cfg["interval"],
    )

    snapshot = realtime_df.iloc[0].to_dict() if not realtime_df.empty else {}

    state = derive_stratum_state_from_market(snapshot, defaults)

    behavior = decision_bias_vector(
        sg=state["sg"],
        cp=state["cp"],
        divergence=state["divergence"],
        p_break=state["p_break"],
        anchor_signal=0.45,
        optimism_narrative=0.30,
        threat_narrative=0.70,
    )
    behavior_state = agent_decision_state(
        effective_risk=behavior["effective_risk"],
        confidence=behavior["confidence"],
    )

    negotiation = negotiation_output(
        credibility=0.42,
        domestic_pressure=0.68,
        strategic_distance=0.62,
        execution_capacity=max(state["theta_eff"], 0.05),
        ambiguity=state["divergence"],
    )

    nodes = ["Hormuz", "Asia", "Europe", "Emerging Markets", "United States"]
    edges = [
        ("Hormuz", "Asia", 0.90),
        ("Hormuz", "Europe", 0.80),
        ("Asia", "Emerging Markets", 0.65),
        ("Europe", "United States", 0.45),
        ("Emerging Markets", "United States", 0.55),
    ]
    adj = build_weighted_adjacency(nodes, edges)

    contagion = simulate_network_sir(
        adjacency=adj,
        sg=state["sg"],
        cp=state["cp"],
        theta_eff=state["theta_eff"],
        steps=20,
        initially_infected=["Hormuz"],
        cfg=ContagionConfig(),
    )

    signal = generate_signal(
        sg=state["sg"],
        cp=state["cp"],
        theta_eff=state["theta_eff"],
        contagion_peak=float(contagion["peak_infection"]),
        negotiation=negotiation,
        thresholds=thresholds,
    )

    alerts = check_alerts(
        signal=signal,
        sg=state["sg"],
        cp=state["cp"],
        theta_eff=state["theta_eff"],
        contagion_peak=float(contagion["peak_infection"]),
        thresholds=thresholds,
    )

    return {
        "market_snapshot": snapshot,
        "state": state,
        "behavior": behavior,
        "behavior_state": behavior_state,
        "negotiation": negotiation,
        "contagion": contagion,
        "signal": signal,
        "alerts": alerts,
    }
