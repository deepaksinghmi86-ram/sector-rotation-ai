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
# MOMENTUM ENGINE
# ===============================

def get_score(symbol):
    data = yf.download(symbol, period="6mo", progress=False)
    
    if data.empty:
        return 0

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if len(close) < 60:
        return 0

    # 4 Week Momentum
    mom_4w = (close.iloc[-1] / close.iloc[-20]) - 1

    # 12 Week Momentum
    mom_12w = (close.iloc[-1] / close.iloc[-60]) - 1

    # Volatility Adjustment
    vol = close.pct_change().rolling(20).std().iloc[-1]

    if pd.isna(vol) or vol == 0:
        vol = 0.01

    score = (mom_4w * 0.4 + mom_12w * 0.6) / vol

    return score


# ===============================
# MARKET REGIME FILTER
# ===============================

nifty = yf.download("^NSEI", period="1y", progress=False)

nifty_close = nifty["Close"]

if isinstance(nifty_close, pd.DataFrame):
    nifty_close = nifty_close.iloc[:, 0]

latest = nifty_close.iloc[-1]
ma200 = nifty_close.rolling(200).mean().iloc[-1]

market_mode = "RISK ON ✅" if latest > ma200 else "RISK OFF ⚠️"


# ===============================
# CALCULATE RANKINGS
# ===============================

scores = {}

for name, symbol in sectors.items():
    scores[name] = get_score(symbol)

ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ===============================
# TELEGRAM MESSAGE
# ===============================

message = f"📊 Institutional Weekly Sector Rotation\n\n"
message += f"Market Mode: {market_mode}\n\n"

for i, (sector, score) in enumerate(ranked, 1):
    message += f"{i}. {sector}  ({round(score,2)})\n"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": message
})

print(response.text)
# fresh deploy trigger
