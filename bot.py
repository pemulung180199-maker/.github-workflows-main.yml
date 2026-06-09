import ccxt
import pandas as pd
import requests
import os

TELEGRAM_TOKEN = os.getenv("8582961660:AAG8rAa4MlvEd1mILN2tWDFS_940IyA4wc0")
TELEGRAM_CHAT_ID = os.getenv("7182146237")
TIMEFRAME = '1h'
MIN_VOLUME = 10_000_000 

# MENGGUNAKAN BYBIT (Lebih ramah terhadap server GitHub/Cloud)
exchange = ccxt.bybit({'options': {'defaultType': 'linear'}})

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

def calculate_ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def get_active_symbols():
    try:
        tickers = exchange.fetch_tickers()
        symbols = []
        for symbol, data in tickers.items():
            # Filter USDT pairs dengan volume > 10jt
            if symbol.endswith(':USDT') and data['quoteVolume'] >= MIN_VOLUME:
                symbols.append(symbol)
        return symbols
    except Exception as e:
        print(f"Gagal ambil ticker: {e}")
        return []

def check_logic():
    symbols = get_active_symbols()
    print(f"Mengecek {len(symbols)} koin di Bybit...")
    
    for symbol in symbols:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=210)
            if len(bars) < 200: continue
            
            df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            df['ema21'] = calculate_ema(df['close'], 21)
            df['ema55'] = calculate_ema(df['close'], 55)
            df['ema200'] = calculate_ema(df['close'], 200)
            
            last = df.iloc[-2]
            high, low = last['high'], last['low']
            emas = {'EMA 21': last['ema21'], 'EMA 55': last['ema55'], 'EMA 200': last['ema200']}
            
            for name, val in emas.items():
                if low <= val <= high:
                    clean_name = symbol.split(':')[0]
                    msg = (f"🔔 *EMA ALERT (Bybit Futures)*\n\n"
                           f"Symbol: `{clean_name}`\n"
                           f"Indicator: *{name}*\n"
                           f"Range: {low} - {high}\n"
                           f"Close: {last['close']}")
                    send_telegram(msg)
        except:
            continue

if __name__ == "__main__":
    check_logic()
