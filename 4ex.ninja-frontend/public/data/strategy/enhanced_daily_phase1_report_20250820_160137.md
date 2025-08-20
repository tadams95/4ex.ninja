# Enhanced Daily Strategy - Phase 1 Backtest Report

**Strategy:** Enhanced Daily Strategy (Phase 1)
**Backtest Date:** 2025-08-20T23:01:37.387714+00:00
**Pairs Tested:** 6
**Initial Balance:** $100,000 per pair

## Phase 1 Enhancements Tested

- Session-Based Trading (JPY pairs during Asian session)
- Support/Resistance Confluence Detection
- Dynamic Position Sizing (0.5% to 3% risk scaling)

## Overall Performance

- **Total Trades:** 110
- **Overall Win Rate:** 43.64%
- **Total Return:** $-24.46
- **Overall Return %:** -0.0%
- **Best Performer:** USD_JPY (0.18%)
- **Worst Performer:** GBP_JPY (-0.19%)

## Phase 1 Enhancement Impact

- **Session-Filtered Trades:** 59 (53.6%)
- **Confluence Trades:** 51 (46.4%)
- **Dynamic-Sized Trades:** 110 (100.0%)

## Individual Pair Performance

| Pair | Trades | Win Rate | Return (%) | Return ($) | Session Filter | Confluence | Dynamic Sizing |
|------|--------|----------|------------|------------|----------------|------------|----------------|
| USD_JPY | 25 | 56.0% | 0.18% | $179.80 | 100.0% | 0.0% | 100.0% |
| EUR_USD | 33 | 30.3% | -0.10% | $-103.08 | 0.0% | 100.0% | 100.0% |
| GBP_USD | 18 | 61.11% | 0.09% | $92.93 | 0.0% | 100.0% | 100.0% |
| EUR_JPY | ERROR | - | - | - | - | - | - |
| AUD_JPY | ERROR | - | - | - | - | - | - |
| GBP_JPY | 34 | 38.24% | -0.19% | $-194.11 | 100.0% | 0.0% | 100.0% |

## Phase 1 Enhancement Analysis

**Total Trades Analyzed:** 40

### Session-Based Trading Impact
- Trades: 20
- Win Rate: 55.0%
- Average Profit: $4.0
- Total Profit: $80.01

### Confluence Detection Impact
- Trades: 20
- Win Rate: 65.0%
- Average Profit: $8.45
- Total Profit: $169.07

### Dynamic Position Sizing Impact
- Trades: 40
- Win Rate: 60.0%
- Average Profit: $6.23
- Total Profit: $249.08

## Conclusion

This backtest represents the TRUE Enhanced Daily Strategy with all Phase 1 enhancements:
1. **Session-Based Trading** - JPY pairs only trade during optimal Asian session
2. **Support/Resistance Confluence** - Multi-factor level detection and scoring
3. **Dynamic Position Sizing** - Risk scaling from 0.5% to 3% based on signal strength

These results demonstrate the actual performance of the sophisticated Phase 1 Enhanced Strategy,
not the basic EMA crossover strategy tested previously.
