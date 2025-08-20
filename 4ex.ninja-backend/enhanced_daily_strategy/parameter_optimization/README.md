# Enhanced Daily Strategy Parameter Optimization

## Current Baseline Performance (August 2025)
- **USD_JPY**: 57.69% win rate (excellent baseline)
- **GBP_JPY**: 36.84% win rate (needs improvement)
- **EUR_JPY**: 0% win rate (1 trade, needs more signals)
- **AUD_JPY**: No trades (too conservative)

## Optimization Targets

### USD_JPY (Fine-tuning)
- **Current**: EMA 20/50, RSI 50/50
- **Test**: EMA 15/45, RSI 45/55
- **Goal**: Maintain 57% win rate, improve consistency

### GBP_JPY (Major optimization)
- **Current**: EMA 20/50, RSI 50/50
- **Test**: EMA 18/42, RSI 40/60, expanded session times
- **Goal**: 36% → 45%+ win rate

### EUR_JPY (Signal generation)
- **Current**: Very conservative filtering
- **Test**: Relaxed crossover conditions, RSI 40/60
- **Goal**: Generate 10-20 trades, maintain quality

### AUD_JPY (Enable trading)
- **Current**: No signals generated
- **Test**: Looser EMA crossover detection
- **Goal**: Generate signals while avoiding false positives

## Experiment Log Template

### Experiment: [Parameter Name] - [Date]
**Hypothesis**: [What we expect to improve and why]
**Method**: [Parameters changed, backtest period, metrics]
**Results**: [Win rate, return, trade count, statistical significance]
**Conclusion**: [Keep/revert changes, next steps]

---

## Active Experiments

[Document ongoing optimization experiments here]
