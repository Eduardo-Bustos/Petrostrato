def apply_shock(sg, divergence, shock_type):
    if shock_type == "Hormuz Disruption":
        sg += 0.15
        divergence += 0.10
    elif shock_type == "Lebanon Escalation":
        sg += 0.10
        divergence += 0.08
    elif shock_type == "Sanctions Tightening":
        sg += 0.08
        divergence += 0.05
    elif shock_type == "Ceasefire":
        sg -= 0.12
        divergence -= 0.07

    sg = max(0, min(1.5, sg))
    divergence = max(0, min(1.0, divergence))
    return sg, divergence


def negotiation_state_modifier(state):
    mapping = {
        "No Contact": 1.20,
        "Indirect Talks": 1.00,
        "Direct Talks": 0.85,
        "Partial Agreement": 0.65,
        "Breakdown": 1.35,
    }
    return mapping.get(state, 1.0)


def price_impact_from_sg(sg, divergence):
    oil = 85 + 25 * sg + 10 * divergence
    gold = 2200 + 300 * sg + 250 * divergence
    risk = max(0, 1 - 0.8 * sg - 0.4 * divergence)
    return oil, gold, risk


def interpret_regime(sg):
    if sg > 0.70:
        return "Transmission regime — execution failure risk high."
    elif sg > 0.40:
        return "Fragile coordination — outcome depends on execution."
    return "Absorptive regime — system stabilizing."
