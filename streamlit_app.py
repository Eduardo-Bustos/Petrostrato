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


# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="PetroStratum",
    layout="wide",
)

st.title("PetroStratum — Stage 5 + Stage 6 Merge")
st.caption("War Room | Regime Engine | Shock Engine | Empirical Calibration")


# -----------------------------------
# DATA PIPELINE
# -----------------------------------
@st.cache_data(ttl=300)
def build_dataset():
    raw = load_market_data(period="6mo", interval="1d")
    if raw.empty:
        return pd.DataFrame(), np.array([])

    feat = compute_features(raw)
    if feat.empty:
        return pd.DataFrame(), np.array([])

    calibrated, beta = calibrate_sg(feat)
    return calibrated, beta
