import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import traceback

st.set_page_config(page_title="Minimalist Indian Stock Comparator", layout="wide")

st.title("📈 Minimalist Indian Stock Comparator")
st.write("Compare three Indian stocks side by side with key metrics and charts.")

# Sidebar input
st.sidebar.header("Select Stocks")
stocks = [
    st.sidebar.text_input(f"Stock {i+1} (Ticker)", value=default)
    for i, default in enumerate(["RELIANCE.NS", "TCS.NS", "INFY.NS"])
]

period = st.sidebar.selectbox("Data Period", ["6mo", "1y", "2y", "5y"], index=1)
chart_type = st.sidebar.radio("Chart Type", ["Relative Price", "Actual Price"], index=0)

# Fetch data
@st.cache_data

def load_data(ticker, period):
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()

histories = {s: load_data(s, period) for s in stocks}

# Helper to safely extract scalar
def safe_scalar(val):
    if isinstance(val, (pd.Series, np.ndarray, list)):
        if len(val) > 0:
            return val[0]
        else:
            return np.nan
    return val

# Compute returns
def compute_returns(df):
    if df.empty:
        return np.nan
    series = df["Close"].dropna()
    if series.empty:
        return np.nan
    start_val = safe_scalar(series.iloc[[0]])
    end_val = safe_scalar(series.iloc[[-1]])
    if pd.notna(start_val) and not np.isclose(start_val, 0):
        try:
            return (end_val / start_val - 1) * 100.0
        except Exception:
            return np.nan
    return np.nan

# Compute market cap
def get_marketcap(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        return info.get("marketCap", np.nan)
    except Exception:
        return np.nan

# Format market cap
def format_mcap(val):
    val = safe_scalar(val)
    if pd.isna(val):
        return "NA"
    if val > 1e12:
        return f"{val/1e12:.2f} T"
    elif val > 1e9:
        return f"{val/1e9:.2f} B"
    elif val > 1e6:
        return f"{val/1e6:.2f} M"
    else:
        return str(val)

# Compute metrics
metrics = {
    s: {
        "Return %": compute_returns(df),
        "Market Cap": format_mcap(get_marketcap(s))
    }
    for s, df in histories.items()
}

# Display metrics
st.subheader("Key Metrics")
st.dataframe(pd.DataFrame(metrics).T.style.format({"Return %": "{:.2f}"}))

# Chart
st.subheader(f"{chart_type} Chart")
fig, ax = plt.subplots(figsize=(8, 4))

for s, df in histories.items():
    try:
        series = df["Close"]
        if isinstance(series, (pd.Series, np.ndarray, list)):
            series = pd.to_numeric(series, errors="coerce").dropna()
        else:
            series = pd.Series([series]).dropna()

        if series.empty:
            continue

        if chart_type == "Relative Price":
            base = safe_scalar(series.iloc[[0]])
            if pd.notna(base) and not np.isclose(base, 0):
                series = (series / base) * 100.0
            ax.set_ylabel("Relative Price (%)")
        else:
            ax.set_ylabel("Actual Price")

        series.plot(ax=ax, label=s)
    except Exception as e:
        st.error(f"Error plotting {s}: {e}\n{traceback.format_exc()}")

ax.legend()
st.pyplot(fig)

st.caption("Data from Yahoo Finance via yfinance. All values approximate.")
