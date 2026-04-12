import numpy as np

def calibrate_sg(df):
    df = df.copy()

    # Variable objetivo: estrés financiero observado
    y = df["vix_z"]

    # Variables explicativas: energía, FX y momentum
    X = df[["brent_z", "dxy_z", "momentum"]].fillna(0)

    # Estimación OLS simple
    beta = np.linalg.lstsq(X.values, y.values, rcond=None)[0]

    # SG calibrado empíricamente
    df["sg"] = X @ beta

    # Dinámica adicional
    df["sg_momentum"] = df["sg"].diff().fillna(0)
    df["theta"] = 1 - df["divergence"]
    df["cp"] = 0.5 * df["freight_proxy"] + 0.5 * df["vix_z"]
    df["theta_eff"] = df["theta"].clip(lower=0)
    df["delta_tau"] = df["divergence"].rolling(3, min_periods=1).mean()
    df["alt_exec"] = (0.6 * df["vix_z"] + 0.4 * df["divergence"]).clip(lower=0)

    return df, beta
