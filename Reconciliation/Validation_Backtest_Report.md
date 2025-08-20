# 🧪 MA_UNIFIED_STRAT VALIDATION RESULTS
**Date:** 2025-08-19 18:44:20
**Test Period:** 2023-01-01 to 2024-12-31

## 📊 EXECUTIVE SUMMARY

- **Total Pairs Tested:** 6
- **Successful Backtests:** 6
- **Target Pairs Comparison:** 3

## 🎯 PERFORMANCE COMPARISON WITH DOCUMENTED RESULTS

| Pair | Metric | Actual | Documented | Variance | Status |
|------|--------|--------|------------|----------|--------|
| EUR_USD | Return | -0.0% | 18.0% | -18.0% | ❌ |
| EUR_USD | Sharpe | -3.97 | 1.40 | -5.37 | ❌ |
| EUR_USD | Drawdown | 0.1% | 8.0% | -7.9% | ❌ |
| EUR_USD | Trades | 16 | - | - | - |
| EUR_USD | Win Rate | 31.2% | - | - | - |

| GBP_USD | Return | 0.1% | 19.8% | -19.8% | ❌ |
| GBP_USD | Sharpe | 15.21 | 1.54 | +13.67 | ❌ |
| GBP_USD | Drawdown | 0.0% | 7.3% | -7.3% | ❌ |
| GBP_USD | Trades | 5 | - | - | - |
| GBP_USD | Win Rate | 80.0% | - | - | - |

| USD_JPY | Return | 8.4% | 17.1% | -8.7% | ⚠️ |
| USD_JPY | Sharpe | 4.81 | 1.33 | +3.48 | ❌ |
| USD_JPY | Drawdown | 4.5% | 8.4% | -3.9% | ⚠️ |
| USD_JPY | Trades | 12 | - | - | - |
| USD_JPY | Win Rate | 58.3% | - | - | - |

## 📈 DETAILED BACKTEST RESULTS

### EUR_USD
**Configuration:** Fast MA: 10, Slow MA: 20, SL ATR: 1.5, TP ATR: 2.25

- **Total Return:** -0.04%
- **Sharpe Ratio:** -3.97
- **Max Drawdown:** 0.06%
- **Total Trades:** 16
- **Win Rate:** 31.2%
- **Avg Win:** 0.0171
- **Avg Loss:** -0.0132

### GBP_USD
**Configuration:** Fast MA: 10, Slow MA: 80, SL ATR: 1.5, TP ATR: 2.25

- **Total Return:** 0.05%
- **Sharpe Ratio:** 15.21
- **Max Drawdown:** 0.01%
- **Total Trades:** 5
- **Win Rate:** 80.0%
- **Avg Win:** 0.0215
- **Avg Loss:** -0.0121

### USD_JPY
**Configuration:** Fast MA: 10, Slow MA: 20, SL ATR: 1.5, TP ATR: 2.25

- **Total Return:** 8.45%
- **Sharpe Ratio:** 4.81
- **Max Drawdown:** 4.55%
- **Total Trades:** 12
- **Win Rate:** 58.3%
- **Avg Win:** 3.6084
- **Avg Loss:** -2.6516

### AUD_USD
**Configuration:** Fast MA: 10, Slow MA: 20, SL ATR: 1.5, TP ATR: 2.25

- **Total Return:** -0.03%
- **Sharpe Ratio:** -2.40
- **Max Drawdown:** 0.08%
- **Total Trades:** 18
- **Win Rate:** 33.3%
- **Avg Win:** 0.0167
- **Avg Loss:** -0.0115

### GBP_JPY
**Configuration:** Fast MA: 10, Slow MA: 80, SL ATR: 1.5, TP ATR: 2.25

- **Total Return:** -0.38%
- **Sharpe Ratio:** -0.27
- **Max Drawdown:** 7.63%
- **Total Trades:** 7
- **Win Rate:** 42.9%
- **Avg Win:** 4.5987
- **Avg Loss:** -3.5838

### USD_CAD
**Configuration:** Fast MA: 10, Slow MA: 80, SL ATR: 1.5, TP ATR: 2.25

- **Total Return:** 0.03%
- **Sharpe Ratio:** 3.54
- **Max Drawdown:** 0.05%
- **Total Trades:** 11
- **Win Rate:** 54.5%
- **Avg Win:** 0.0184
- **Avg Loss:** -0.0136

## 🔍 ANALYSIS & CONCLUSIONS

⚠️ **High Variance Detected:** EUR_USD, GBP_USD
- Current strategy configuration may not match documented optimal parameters
- Recommend proceeding to Phase 2: Strategy Configuration Alignment

## 🎯 NEXT STEPS

1. **If High Variance:** Extract optimal parameters from documented results
2. **If Aligned:** Continue with frontend data reconciliation
3. **If Issues:** Investigate backtesting methodology differences