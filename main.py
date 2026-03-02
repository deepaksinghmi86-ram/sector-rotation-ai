import requests
import yfinance as yf
import pandas as pd
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ===============================
# ALL MAJOR NIFTY SECTOR INDICES
# ===============================

sectors = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Realty": "^CNXREALTY",
    "Nifty PSU Bank": "^CNXPSUBANK",
    "Nifty Financial Services": "^CNXFINANCE",
    "Nifty Energy": "^CNXENERGY",
    "Nifty Infra": "^CNXINFRA",
    "Nifty Media": "^CNXMEDIA"
}

# ===============================
# STOCKS INSIDE EACH SECTOR
# ===============================

sector_stocks = {
    "Nifty Bank": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
    "Nifty IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
    "Nifty Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    "Nifty Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "Nifty Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS"],
    "Nifty PSU Bank": ["SBIN.NS", "PNB.NS", "BANKBARODA.NS", "CANBK.NS"],
    "Nifty Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS"]
}

# ===============================
# SECTOR MOMENTUM ENGINE
# ===============================

def get_score(symbol):
    data = yf.download(symbol, period="6mo", progress=False)

    if data.empty:
        return 0, 0

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if len(close) < 60:
        return 0, 0

    mom_4w_now = (close.iloc[-1] / close.iloc[-20]) - 1
    mom_4w_prev = (close.iloc[-6] / close.iloc[-26]) - 1
    mom_12w = (close.iloc[-1] / close.iloc[-60]) - 1

    vol = close.pct_change().rolling(20).std().iloc[-1]
    if pd.isna(vol) or vol == 0:
        vol = 0.01

    score = (mom_4w_now * 0.4 + mom_12w * 0.6) / vol
    trend = mom_4w_now - mom_4w_prev

    return score, trend

# ===============================
# STOCK MOMENTUM ENGINE
# ===============================

def get_stock_momentum(symbol):
    data = yf.download(symbol, period="6mo", progress=False)

    if data.empty:
        return 0

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if len(close) < 60:
        return 0

    mom_4w = (close.iloc[-1] / close.iloc[-20]) - 1
    mom_12w = (close.iloc[-1] / close.iloc[-60]) - 1

    return mom_4w * 0.5 + mom_12w * 0.5


# ===============================
# CALCULATE SECTOR RANKING
# ===============================

scores = {}

for name, symbol in sectors.items():
    score, trend = get_score(symbol)
    scores[name] = (score, trend)

ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)

# ===============================
# MARKET MODE (RISK ON / OFF)
# ===============================

nifty = yf.download("^NSEI", period="6mo", progress=False)
market_mode = "RISK ON ✅"

if not nifty.empty:
    close = nifty["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    ma200 = close.rolling(200).mean().iloc[-1]
    latest = close.iloc[-1]

    if latest < ma200:
        market_mode = "RISK OFF ⚠️"

# ===============================
# TOP STOCKS INSIDE TOP SECTOR
# ===============================

top_sector = ranked[0][0]
top_stocks = []

if top_sector in sector_stocks:
    for stock in sector_stocks[top_sector]:
        score = get_stock_momentum(stock)
        top_stocks.append((stock, score))

    top_stocks = sorted(top_stocks, key=lambda x: x[1], reverse=True)[:3]

# ===============================
# TELEGRAM MESSAGE
# ===============================

message = "📊 Institutional Weekly Sector Rotation\n\n"
message += f"Market Mode: {market_mode}\n\n"

for i, (sector, values) in enumerate(ranked, 1):
    score, trend = values
    arrow = "⬆️" if trend > 0 else "⬇️"
    message += f"{i}. {sector} {arrow} ({round(score,2)})\n"

if top_stocks:
    message += f"\n🔥 Top Stocks in {top_sector}\n\n"
    for i, (stock, score) in enumerate(top_stocks, 1):
        message += f"{i}. {stock} ({round(score,2)})\n"

# ===============================
# SEND TELEGRAM MESSAGE
# ===============================

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": message
})
