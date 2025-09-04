# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import pandas_ta as ta
import config
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders

from datetime import datetime, timezone
import time

client = API(access_token=config.OANDA_API_KEY)


timeframe = "M1"
instrument = "GBP_JPY"


def get_candles(tf):
    params = {
        "granularity": tf,
        "price": "A"
    }

    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    candles = client.request(r)['candles']

    data = []

    for c in candles:
        if c["complete"]:
            data.append({
                "time": c["time"],
                "open": float(c["ask"]["o"]),
                "high": float(c["ask"]["h"]),
                "low": float(c["ask"]["l"]),
                "close": float(c["ask"]["c"])
            })

    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])

    return df


# Function to calculate indicators
def calculate_indicators(df):
    # EMAs
    df["EMA_5"] = ta.ema(df["close"], length=5)
    df["EMA_8"] = ta.ema(df["close"], length=8)

    # ATR
    df["ATR_14"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    return df


# Function to place an order
def place_order(stop_loss, take_profit):
    data = {
        "order": {
            "instrument": instrument,
            "units": 1,
            "type": "MARKET",
            "stopLossOnFill": {"price": f"{stop_loss:.3f}"},
            "takeProfitOnFill": {"price": f"{take_profit:.3f}"},
        }
    }

    r = orders.OrderCreate(config.OANDA_ACCOUNT_ID, data=data)
    client.request(r)
    print(
        f"Placed order for {instrument} with stop loss at {round(stop_loss, 3)} and take profit at {round(take_profit, 3)}.")


# Function to check for EMA Crossover signals
def ema_crossover(df):
    tp_ratio = 1.5

    # Check if the 5-period EMA crosses above the 8-period EMA
    last_candle = df.iloc[-1]
    previous_candle = df.iloc[-2]

    # Crossover Buy Signal (EMA 5 crosses above EMA 8)
    if last_candle['EMA_5'] > last_candle['EMA_8'] and previous_candle['EMA_5'] < previous_candle['EMA_8']:
        print("Buy Signal: EMA 5 crossed above EMA 8")
        entry_price = last_candle['close']
        stop_loss = entry_price - last_candle['ATR_14']
        stop_distance = entry_price - stop_loss
        take_profit = entry_price + (stop_distance * tp_ratio)
        place_order(stop_loss, take_profit)
    else:
        print("Strategy conditions not met")


def run_bot():
    print("Starting trading bot")
    last_checked = None

    while True:
        current_time = datetime.now(timezone.utc)

        # Check for a new 15 minute candle
        # if current_time.minute % 15 == 0 and current_time.second < 10:
        if current_time.minute % 1 == 0 and current_time.second < 10:
            # Check if the 15-minute interval has changed since the last check
            if last_checked != current_time.minute:
                print(f"Current time: {current_time}")
                print("Checking for trade signals")
                price = get_candles(timeframe)
                price = calculate_indicators(price)
                ema_crossover(price)
                last_checked = current_time.minute  # Update to prevent re-triggering

        time.sleep(1)


run_bot()

