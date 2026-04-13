from __future__ import annotations

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from engine.data_loader import load_market_data
from engine.feature_engineering import compute_features
from engine.econometrics import calibrate_sg, extract_latest_state, beta_table
from engine.scenario_engine import scenario_summary
from engine.monte_carlo import monte_carlo_summary
from engine.contagion_engine import (
    ContagionConfig,
    build_weighted_adjacency,
    identify_critical_nodes,
    simulate_network_sir,
)
from engine.behavior_engine import (
    BehavioralConfig,
    agent_decision_state,
    decision_bias_vector,
)
from engine.negotiation_engine import negotiation_output
from engine.validation_engine import (
    SensitivityConfig,
    basic_validation_report,
    sensitivity_table,
)

st.set_page_config(page_title="PetroStratum Stage 7", layout="wide")

st.title("PetroStratum — Stage 7")
st.caption("War Room | Econometrics | Contagion | Behavior | Negotiation | Validation")


@st.cache_data(ttl=300)
def build_dataset():
    raw = load_market_data()
    if raw.empty:
        return pd.DataFrame(), np.array([])
    feats = compute_features(raw)
    calibrated, beta = calibrate_sg(feats)
    return calibrated, beta


df, beta = build_dataset()

if df.empty:
    st.error("No market data available.")
    st.stop()

state = extract_latest_state(df)
beta_df = beta_table(beta)

sg_current = float(state["sg"])
cp_current = float(state["cp"])
theta_eff_current = float(state["theta_eff"])
div_current = float(state["divergence"])
p_break_current = float(state["p_break"])


def p_break_proxy(sg: float, cp: float, theta_eff: float) -> float:
    raw = 1.10 * sg + 0.85 * cp - 1.20 * theta_eff
    return float(1.0 / (1.0 + np.exp(-raw)))


# -------------------------
# Behavior layer
# -------------------------
behavior = decision_bias_vector(
    sg=sg_current,
    cp=cp_current,
    divergence=div_current,
    p_break=p_break_current,
    anchor_signal=0.45,
    optimism_narrative=0.30,
    threat_narrative=0.75,
    cfg=BehavioralConfig(),
)
agent_state = agent_decision_state(
    effective_risk=behavior["effective_risk"],
    confidence=behavior["confidence"],
)

# -------------------------
# Negotiation layer
# -------------------------
negotiation = negotiation_output(
    credibility=0.40,
    domestic_pressure=0.70,
    strategic_distance=0.65,
    execution_capacity=max(theta_eff_current, 0.05),
    ambiguity=div_current,
)

# -------------------------
# Scenario layer
# -------------------------
scenario = scenario_summary(
    sg=sg_current,
    divergence=div_current,
    shock_type="None",
    negotiation_state="Indirect Talks",
)

# -------------------------
# Monte Carlo layer
# -------------------------
drift = 0.01 if float(state["sg_momentum"]) >= 0 else -0.005
mc = monte_carlo_summary(
    sg0=sg_current,
    div0=div_current,
    drift=drift,
    sigma=0.05,
    steps=20,
    sims=400,
)

# -------------------------
# Contagion layer
# -------------------------
nodes = ["Hormuz", "Asia", "Europe", "Emerging Markets", "United States"]
edges = [
    ("Hormuz", "Asia", 0.90),
    ("Hormuz", "Europe", 0.80),
    ("Asia", "Emerging Markets", 0.65),
    ("Europe", "United States", 0.45),
    ("Emerging Markets", "United States", 0.55),
]
adj = build_weighted_adjacency(nodes, edges)
critical_nodes = identify_critical_nodes(adj)

contagion = simulate_network_sir(
    adjacency=adj,
    sg=sg_current,
    cp=cp_current,
    theta_eff=theta_eff_current,
    steps=20,
    initially_infected=["Hormuz"],
    cfg=ContagionConfig(),
)

contagion_hist = contagion["history"]
peak_infection = float(contagion["peak_infection"])
peak_r_t = float(contagion["peak_R_t"])

# -------------------------
# Validation & sensitivity
# -------------------------
validation = basic_validation_report(df)
sens_df = sensitivity_table(
    sg=sg_current,
    cp=cp_current,
    theta_eff=theta_eff_current,
    p_break_fn=p_break_proxy,
    cfg=SensitivityConfig(),
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "Live",
        "Calibration",
        "Behavior",
        "Negotiation",
        "Contagion",
        "Monte Carlo",
        "Validation",
    ]
)

with tab1:
    st.subheader("Live State")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SG", round(sg_current, 3), round(float(state["sg_momentum"]), 3))
    c2.metric("CP", round(cp_current, 3))
    c3.metric("Theta_eff", round(theta_eff_current, 3))
    c4.metric("P(Break)", round(p_break_current, 3))

    st.line_chart(df[["sg", "cp", "theta_eff", "p_break"]])

with tab2:
    st.subheader("Empirical Calibration")
    st.dataframe(beta_df, use_container_width=True)
    st.line_chart(df[["sg", "sg_smooth", "divergence"]])

with tab3:
    st.subheader("Behavioral Layer")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Effective Risk", round(float(behavior["effective_risk"]), 3))
    b2.metric("Confidence", round(float(behavior["confidence"]), 3))
    b3.metric("Amplification", round(float(behavior["amplification"]), 3))
    b4.metric("Agent State", agent_state)

    st.write("Behavioral diagnostics")
    st.json(behavior)

with tab4:
    st.subheader("Negotiation Layer")
    n1, n2, n3 = st.columns(3)
    n1.metric("P(Agreement)", round(float(negotiation["p_agreement"]), 3))
    n2.metric("P(Execution)", round(float(negotiation["p_execution"]), 3))
    n3.metric("State", str(negotiation["state"]))

    st.write("Scenario summary")
    st.json(scenario)

with tab5:
    st.subheader("Contagion Engine")
    c1, c2 = st.columns(2)
    c1.metric("Peak Infection", round(peak_infection, 3))
    c2.metric("Peak R_t", round(peak_r_t, 3))

    st.markdown("### Contagion paths")
    st.line_chart(contagion_hist.set_index("t")[["I_total", "R_t", "hawkes_intensity"]])

    st.markdown("### Critical nodes")
    st.dataframe(critical_nodes, use_container_width=True)

with tab6:
    st.subheader("Monte Carlo")
    fig, ax = plt.subplots(figsize=(10, 4))
    horizon = np.arange(len(mc["mean_path"]))
    ax.plot(horizon, mc["mean_path"], label="Mean path")
    ax.fill_between(
        horizon,
        mc["p25_path"],
        mc["p75_path"],
        alpha=0.2,
        label="25–75% band",
    )
    ax.axhline(0.40, linestyle="--", linewidth=1)
    ax.axhline(0.70, linestyle="--", linewidth=1)
    ax.legend()
    ax.set_title("Projected SG")
    st.pyplot(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("P(Absorption)", f"{mc['p_absorption']:.1%}")
    m2.metric("P(Fragile)", f"{mc['p_fragile']:.1%}")
    m3.metric("P(Transmission)", f"{mc['p_transmission']:.1%}")

with tab7:
    st.subheader("Validation & Sensitivity")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Rows", int(validation["rows"]))
    v2.metric("SG mean", round(float(validation["sg_mean"]), 3))
    v3.metric("SG std", round(float(validation["sg_std"]), 3))
    v4.metric("P(Break) mean", round(float(validation["p_break_mean"]), 3))

    st.markdown("### Sensitivity table")
    st.dataframe(sens_df.head(25), use_container_width=True)

    st.markdown("### Sensitivity heat proxy")
    pivot = sens_df.pivot_table(
        values="p_break",
        index="d_sg",
        columns="d_cp",
        aggfunc="mean",
    )
    st.dataframe(pivot, use_container_width=True)

st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
