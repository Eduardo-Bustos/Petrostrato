import numpy as np
import pandas as pd


def clamp_array(arr, lower=0.0, upper=1.5):
    return np.clip(arr, lower, upper)


def regime_from_value(x):
    if x > 0.70:
        return "Transmission"
    elif x > 0.40:
        return "Fragile"
    return "Absorption"


def regime_probabilities_from_terminal(terminal):
    """
    Calcula probabilidades terminales por régimen.
    """
    terminal = np.asarray(terminal, dtype=float)

    p_absorption = float(np.mean(terminal <= 0.40))
    p_fragile = float(np.mean((terminal > 0.40) & (terminal <= 0.70)))
    p_transmission = float(np.mean(terminal > 0.70))

    return p_absorption, p_fragile, p_transmission


def summarize_terminal_distribution(terminal):
    """
    Resumen estadístico útil para dashboard/paper.
    """
    terminal = np.asarray(terminal, dtype=float)

    return {
        "mean": float(np.mean(terminal)),
        "median": float(np.median(terminal)),
        "p10": float(np.quantile(terminal, 0.10)),
        "p25": float(np.quantile(terminal, 0.25)),
        "p75": float(np.quantile(terminal, 0.75)),
        "p90": float(np.quantile(terminal, 0.90)),
    }


def monte_carlo_sg(
    sg0,
    div0,
    drift,
    sigma=0.05,
    steps=20,
    sims=400,
    seed=42,
    persistence=0.65,
    divergence_weight=0.10,
    stress_threshold=0.55,
    stress_amplification=0.08,
    lower_bound=0.0,
    upper_bound=1.5,
):
    """
    Monte Carlo para SG con:
    - persistencia
    - drift
    - shocks gaussianos
    - efecto de divergencia
    - amplificación en zona de estrés

    Parámetros:
    ----------
    sg0 : float
        valor inicial de SG
    div0 : float
        divergencia actual
    drift : float
        drift base del sistema
    sigma : float
        volatilidad del shock aleatorio
    steps : int
        horizonte
    sims : int
        número de simulaciones
    persistence : float
        componente autoregresivo
    divergence_weight : float
        peso del divergence term
    stress_threshold : float
        umbral donde el sistema acelera
    stress_amplification : float
        amplificación si el sistema entra en régimen estresado
    """
    rng = np.random.default_rng(seed)

    sg0 = float(sg0)
    div0 = float(div0)
    drift = float(drift)

    paths = np.zeros((sims, steps), dtype=float)
    paths[:, 0] = sg0

    for t in range(1, steps):
        shock = rng.normal(0.0, sigma, sims)

        prev = paths[:, t - 1]
        persistence_term = persistence * prev
        drift_term = drift
        divergence_term = divergence_weight * div0

        # Si ya entró en zona de fragilidad alta / transmisión,
        # amplifica dinámica del sistema
        stress_term = np.maximum(prev - stress_threshold, 0.0) * stress_amplification

        paths[:, t] = persistence_term + drift_term + divergence_term + stress_term + shock
        paths[:, t] = clamp_array(paths[:, t], lower=lower_bound, upper=upper_bound)

    return paths


def monte_carlo_summary(
    sg0,
    div0,
    drift,
    sigma=0.05,
    steps=20,
    sims=400,
    seed=42,
):
    """
    Función de alto nivel:
    corre paths + resume resultados.
    """
    paths = monte_carlo_sg(
        sg0=sg0,
        div0=div0,
        drift=drift,
        sigma=sigma,
        steps=steps,
        sims=sims,
        seed=seed,
    )

    terminal = paths[:, -1]

    p_absorption, p_fragile, p_transmission = regime_probabilities_from_terminal(terminal)
    stats = summarize_terminal_distribution(terminal)

    mean_path = paths.mean(axis=0)
    p25_path = np.quantile(paths, 0.25, axis=0)
    p75_path = np.quantile(paths, 0.75, axis=0)
    p10_path = np.quantile(paths, 0.10, axis=0)
    p90_path = np.quantile(paths, 0.90, axis=0)

    return {
        "paths": paths,
        "terminal": terminal,
        "mean_path": mean_path,
        "p10_path": p10_path,
        "p25_path": p25_path,
        "p75_path": p75_path,
        "p90_path": p90_path,
        "terminal_stats": stats,
        "p_absorption": p_absorption,
        "p_fragile": p_fragile,
        "p_transmission": p_transmission,
        "terminal_regime": regime_from_value(float(np.mean(terminal))),
    }


def paths_to_dataframe(paths):
    """
    Convierte matriz de paths a DataFrame útil para export.
    """
    arr = np.asarray(paths, dtype=float)
    horizon = arr.shape[1]
    cols = [f"t_{i}" for i in range(horizon)]
    return pd.DataFrame(arr, columns=cols)
