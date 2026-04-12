import numpy as np

def zscore(series):
    return (series - series.mean()) / (series.std() + 1e-9)

def compute_features(df):
    df = df.copy()

    # Normalización
    df["brent_z"] = zscore(df["brent"])
    df["vix_z"] = zscore(df["vix"])
    df["dxy_z"] = zscore(df["dxy"])

    # Momentum (dinámica de precio)
    df["momentum"] = df["brent"].pct_change(5)

    # Volatilidad local
    df["volatility"] = df["brent"].rolling(10).std()

    # Proxy logístico (muy importante en Stratum)
    df["freight_proxy"] = df["brent_z"].rolling(5, min_periods=1).mean()

    # Divergencia entre capas (core del modelo)
    df["divergence"] = abs(df["brent_z"] - df["vix_z"])

    return df.dropna()
