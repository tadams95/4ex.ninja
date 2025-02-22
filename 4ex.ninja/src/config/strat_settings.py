# Config for strategies
STRATEGIES = {
    "AUD_USD_H4": {
        "pair": "AUD_USD",
        "timeframe": "H4",
        "slow_ma": 160,
        "fast_ma": 50,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "AUD_USD_D": {
        "pair": "AUD_USD",
        "timeframe": "D",
        "slow_ma": 60,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "EUR_GBP_H4": {
        "pair": "EUR_GBP",
        "timeframe": "H4",
        "slow_ma": 90,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "EUR_GBP_D": {
        "pair": "EUR_GBP",
        "timeframe": "D",
        "slow_ma": 60,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "EUR_USD_H4": {
        "pair": "EUR_USD",
        "timeframe": "H4",
        "slow_ma": 140,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "EUR_USD_D": {
        "pair": "EUR_USD",
        "timeframe": "D",
        "slow_ma": 20,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "GBP_JPY_H4": {
        "pair": "GBP_JPY",
        "timeframe": "H4",
        "slow_ma": 70,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.03,  # Adjusted for JPY pairs
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "GBP_JPY_D": {
        "pair": "GBP_JPY",
        "timeframe": "D",
        "slow_ma": 20,
        "fast_ma": 160,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.03,  # Adjusted for JPY pairs
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "GBP_USD_H4": {
        "pair": "GBP_USD",
        "timeframe": "H4",
        "slow_ma": 50,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "GBP_USD_D": {
        "pair": "GBP_USD",
        "timeframe": "D",
        "slow_ma": 80,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "NZD_USD_H4": {
        "pair": "NZD_USD",
        "timeframe": "H4",
        "slow_ma": 110,
        "fast_ma": 50,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "NZD_USD_D": {
        "pair": "NZD_USD",
        "timeframe": "D",
        "slow_ma": 40,
        "fast_ma": 30,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "USD_CAD_H4": {
        "pair": "USD_CAD",
        "timeframe": "H4",
        "slow_ma": 50,
        "fast_ma": 80,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "USD_CAD_D": {
        "pair": "USD_CAD",
        "timeframe": "D",
        "slow_ma": 100,
        "fast_ma": 40,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0003,
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
    "USD_JPY_H4": {
        "pair": "USD_JPY",
        "timeframe": "H4",
        "slow_ma": 90,
        "fast_ma": 30,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.03,  # Adjusted for JPY pairs
        "min_rr_ratio": 1.5,
        "sleep_seconds": 14400,  # 4 hours
    },
    "USD_JPY_D": {
        "pair": "USD_JPY",
        "timeframe": "D",
        "slow_ma": 20,
        "fast_ma": 10,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.03,  # Adjusted for JPY pairs
        "min_rr_ratio": 1.5,
        "sleep_seconds": 86400,  # 24 hours
    },
}
