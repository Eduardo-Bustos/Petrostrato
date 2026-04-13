import pandas as pd
import yfinance as yf


def _download_close(ticker, period="6mo", interval="1d"):
    """
    Descarga una serie de cierre para un ticker dado.
    Devuelve una Series limpia o una Series vacía si falla.
    """
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if data is None or data.empty:
            return pd.Series(dtype="float64")

        if "Close" not in data.columns:
            return pd.Series(dtype="float64")

        series = data["Close"].copy()
        series.name = ticker
        return series.dropna()

    except Exception:
        return pd.Series(dtype="float64")


def load_market_data(period="6mo", interval="1d"):
    """
    Carga datos de mercado para:
    - Brent
    - VIX
    - DXY

    Devuelve un DataFrame con columnas:
    ['brent', 'vix', 'dxy']

    Si alguna serie falla, intenta seguir con las demás.
    Si no hay suficientes datos, devuelve DataFrame vacío.
    """
    brent = _download_close("BZ=F", period=period, interval=interval)
    vix = _download_close("^VIX", period=period, interval=interval)
    dxy = _download_close("DX-Y.NYB", period=period, interval=interval)

    series_map = {
        "brent": brent,
        "vix": vix,
        "dxy": dxy,
    }

    available = {k: v for k, v in series_map.items() if not v.empty}

    if len(available) < 2:
        return pd.DataFrame()

    df = pd.concat(available.values(), axis=1)
    df.columns = list(available.keys())

    # Si falta una columna, la creamos vacía para mantener compatibilidad
    for col in ["brent", "vix", "dxy"]:
        if col not in df.columns:
            df[col] = pd.NA

    # Orden canónico
    df = df[["brent", "vix", "dxy"]]

    # Forward-fill moderado y limpieza final
    df = df.sort_index().ffill().dropna()

    # Asegurar tipo numérico
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna()

    return df
