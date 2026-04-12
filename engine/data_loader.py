import pandas as pd
import yfinance as yf

def load_market_data():
    try:
        brent = yf.download("BZ=F", period="6mo", progress=False)["Close"]
        vix = yf.download("^VIX", period="6mo", progress=False)["Close"]
        dxy = yf.download("DX-Y.NYB", period="6mo", progress=False)["Close"]

        df = pd.concat([brent, vix, dxy], axis=1)
        df.columns = ["brent", "vix", "dxy"]

        df = df.dropna()

        return df

    except Exception as e:
        # fallback para evitar que Streamlit rompa
        return pd.DataFrame()
