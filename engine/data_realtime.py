from __future__ import annotations

from typing import Dict, Any
import pandas as pd
import yfinance as yf


def fetch_latest_prices(
    assets: dict[str, str],
    history_period: str = "5d",
    interval: str = "1m",
) -> dict[str, float | None]:
    prices: dict[str, float | None] = {}

    for name, ticker in assets.items():
        try:
            df = yf.download(
                ticker,
                period=history_period,
                interval=interval,
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            if df is None or df.empty or "Close" not in df.columns:
                prices[name] = None
                continue

            prices[name] = float(df["Close"].dropna().iloc[-1])
        except Exception:
            prices[name] = None

    return prices


def build_realtime_frame(
    assets: dict[str, str],
    history_period: str = "5d",
    interval: str = "1m",
) -> pd.DataFrame:
    prices = fetch_latest_prices(
        assets=assets,
        history_period=history_period,
        interval=interval,
    )
    return pd.DataFrame([prices])


def validate_market_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    valid = {k: v for k, v in snapshot.items() if v is not None}
    return {
        "valid_count": len(valid),
        "missing_count": len(snapshot) - len(valid),
        "valid_fields": list(valid.keys()),
    }
