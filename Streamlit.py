from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from engine.data_loader import load_market_data
from engine.feature_engineering import compute_features
from engine.econometrics import calibrate_sg
from engine.scenario_engine import (
    apply_shock,
    negotiation_state_modifier,
    price_impact_from_sg,
    interpret_regime,
)
from engine.monte_carlo import monte_carlo_sg, regime_probabilities_from_terminal

st.set_page_config(page_title="PetroStratum", layout="wide")

st.title("PetroStratum — Stage 5 + 6 Merge")
st.caption("War Room | Regime Engine | Shock Engine | Empirical Calibration")

@st.cache_data(ttl=300)
def build_dataset():
    df = load_market_data()
    df = compute_features(df)
    df, beta = calibrate_sg(df)
    return df, beta

df, beta = build_dataset()

if df.empty:
    st.error("No market data available.")
    st.stop()

latest = df.iloc[-1]
sg_current = float(latest["sg"])
div_current = float(latest["divergence"])
sg_momentum = float(latest["sg_momentum"])

def regime_name(sg):
    if sg > 0.70:
        return "Transmission"
    elif sg > 0.40:
        return "Fragile"
    return "Absorption"

regime_now = regime_name(sg_current)

scores = np.array([
    1.2 - 2.2 * sg_current - 1.0 * max(sg_momentum, 0) - 0.8 * div_current,
    0.8 + 0.6 * sg_current + 0.4 * div_current,
    -0.5 + 2.5 * sg_current + 1.1 * div_current
], dtype=float)

probs = np.exp(scores - scores.max())
probs = probs / probs.sum()
p_absorb, p_fragile, p_trans = probs.tolist()

drift = 0.01 if sg_momentum >= 0 else -0.005
paths = monte_carlo_sg(sg_current, div_current, drift=drift)
terminal = paths[:, -1]
mc_absorb, mc_fragile, mc_trans = regime_probabilities_from_terminal(terminal)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Live",
    "Signals",
    "Calibration",
    "Regime Engine",
    "Monte Carlo",
    "War Room"
])

with tab1:
    st.subheader("Live System State")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Brent", round(float(latest["brent"]), 2))
    c2.metric("VIX", round(float(latest["vix"]), 2))
    c3.metric("DXY", round(float(latest["dxy"]), 2))
    c4.metric("SG", round(sg_current, 3), round(sg_momentum, 3))

    st.write(f"Current regime: **{regime_now}**")
    st.write(f"Divergence: **{round(div_current, 3)}**")

with tab2:
    st.subheader("Cross-Layer Signals")
    st.line_chart(df[["brent_z", "vix_z", "dxy_z", "freight_proxy", "sg"]])

with tab3:
    st.subheader("Empirical Calibration")
    beta_df = pd.DataFrame({
        "Variable": ["brent_z", "dxy_z", "momentum"],
        "Coefficient": beta
    })
    st.dataframe(beta_df, use_container_width=True)
    st.line_chart(df["sg"])

with tab4:
    st.subheader("Regime Probabilities")
    r1, r2, r3 = st.columns(3)
    r1.metric("Absorption", f"{p_absorb:.1%}")
    r2.metric("Fragile", f"{p_fragile:.1%}")
    r3.metric("Transmission", f"{p_trans:.1%}")

    regime_df = pd.DataFrame({
        "Scenario": ["Absorption", "Fragile", "Transmission"],
        "Probability": [p_absorb, p_fragile, p_trans]
    }).set_index("Scenario")
    st.bar_chart(regime_df)

with tab5:
    st.subheader("Monte Carlo SG Paths")

    fig, ax = plt.subplots(figsize=(10, 4))
    horizon = np.arange(paths.shape[1])
    mean_path = paths.mean(axis=0)
    p25 = np.quantile(paths, 0.25, axis=0)
    p75 = np.quantile(paths, 0.75, axis=0)

    ax.plot(horizon, mean_path, label="Mean path")
    ax.fill_between(horizon, p25, p75, alpha=0.2, label="25–75% band")
    ax.axhline(0.40, linestyle="--", linewidth=1)
    ax.axhline(0.70, linestyle="--", linewidth=1)
    ax.legend()
    ax.set_title("Projected SG")
    st.pyplot(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Terminal Absorption", f"{mc_absorb:.1%}")
    m2.metric("Terminal Fragile", f"{mc_fragile:.1%}")
    m3.metric("Terminal Transmission", f"{mc_trans:.1%}")

with tab6:
    st.subheader("Negotiation + Shock Engine")

    shock = st.selectbox(
        "Shock",
        ["None", "Hormuz Disruption", "Lebanon Escalation", "Sanctions Tightening", "Ceasefire"]
    )

    negotiation = st.selectbox(
        "Negotiation State",
        ["No Contact", "Indirect Talks", "Direct Talks", "Partial Agreement", "Breakdown"]
    )

    sg_adj = sg_current
    div_adj = div_current

    if shock != "None":
        sg_adj, div_adj = apply_shock(sg_adj, div_adj, shock)

    sg_adj = min(1.5, sg_adj * negotiation_state_modifier(negotiation))
    oil, gold, risk = price_impact_from_sg(sg_adj, div_adj)

    w1, w2, w3 = st.columns(3)
    w1.metric("Adjusted SG", round(sg_adj, 2))
    w2.metric("Oil (model)", round(oil, 1))
    w3.metric("Gold (model)", round(gold, 1))

    st.write(f"Risk Appetite Index: {round(risk, 2)}")
    st.write(interpret_regime(sg_adj))

st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
