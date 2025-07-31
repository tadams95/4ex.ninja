# Config for strategies
STRATEGIES = {
    "AUD_USD_H4": {
        "pair": "AUD_USD",
        "timeframe": "H4",
        "slow_ma": 160,
        "fast_ma": 50,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,  # Wider SL—H4 volatility
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.0002,  # Lower—catches AUD_USD (~0.0004)
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
        "min_candles": 200,
    },
    "AUD_USD_D": {
        "pair": "AUD_USD",
        "timeframe": "D",
        "slow_ma": 60,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,  # Daily—tighter
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.0003,  # Matches ~0.004-0.006
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
        "min_candles": 200,
    },
    "EUR_GBP_H4": {
        "pair": "EUR_GBP",
        "timeframe": "H4",
        "slow_ma": 90,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,  # Wider—H4
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.0001,  # Lower—EUR_GBP (~0.0002)
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "EUR_GBP_D": {
        "pair": "EUR_GBP",
        "timeframe": "D",
        "slow_ma": 60,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,  # Matches Jupyter
        "tp_atr_multiplier": 2.25,  # R/R = 1.5—catches your 5
        "min_atr_value": 0.0002,  # Lowered—EUR_GBP (~0.002-0.005)
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
    "EUR_USD_H4": {
        "pair": "EUR_USD",
        "timeframe": "H4",
        "slow_ma": 140,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.0002,  # EUR_USD (~0.0004)
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "EUR_USD_D": {
        "pair": "EUR_USD",
        "timeframe": "D",
        "slow_ma": 20,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
    "GBP_JPY_H4": {
        "pair": "GBP_JPY",
        "timeframe": "H4",
        "slow_ma": 70,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.02,  # JPY (~0.2-0.3 H4)
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "GBP_JPY_D": {
        "pair": "GBP_JPY",
        "timeframe": "D",
        "slow_ma": 20,
        "fast_ma": 160,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.03,  # JPY (~0.8-1.2 D)
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
    "GBP_USD_H4": {
        "pair": "GBP_USD",
        "timeframe": "H4",
        "slow_ma": 50,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.0002,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "GBP_USD_D": {
        "pair": "GBP_USD",
        "timeframe": "D",
        "slow_ma": 80,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
    "NZD_USD_H4": {
        "pair": "NZD_USD",
        "timeframe": "H4",
        "slow_ma": 110,
        "fast_ma": 50,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.0002,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "NZD_USD_D": {
        "pair": "NZD_USD",
        "timeframe": "D",
        "slow_ma": 40,
        "fast_ma": 30,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
    "USD_CAD_H4": {
        "pair": "USD_CAD",
        "timeframe": "H4",
        "slow_ma": 50,
        "fast_ma": 80,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.0002,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "USD_CAD_D": {
        "pair": "USD_CAD",
        "timeframe": "D",
        "slow_ma": 100,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
    "USD_JPY_H4": {
        "pair": "USD_JPY",
        "timeframe": "H4",
        "slow_ma": 90,
        "fast_ma": 30,
        "atr_period": 14,
        "sl_atr_multiplier": 2.0,
        "tp_atr_multiplier": 3.0,  # R/R = 1.5
        "min_atr_value": 0.02,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,
        "min_candles": 200,
    },
    "USD_JPY_D": {
        "pair": "USD_JPY",
        "timeframe": "D",
        "slow_ma": 20,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,  # R/R = 1.5
        "min_atr_value": 0.03,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,
        "min_candles": 200,
    },
}
