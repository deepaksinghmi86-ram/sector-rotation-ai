# sector-rotation-ai
AI based sector rotation telegram bot
import requests
import yfinance as yf
import pandas as pd
import os
import numpy as np

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_score(symbol):
    data = yf.download(symbol, period="6mo", progress=False)
    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if len(close) < 60:
        return 0

    # 4 Week Momentum
    mom_4w = (close.iloc[-1] / close.iloc[-20]) - 1

    # 12 Week Momentum
    mom_12w = (close.iloc[-1] / close.iloc[-60]) - 1

    # Volatility
    vol = close.pct_change().rolling(20).std().iloc[-1]
    vol_score = 1 / vol if vol != 0 else 0

    final_score = (mom_4w * 0.4) + (mom_12w * 0.4) + (vol_score * 0.2)

    return final_score

# Market Regime
nifty = yf.download("^NSEI", period="6mo", progress=False)
nifty_close = nifty["Close"]

if isinstance(nifty_close, pd.DataFrame):
    nifty_close = nifty_close.iloc[:, 0]

ma50 = nifty_close.rolling(50).mean().iloc[-1]
latest = nifty_close.iloc[-1]

market_mode = "RISK ON ✅" if latest > ma50 else "RISK OFF ⚠️"


    sectors = {
    "BANK": "^NSEBANK",
    "FINANCIAL_SERVICES": "^CNXFINANCE",
    "IT": "^CNXIT",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "METAL": "^CNXMETAL",
    "REALTY": "^CNXREALTY",
    "ENERGY": "^CNXENERGY",
    "PSU_BANK": "^CNXPSUBANK",
    "MEDIA": "^CNXMEDIA",
    "INFRA": "^CNXINFRA",
    "CONSUMPTION": "^CNXCONSUMPTION",
    "OIL_GAS": "^CNXOILGAS",
    "HEALTHCARE": "^CNXHEALTHCARE"
}

scores = {}

for name, symbol in sectors.items():
    scores[name] = get_score(symbol)

ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

message = f"📊 Institutional Sector Report\n\nMarket Mode: {market_mode}\n\n"

for i, (sector, score) in enumerate(ranked[:3], 1):
    message += f"{i}️⃣ {sector} (Score: {round(score,2)})\n"

message += "\nSuggested Allocation:\nTop 2 → 60%\n3rd → 20%\nCash → 20%"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": message
})
