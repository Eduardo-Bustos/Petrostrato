import numpy as np
import pandas as pd


REQUIRED_FEATURE_COLUMNS = [
    "brent_z",
    "vix_z",
    "dxy_z",
    "momentum",
    "divergence",
    "freight_proxy",
]


def validate_feature_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")


def safe_clip(series: pd.Series, lower=None, upper=None) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return s.clip(lower=lower, upper=upper)


def logistic(x):
    return 1.0 / (1.0 + np.exp(-x))


def calibrate_sg(df: pd.DataFrame):
    """
    Calibra SG empíricamente usando una regresión OLS simple:
        vix_z ~ brent_z + dxy_z + momentum

    Luego construye variables estructurales:
    - sg
    - sg_momentum
    - theta
    - cp
    - theta_eff
    - delta_tau
    - alt_exec
    - p_break
    """
    if df is None or df.empty:
        return pd.DataFrame(), np.array([])

    out = df.copy()
    validate_feature_columns(out)

    # -------------------------
    # Cleaning
    # -------------------------
    out = out.replace([np.inf, -np.inf], np.nan).dropna().copy()

    if len(out) < 10:
        # Dataset demasiado chico para calibración útil
        return pd.DataFrame(), np.array([])

    # -------------------------
    # Target & regressors
    # -------------------------
    y = pd.to_numeric(out["vix_z"], errors="coerce").fillna(0.0)

    X = out[["brent_z", "dxy_z", "momentum"]].copy()
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # -------------------------
    # OLS calibration
    # -------------------------
    beta = np.linalg.lstsq(X.values, y.values, rcond=None)[0]

    # -------------------------
    # SG calibrated
    # -------------------------
    out["sg"] = X @ beta

    # suavizado ligero opcional
    out["sg_smooth"] = out["sg"].rolling(3, min_periods=1).mean()

    # -------------------------
    # Structural dynamics
    # -------------------------
    out["sg_momentum"] = out["sg"].diff().fillna(0.0)
    out["sg_acceleration"] = out["sg_momentum"].diff().fillna(0.0)

    # Theta: capacidad de coordinación (alta cuando divergence es baja)
    out["theta"] = 1.0 - safe_clip(out["divergence"], lower=0.0)

    # Constraint propagation
    out["cp"] = 0.5 * pd.to_numeric(out["freight_proxy"], errors="coerce").fillna(0.0) \
              + 0.5 * pd.to_numeric(out["vix_z"], errors="coerce").fillna(0.0)

    # Effective theta
    out["delta_tau"] = pd.to_numeric(out["divergence"], errors="coerce").fillna(0.0) \
        .rolling(3, min_periods=1).mean()

    out["alt_exec"] = (
        0.6 * safe_clip(out["vix_z"], lower=0.0).fillna(0.0)
        + 0.4 * safe_clip(out["divergence"], lower=0.0).fillna(0.0)
    )

    out["theta_eff"] = (
        out["theta"] * (1.0 - 0.5 * out["alt_exec"])
    ).clip(lower=0.0)

    # -------------------------
    # Break probability
    # -------------------------
    raw_break = (
        1.10 * out["sg"]
        + 0.85 * out["cp"]
        + 0.60 * out["delta_tau"]
        - 1.20 * out["theta_eff"]
        + 0.70 * out["alt_exec"]
    )

    out["p_break"] = logistic(raw_break)

    # -------------------------
    # Regime flags
    # -------------------------
    out["regime"] = np.where(
        out["sg"] > 0.70,
        "Transmission",
        np.where(out["sg"] > 0.40, "Fragile", "Absorption")
    )

    out["flag_fragile"] = (out["regime"] == "Fragile").astype(int)
    out["flag_transmission"] = (out["regime"] == "Transmission").astype(int)
    out["flag_high_break"] = (out["p_break"] > 0.70).astype(int)

    # -------------------------
    # Final cleaning
    # -------------------------
    out = out.replace([np.inf, -np.inf], np.nan).dropna().copy()

    return out, beta


def extract_latest_state(df: pd.DataFrame) -> dict:
    """
    Devuelve el último estado del sistema en formato dict.
    """
    if df is None or df.empty:
        return {}

    row = df.iloc[-1]

    return {
        "brent": float(row["brent"]) if "brent" in row else None,
        "vix": float(row["vix"]) if "vix" in row else None,
        "dxy": float(row["dxy"]) if "dxy" in row else None,
        "sg": float(row["sg"]) if "sg" in row else None,
        "sg_smooth": float(row["sg_smooth"]) if "sg_smooth" in row else None,
        "sg_momentum": float(row["sg_momentum"]) if "sg_momentum" in row else None,
        "sg_acceleration": float(row["sg_acceleration"]) if "sg_acceleration" in row else None,
        "divergence": float(row["divergence"]) if "divergence" in row else None,
        "theta": float(row["theta"]) if "theta" in row else None,
        "theta_eff": float(row["theta_eff"]) if "theta_eff" in row else None,
        "cp": float(row["cp"]) if "cp" in row else None,
        "delta_tau": float(row["delta_tau"]) if "delta_tau" in row else None,
        "alt_exec": float(row["alt_exec"]) if "alt_exec" in row else None,
        "p_break": float(row["p_break"]) if "p_break" in row else None,
        "regime": str(row["regime"]) if "regime" in row else None,
    }


def beta_table(beta: np.ndarray) -> pd.DataFrame:
    """
    Devuelve los coeficientes en formato tabla.
    """
    if beta is None or len(beta) == 0:
        return pd.DataFrame(columns=["Variable", "Coefficient"])

    return pd.DataFrame({
        "Variable": ["brent_z", "dxy_z", "momentum"],
        "Coefficient": beta
    })
