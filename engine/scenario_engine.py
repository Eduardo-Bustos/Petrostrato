import numpy as np


VALID_SHOCKS = [
    "None",
    "Hormuz Disruption",
    "Lebanon Escalation",
    "Sanctions Tightening",
    "Ceasefire",
]

VALID_NEGOTIATION_STATES = [
    "No Contact",
    "Indirect Talks",
    "Direct Talks",
    "Partial Agreement",
    "Breakdown",
]


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def apply_shock(sg, divergence, shock_type):
    """
    Aplica shock exógeno al sistema.
    Devuelve SG ajustado y divergence ajustada.
    """
    sg_adj = float(sg)
    div_adj = float(divergence)

    if shock_type == "Hormuz Disruption":
        sg_adj += 0.15
        div_adj += 0.10

    elif shock_type == "Lebanon Escalation":
        sg_adj += 0.10
        div_adj += 0.08

    elif shock_type == "Sanctions Tightening":
        sg_adj += 0.08
        div_adj += 0.05

    elif shock_type == "Ceasefire":
        sg_adj -= 0.12
        div_adj -= 0.07

    sg_adj = clamp(sg_adj, 0.0, 1.5)
    div_adj = clamp(div_adj, 0.0, 1.0)

    return sg_adj, div_adj


def negotiation_state_modifier(state):
    """
    Multiplicador de ejecución política / diplomática.
    >1 empeora
    <1 mejora
    """
    mapping = {
        "No Contact": 1.20,
        "Indirect Talks": 1.00,
        "Direct Talks": 0.85,
        "Partial Agreement": 0.65,
        "Breakdown": 1.35,
    }
    return mapping.get(state, 1.0)


def apply_negotiation_state(sg, divergence, state):
    """
    Aplica el efecto del estado de negociación sobre SG.
    Divergence se mueve menos que SG, pero también responde.
    """
    sg_adj = float(sg)
    div_adj = float(divergence)

    modifier = negotiation_state_modifier(state)

    sg_adj = sg_adj * modifier

    # divergence también se ajusta, pero con elasticidad menor
    if modifier > 1:
        div_adj = div_adj * (1 + (modifier - 1) * 0.5)
    elif modifier < 1:
        div_adj = div_adj * (1 - (1 - modifier) * 0.4)

    sg_adj = clamp(sg_adj, 0.0, 1.5)
    div_adj = clamp(div_adj, 0.0, 1.0)

    return sg_adj, div_adj


def derive_structural_adjustments(sg, divergence):
    """
    Reconstruye proxies estructurales ajustados
    para usar en tablero o price layer.
    """
    theta = clamp(1.0 - divergence, 0.0, 1.0)
    cp = clamp(0.5 * divergence + 0.5 * sg, 0.0, 1.5)
    delta_tau = clamp(divergence, 0.0, 1.0)
    alt_exec = clamp(0.6 * divergence + 0.4 * max(sg - 0.4, 0), 0.0, 1.5)
    theta_eff = clamp(theta * (1.0 - 0.5 * min(alt_exec, 1.0)), 0.0, 1.0)

    raw_break = (
        1.10 * sg
        + 0.85 * cp
        + 0.60 * delta_tau
        - 1.20 * theta_eff
        + 0.70 * min(alt_exec, 1.0)
    )

    p_break = 1.0 / (1.0 + np.exp(-raw_break))

    return {
        "theta": theta,
        "cp": cp,
        "delta_tau": delta_tau,
        "alt_exec": alt_exec,
        "theta_eff": theta_eff,
        "p_break": p_break,
    }


def price_impact_from_sg(sg, divergence):
    """
    Traducción simplificada del estado sistémico a variables observables.
    """
    oil = 85 + 25 * sg + 10 * divergence
    gold = 2200 + 300 * sg + 250 * divergence
    risk = max(0.0, 1.0 - 0.8 * sg - 0.4 * divergence)

    return oil, gold, risk


def regime_from_sg(sg):
    if sg > 0.70:
        return "Transmission"
    elif sg > 0.40:
        return "Fragile"
    return "Absorption"


def interpret_regime(sg):
    if sg > 0.70:
        return "Transmission regime — execution failure risk high."
    elif sg > 0.40:
        return "Fragile coordination — outcome depends on execution."
    return "Absorptive regime — system stabilizing."


def scenario_summary(sg, divergence, shock_type="None", negotiation_state="Indirect Talks"):
    """
    Función maestra para el war-room:
    aplica shock + negociación + reconstrucción estructural + impacto en precios.
    """
    sg_adj, div_adj = apply_shock(sg, divergence, shock_type)
    sg_adj, div_adj = apply_negotiation_state(sg_adj, div_adj, negotiation_state)

    structural = derive_structural_adjustments(sg_adj, div_adj)
    oil, gold, risk = price_impact_from_sg(sg_adj, div_adj)

    return {
        "shock": shock_type,
        "negotiation_state": negotiation_state,
        "sg_adj": sg_adj,
        "divergence_adj": div_adj,
        "regime": regime_from_sg(sg_adj),
        "interpretation": interpret_regime(sg_adj),
        "oil_model": oil,
        "gold_model": gold,
        "risk_appetite": risk,
        **structural,
    }
