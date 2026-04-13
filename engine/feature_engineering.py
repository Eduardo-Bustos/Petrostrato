import numpy as np
import pandas as pd


def safe_zscore(series: pd.Series) -> pd.Series:
    """
    Z-score robusto para evitar divisiones por cero.
    """
    s = pd.to_numeric(series, errors="coerce")
    std = s.std(ddof=0)

    if std is None or np.isnan(std) or std < 1e-9:
        return pd.Series(np.zeros(len(s)), index=s.index, dtype="float64")

    return (s - s.mean()) / (std + 1e-9)


def safe_pct_change(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Cambio porcentual limpio y sin inf.
    """
    out = pd.to_numeric(series, errors="coerce").pct_change(periods=periods)
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def safe_rolling_std(series: pd.Series, window: int = 10) -> pd.Series:
    """
    Rolling std con limpieza.
    """
    out = pd.to_numeric(series, errors="coerce").rolling(window, min_periods=max(2, window // 2)).std()
    return out.replace([np.inf, -np.inf], np.nan)


def validate_market_columns(df: pd.DataFrame):
    required = ["brent", "vix", "dxy"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye features de Stage 5 + Stage 6:
    - normalización
    - momentum
    - volatilidad
    - freight proxy
    - divergence
    - returns auxiliares
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    validate_market_columns(out)

    for col in ["brent", "vix", "dxy"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.sort_index()

    # -------------------------
    # Normalized layers
    # -------------------------
    out["brent_z"] = safe_zscore(out["brent"])
    out["vix_z"] = safe_zscore(out["vix"])
    out["dxy_z"] = safe_zscore(out["dxy"])

    # -------------------------
    # Returns / momentum
    # -------------------------
    out["brent_ret_1"] = safe_pct_change(out["brent"], periods=1)
    out["brent_ret_5"] = safe_pct_change(out["brent"], periods=5)
    out["vix_ret_1"] = safe_pct_change(out["vix"], periods=1)
    out["dxy_ret_1"] = safe_pct_change(out["dxy"], periods=1)

    out["momentum"] = out["brent_ret_5"]

    # -------------------------
    # Volatility
    # -------------------------
    out["volatility"] = safe_rolling_std(out["brent_ret_1"], window=10)

    # -------------------------
    # Physical / logistics proxy
    # -------------------------
    out["freight_proxy"] = out["brent_z"].rolling(5, min_periods=1).mean()

    # -------------------------
    # Cross-layer divergence
    # -------------------------
    out["divergence"] = (out["brent_z"] - out["vix_z"]).abs()

    # optional extra divergence
    out["fx_energy_divergence"] = (out["brent_z"] - out["dxy_z"]).abs()

    # -------------------------
    # Cleaning
    # -------------------------
    numeric_cols = out.select_dtypes(include=[np.number]).columns
    out[numeric_cols] = out[numeric_cols].replace([np.inf, -np.inf], np.nan)

    out = out.dropna()

    return out
