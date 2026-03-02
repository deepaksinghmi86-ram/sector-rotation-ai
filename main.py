import requests
import yfinance as yf
import pandas as pd

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

sectors = {
    "BANK": "^NSEBANK",
    "IT": "^CNXIT",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
    "ENERGY": "^CNXENERGY"
}

scores = {}

for name, symbol in sectors.items():
    data = yf.download(symbol, period="1mo", progress=False)
    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if len(close) < 5:
        scores[name] = 0
        continue

    latest = float(close.iloc[-1])
    previous = float(close.iloc[0])

    scores[name] = (latest / previous) - 1

ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

message = "📊 Weekly Sector Momentum\n\n"

for i, (sector, score) in enumerate(ranked, 1):
    message += f"{i}. {sector} ({round(score*100,2)}%)\n"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": message
})
