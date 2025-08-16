# Live Trading System Documentation
## 4ex.ninja OANDA Integration

**Status:** ✅ **PRODUCTION READY**  
**Last Updated:** August 15, 2025  
**Live Data:** ✅ OANDA API Connected  
**Strategies:** ✅ 3 Strategy Types Available  
**Risk Management:** ✅ Comprehensive Controls  

---

## 🎯 Overview

The Live Trading System seamlessly connects your **backtested strategies** to **live OANDA data** for real-time automated trading. All strategies from the backtesting framework work directly with live data without modification.

### **Key Features:**
- ✅ **Real-time OANDA data feeds** (M1, M5, M15, M30, H1, H4, D)
- ✅ **Automated strategy execution** with all 3 strategy types
- ✅ **Comprehensive risk management** with position sizing and limits
- ✅ **Portfolio coordination** across multiple strategies and instruments
- ✅ **Demo mode** for safe testing before live trading
- ✅ **Real-time monitoring** with detailed statistics and alerts

---

## 🚀 Quick Start

### **1. Basic Setup**
```python
from src.live_trading import LiveTradingEngine

# Create trading engine
engine = LiveTradingEngine(
    update_interval=300,    # Check signals every 5 minutes
    max_positions=5,        # Maximum 5 open positions
    risk_per_trade=0.02     # Risk 2% per trade
)
```

### **2. Add Strategies**
```python
# Add Moving Average strategy for EUR_USD
engine.add_strategy('ma_crossover', 'EUR_USD', 'M15', {
    'fast_ma': 10,
    'slow_ma': 20,
    'ma_type': 'SMA'
})

# Add RSI strategy for GBP_USD  
engine.add_strategy('rsi', 'GBP_USD', 'M15', {
    'rsi_period': 14,
    'overbought_level': 70,
    'oversold_level': 30
})

# Add Bollinger Bands strategy for USD_JPY
engine.add_strategy('bollinger', 'USD_JPY', 'H1', {
    'bb_period': 20,
    'signal_mode': 'reversal'
})
```

### **3. Start Trading**
```python
# DEMO MODE (recommended first)
engine.disable_trading()  # Signals only, no real trades
engine.start_trading()

# LIVE MODE (after testing)
engine.enable_trading()   # Real trades executed
engine.start_trading()
```

---

## 📊 System Components

### **1. Live Trading Engine** (`LiveTradingEngine`)
**Main coordinator** that manages all trading activities:

```python
engine = LiveTradingEngine(
    update_interval=300,     # Signal check frequency (seconds)
    max_positions=5,         # Maximum open positions
    risk_per_trade=0.02      # Risk per trade (2% of balance)
)

# Add multiple strategies
engine.add_strategy('ma_crossover', 'EUR_USD', 'M5', config)
engine.add_strategy('rsi', 'GBP_USD', 'M15', config)

# Control trading
engine.start_trading()     # Start the engine
engine.stop_trading()      # Stop the engine
engine.enable_trading()    # Enable real trade execution
engine.disable_trading()   # Demo mode (signals only)

# Monitor status
status = engine.get_engine_status()
```

### **2. OANDA Data Feed** (`OandaDataFeed`)
**Real-time market data** from OANDA API:

```python
from src.live_trading import OandaDataFeed

feed = OandaDataFeed()

# Get real-time data
current_data = feed.get_latest_candles('EUR_USD', 'M5', count=100)
current_price = feed.get_current_price('EUR_USD')
historical_data = feed.get_historical_data('EUR_USD', 'H1', days_back=30)

# Test connection
feed.test_connection()
```

**Supported Instruments:**
- EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD, NZD_USD, EUR_GBP, GBP_JPY

**Supported Timeframes:**
- M1 (1 minute), M5 (5 minutes), M15 (15 minutes), M30 (30 minutes)
- H1 (1 hour), H4 (4 hours), D (daily)

### **3. Position Manager** (`PositionManager`)
**Trade execution and position tracking**:

```python
from src.live_trading import PositionManager

pm = PositionManager(
    max_positions_per_instrument=1,  # Max positions per instrument
    max_total_positions=5            # Max total positions
)

# Open position from signal
position = pm.open_position(signal, strategy_name="MA_Strategy")

# Manage positions
pm.close_position(position_id)
pm.update_positions()              # Update with current prices
open_positions = pm.get_open_positions()
summary = pm.get_position_summary()
```

### **4. Risk Manager** (`RiskManager`)
**Comprehensive risk controls**:

```python
from src.live_trading import RiskManager

rm = RiskManager(
    max_risk_per_trade=0.02,    # 2% risk per trade
    max_total_risk=0.10,        # 10% total portfolio risk
    max_drawdown_limit=0.15     # 15% maximum drawdown
)

# Validate signals
is_valid, warnings = rm.validate_signal_risk(signal, account_info, positions)

# Calculate position size
position_size = rm.calculate_position_size(signal, account_info)

# Assess portfolio risk
risk_metrics = rm.assess_portfolio_risk(account_info, positions)

# Emergency stops
should_stop, reason = rm.should_stop_trading(account_info, positions)
```

---

## ⚙️ Configuration Options

### **Engine Configuration:**
```python
LiveTradingEngine(
    update_interval=300,        # Signal check frequency (seconds)
    max_positions=5,           # Maximum open positions
    risk_per_trade=0.02        # Risk per trade (fraction of balance)
)
```

### **Risk Management Configuration:**
```python
RiskManager(
    max_risk_per_trade=0.02,   # Maximum risk per individual trade
    max_total_risk=0.10,       # Maximum total portfolio risk  
    max_correlation=0.7,       # Maximum correlation between positions
    max_drawdown_limit=0.15    # Maximum acceptable drawdown
)
```

### **Strategy Configurations:**

**Moving Average Strategy:**
```python
ma_config = {
    'fast_ma': 10,                    # Fast MA period
    'slow_ma': 20,                    # Slow MA period  
    'ma_type': 'SMA',                 # 'SMA' or 'EMA'
    'min_crossover_strength': 0.1     # Minimum signal strength
}
```

**RSI Strategy:**
```python
rsi_config = {
    'rsi_period': 14,                 # RSI calculation period
    'overbought_level': 70,           # Sell signal threshold
    'oversold_level': 30,             # Buy signal threshold
    'min_rsi_strength': 0.2           # Minimum signal strength
}
```

**Bollinger Bands Strategy:**
```python
bollinger_config = {
    'bb_period': 20,                  # Bollinger Band period
    'bb_std': 2.0,                    # Standard deviation multiplier
    'signal_mode': 'reversal',        # 'reversal' or 'breakout'
    'min_band_width': 0.001           # Minimum band width for signals
}
```

---

## 🔒 Safety Features

### **1. Demo Mode**
Test strategies without real money:
```python
engine.disable_trading()    # Enable demo mode
engine.start_trading()      # Generates signals but no real trades
```

### **2. Risk Limits**
Automatic risk management:
- **Per-trade risk limits** (default 2% of balance)
- **Total portfolio risk limits** (default 10% of balance)
- **Maximum drawdown protection** (default 15%)
- **Position size limits** based on account balance
- **Margin usage monitoring**

### **3. Emergency Stops**
Automatic trading halt conditions:
- Drawdown limit exceeded
- Margin call risk (>90% margin usage)
- Total exposure exceeded
- Significant account loss detected

### **4. Signal Validation**
Every signal is validated for:
- Risk management compliance
- Position limits
- Signal quality thresholds
- Account health
- Correlation limits

---

## 📈 Monitoring & Analytics

### **Real-time Status:**
```python
status = engine.get_engine_status()
# Returns:
{
    'is_running': True,
    'is_trading_enabled': True,
    'uptime': '2:30:15',
    'active_strategies': 3,
    'open_positions': 2,
    'account_balance': 10500.0,
    'total_exposure': 0.08,
    'risk_level': 'low',
    'signals_generated': 15,
    'trades_executed': 5
}
```

### **Risk Metrics:**
```python
risk_metrics = risk_manager.assess_portfolio_risk(account_info, positions)
# Returns:
{
    'total_exposure': 0.08,      # 8% of balance exposed
    'max_drawdown': 0.03,        # 3% current drawdown
    'risk_level': 'low',         # low/medium/high/critical
    'risk_score': 25.5,          # 0-100 scale
    'warnings': ['High margin usage']
}
```

### **Position Summary:**
```python
summary = position_manager.get_position_summary()
# Returns:
{
    'total_positions': 3,
    'total_unrealized_pnl': 150.25,
    'positions_by_instrument': {'EUR_USD': 1, 'GBP_USD': 2},
    'positions_by_strategy': {'ma_crossover': 2, 'rsi': 1}
}
```

---

## 🛠️ Advanced Usage

### **Multi-Strategy Portfolio:**
```python
# Create engine with multiple strategies
engine = LiveTradingEngine()

# Trend following strategies
engine.add_strategy('ma_crossover', 'EUR_USD', 'H1', {'fast_ma': 8, 'slow_ma': 21})
engine.add_strategy('ma_crossover', 'GBP_USD', 'H1', {'fast_ma': 5, 'slow_ma': 13})

# Mean reversion strategies  
engine.add_strategy('rsi', 'USD_JPY', 'M30', {'rsi_period': 14})
engine.add_strategy('bollinger', 'AUD_USD', 'H1', {'signal_mode': 'reversal'})

# Volatility strategies
engine.add_strategy('bollinger', 'EUR_GBP', 'H4', {'signal_mode': 'breakout'})
```

### **Dynamic Strategy Management:**
```python
# Add strategies dynamically
engine.add_strategy('rsi', 'USD_CAD', 'M15', {'rsi_period': 21})

# Remove strategies
engine.remove_strategy('ma_crossover', 'EUR_USD', 'H1')

# Enable/disable trading
engine.disable_trading()  # Demo mode
engine.enable_trading()   # Live mode
```

### **Custom Risk Parameters:**
```python
# Conservative setup
conservative_engine = LiveTradingEngine(
    risk_per_trade=0.01,      # 1% per trade
    max_positions=3           # Max 3 positions
)

# Aggressive setup  
aggressive_engine = LiveTradingEngine(
    risk_per_trade=0.03,      # 3% per trade
    max_positions=8           # Max 8 positions
)
```

---

## 🧪 Testing & Validation

### **Run Complete System Test:**
```bash
cd 4ex.ninja-backend
python3 src/live_trading/test_live_system.py
```

### **Test Individual Components:**
```python
# Test data feed
from src.live_trading import OandaDataFeed
feed = OandaDataFeed()
feed.test_connection()

# Test strategy
from src.backtesting.strategies import StrategyFactory
strategy = StrategyFactory.create_strategy('ma_crossover', {})

# Test risk management
from src.live_trading import RiskManager
rm = RiskManager()
```

### **Quick Demo:**
```bash
cd 4ex.ninja-backend
python3 src/live_trading/example_live_trading.py
# Choose option 2 for 3-minute demo
```

---

## 🚨 Important Notes

### **⚠️ Before Live Trading:**
1. **Test thoroughly in demo mode** for several hours/days
2. **Verify all strategies** are generating expected signals
3. **Check risk limits** are appropriate for your account size
4. **Monitor initial trades closely** for the first few hours
5. **Start with small position sizes** until confident

### **💡 Best Practices:**
- **Start conservative:** Use 1% risk per trade initially
- **Monitor regularly:** Check engine status every few hours
- **Diversify timeframes:** Use different timeframes for different strategies
- **Diversify instruments:** Avoid over-concentration in one currency pair
- **Keep logs:** Monitor signal quality and trade performance

### **🔧 OANDA Account Requirements:**
- **Practice Account:** Recommended for initial testing
- **Live Account:** Required for real trading
- **API Access:** Ensure your account has API trading enabled
- **Sufficient Balance:** Minimum $1000 recommended for proper position sizing

---

## 📞 Support & Troubleshooting

### **Common Issues:**

**Connection Problems:**
```python
# Test OANDA connection
from src.live_trading import OandaDataFeed
feed = OandaDataFeed()
if not feed.test_connection():
    print("Check OANDA_API_KEY and OANDA_ACCOUNT_ID in .env file")
```

**No Signals Generated:**
- Check market conditions (signals may be rare in ranging markets)
- Verify strategy configuration parameters
- Ensure sufficient historical data is available
- Check timeframe vs market volatility

**Risk Manager Rejecting Signals:**
- Review risk parameters (may be too conservative)
- Check account balance and margin usage
- Verify signal quality meets minimum thresholds

### **Debug Mode:**
```python
# Enable verbose logging
engine = LiveTradingEngine(update_interval=60)  # 1-minute updates for debugging
engine.disable_trading()  # Demo mode for testing
```

---

**Status:** ✅ **READY FOR LIVE TRADING**  
**Next Steps:** Start with demo mode, then gradually enable live trading with conservative settings.
