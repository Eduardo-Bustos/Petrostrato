import yfinance as yf
import pandas as pd

ASSETS = {
    "brent": "BZ=F",
    "wti": "CL=F",
    "gold": "GC=F",
    "natgas": "NG=F",
    "spx": "^GSPC",
    "vix": "^VIX",
}

def fetch_latest_prices():
    data = {}
    for name, ticker in ASSETS.items():
        try:
            df = yf.download(ticker, period="1d", interval="1m")
            data[name] = float(df["Close"].iloc[-1])
        except:
            data[name] = None
    return data


def build_realtime_frame():
    prices = fetch_latest_prices()
    df = pd.DataFrame([prices])
    return df
