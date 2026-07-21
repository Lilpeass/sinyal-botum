"""
Sinyal Botu - GitHub Actions ile 7/24 çalışan, Telegram'a bildirim gönderen versiyon.

Bu script, Claude ile birlikte tarayıcıda kurduğumuz "Sinyal Paneli"nin
aynı mantığını kullanır (RSI + SMA trend filtresi), ama bir web sayfası
yerine GitHub'ın sunucularında periyodik olarak çalışır ve sinyal
çıktığında Telegram üzerinden bildirim gönderir.

AYARLAR (CONFIG) - istersen aşağıdaki değerleri backtest/optimizasyon
sonuçlarına göre değiştirebilirsin. Şu anki değerler, panelde bulduğumuz
"RSI 30/75 + SMA100" kombinasyonuna karşılık geliyor.
"""

import os
import json
import requests

# ----------------------------------------------------------------------
# AYARLAR - paneldeki "Ayarları Optimize Et" sonucuna göre güncelleyebilirsin
# ----------------------------------------------------------------------
SYMBOL = "BTCUSDT"          # izlenecek parite (panel ile aynı isimlendirme, aşağıda Coinbase karşılığına çevriliyor)
INTERVAL = "5m"             # mum periyodu

# Binance yerine Coinbase kullanıyoruz çünkü GitHub Actions sunucuları ABD'de barınıyor
# ve Binance.com ABD IP'lerinden gelen istekleri (HTTP 451) engelliyor.
COINBASE_SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "SOLUSDT": "SOL-USD",
    "BNBUSDT": "BNB-USD",
    "XRPUSDT": "XRP-USD",
}
INTERVAL_TO_GRANULARITY = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}

OVERSOLD = 30                # RSI bu değerin altındaysa + trend uygunsa -> AL
OVERBOUGHT = 75               # RSI bu değerin üstündeyse + trend uygunsa -> SAT
SMA_LONG = 100                 # trend filtresi için kullanılan hareketli ortalama periyodu
SL_MULT = 1.0                  # zarar-kes çarpanı (oynaklığa göre)
TP_MULT = 1.2                  # kâr-al çarpanı (oynaklığa göre)
HOLD_MINUTES = 180             # önerilen tutma süresi (bilgi amaçlı, mesaja eklenir)

STATE_FILE = "state.json"      # aynı sinyali tekrar tekrar bildirmemek için durum dosyası

# ----------------------------------------------------------------------
# TELEGRAM BİLGİLERİ - Bunları GitHub repo Secrets üzerinden alacağız,
