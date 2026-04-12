import numpy as np

def monte_carlo_sg(sg0, div0, drift, sigma=0.05, steps=20, sims=400, seed=42):
    rng = np.random.default_rng(seed)
    paths = np.zeros((sims, steps))
    paths[:, 0] = sg0

    for t in range(1, steps):
        shock = rng.normal(0, sigma, sims)
        persistence = 0.65 * paths[:, t - 1]
        divergence_term = 0.10 * div0
        paths[:, t] = np.clip(
            persistence + drift + divergence_term + shock,
            0,
            1.5
        )

    return paths


def regime_probabilities_from_terminal(terminal):
    terminal = np.asarray(terminal)

    p_absorption = float(np.mean(terminal <= 0.40))
    p_fragile = float(np.mean((terminal > 0.40) & (terminal <= 0
