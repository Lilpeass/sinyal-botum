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
SYMBOL = "BTCUSDT"          # izlenecek parite (ETHUSDT, SOLUSDT vb. de olur)
INTERVAL = "5m"             # mum periyodu
OVERSOLD = 30                # RSI bu değerin altındaysa + trend uygunsa -> AL
OVERBOUGHT = 75               # RSI bu değerin üstündeyse + trend uygunsa -> SAT
SMA_LONG = 100                 # trend filtresi için kullanılan hareketli ortalama periyodu
SL_MULT = 1.0                  # zarar-kes çarpanı (oynaklığa göre)
TP_MULT = 1.2                  # kâr-al çarpanı (oynaklığa göre)
HOLD_MINUTES = 180             # önerilen tutma süresi (bilgi amaçlı, mesaja eklenir)

STATE_FILE = "state.json"      # aynı sinyali tekrar tekrar bildirmemek için durum dosyası

# ----------------------------------------------------------------------
# TELEGRAM BİLGİLERİ - Bunları GitHub repo Secrets üzerinden alacağız,
# kodun içine YAZMA. (README.md'de nasıl kurulacağı anlatılıyor.)
# ----------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_klines(symbol, interval, limit=150):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    closes = [float(k[4]) for k in data]
    return closes


def sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(len(closes) - period, len(closes)):
        diff = closes[i] - closes[i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def volatility_pct(closes, window=20):
    recent = closes[-window:]
    high, low = max(recent), min(recent)
    last = closes[-1]
    return (high - low) / last * 100


def compute_verdict(closes):
    price = closes[-1]
    rsi_val = rsi(closes, 14)
    sma_long_val = sma(closes, SMA_LONG)

    if rsi_val is None or sma_long_val is None:
        return {"verdict": "bekle", "reason": "Yeterli veri yok."}

    vol = volatility_pct(closes)

    if rsi_val < OVERSOLD and price > sma_long_val:
        stop_loss = price * (1 - (vol * SL_MULT) / 100)
        take_profit = price * (1 + (vol * TP_MULT) / 100)
        reason = (
            f"RSI {rsi_val:.1f} ile {OVERSOLD} eşiğinin altında (aşırı satım) "
            f"ve fiyat SMA{SMA_LONG} ({sma_long_val:.2f}) üzerinde, yani genel trend güçlü."
        )
        return {"verdict": "al", "reason": reason, "price": price,
                "stop_loss": stop_loss, "take_profit": take_profit, "rsi": rsi_val}

    if rsi_val > OVERBOUGHT and price < sma_long_val:
        stop_loss = price * (1 + (vol * SL_MULT) / 100)
        take_profit = price * (1 - (vol * TP_MULT) / 100)
        reason = (
            f"RSI {rsi_val:.1f} ile {OVERBOUGHT} eşiğinin üstünde (aşırı alım) "
            f"ve fiyat SMA{SMA_LONG} ({sma_long_val:.2f}) altında, yani genel trend zayıf."
        )
        return {"verdict": "sat", "reason": reason, "price": price,
                "stop_loss": stop_loss, "take_profit": take_profit, "rsi": rsi_val}

    return {"verdict": "bekle", "reason": f"RSI {rsi_val:.1f}, net bir sinyal yok."}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_side": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("UYARI: TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID tanımlı değil, bildirim gönderilemedi.")
        print("Mesaj (gönderilseydi):\n", text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=15)
    resp.raise_for_status()


def main():
    closes = get_klines(SYMBOL, INTERVAL, limit=max(150, SMA_LONG + 20))
    result = compute_verdict(closes)
    state = load_state()

    verdict = result["verdict"]

    if verdict in ("al", "sat"):
        # Sadece YENİ bir sinyal olduğunda bildir (aynı sinyal sürerken tekrar tekrar spam yapmasın)
        if state.get("last_side") != verdict:
            label = "AL SİNYALİ 🟢" if verdict == "al" else "SAT SİNYALİ 🔴"
            message = (
                f"{label} — {SYMBOL}\n\n"
                f"Fiyat: ${result['price']:.2f}\n"
                f"RSI: {result['rsi']:.1f}\n"
                f"Zarar-kes: ${result['stop_loss']:.2f}\n"
                f"Kâr-al: ${result['take_profit']:.2f}\n"
                f"Önerilen süre: ~{HOLD_MINUTES/60:.1f} saat\n\n"
                f"Neden: {result['reason']}\n\n"
                f"NOT: Bu otomatik, kural bazlı bir sinyaldir. Yatırım tavsiyesi değildir, "
                f"gerçek para koymadan önce kendi değerlendirmeni yap."
            )
            send_telegram_message(message)
            print("Yeni sinyal bildirildi:", verdict)
        else:
            print("Sinyal devam ediyor, tekrar bildirim gönderilmedi:", verdict)
        state["last_side"] = verdict
    else:
        if state.get("last_side") is not None:
            print("Sinyal sona erdi, durum sıfırlandı.")
        state["last_side"] = None

    save_state(state)


if __name__ == "__main__":
    main()
