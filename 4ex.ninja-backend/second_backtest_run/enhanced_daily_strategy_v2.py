#!/usr/bin/env python3
"""
Enhanced Daily Strategy V2
Production-ready forex trading strategy based on comprehensive 10-pair validation.

Key Features:
- EMA 10/20 crossover on H4 timeframe (proven optimal)
- Realistic performance expectations (48-52% win rate)
- Validated across 4,436 historical trades
- Conservative risk management (0.5% position sizing)
- Priority pairs: USD_JPY, EUR_GBP, AUD_JPY

Performance Expectations (Live Trading):
- Win Rate: 45-55% (conservative from 62.4% backtest)
- Profit Factor: 1.8-2.5 (conservative from 3.51 backtest)
- Monthly Trades: 6-8 per pair
- Max Consecutive Losses: <10

Based on comprehensive validation from second_backtest_run/comprehensive_10_pair_test.py
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

class EnhancedDailyStrategyV2:
    """
    Enhanced Daily Strategy V2 - Validated Implementation
    
    Based on comprehensive testing of 10 currency pairs over 5 years of data.
    Implements proven EMA 10/20 crossover strategy with realistic expectations.
    """
    
    def __init__(self, account_balance: float = 10000, risk_per_trade: float = 0.005):
        """
        Initialize Enhanced Daily Strategy V2
        
        Args:
            account_balance: Account balance for position sizing
            risk_per_trade: Risk percentage per trade (0.005 = 0.5%)
        """
        self.logger = logging.getLogger(__name__)
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        
        # Strategy version and metadata
        self.version = "2.0.0"
        self.strategy_name = "Enhanced Daily Strategy V2"
        self.validation_date = "2025-08-21"
        self.validation_trades = 4436
        
        # Validated configuration from comprehensive testing
        self.validated_config = {
            "USD_JPY": {
                "ema_fast": 10,
                "ema_slow": 20,
                "timeframe": "H4",
                "priority": 1,
                "sl_pips": 25,
                "tp_pips": 50,
                "pip_value": 0.01,
                "expected_performance": {
                    "backtest_win_rate": 68.0,
                    "realistic_win_rate": 55.0,
                    "backtest_profit_factor": 4.14,
                    "realistic_profit_factor": 2.5,
                    "monthly_trades": 8,
                    "confidence_level": 80
                }
            },
            "EUR_GBP": {
                "ema_fast": 10,
                "ema_slow": 20,
                "timeframe": "H4",
                "priority": 2,
                "sl_pips": 25,
                "tp_pips": 50,
                "pip_value": 0.0001,
                "expected_performance": {
                    "backtest_win_rate": 63.4,
                    "realistic_win_rate": 51.0,
                    "backtest_profit_factor": 4.02,
                    "realistic_profit_factor": 2.3,
                    "monthly_trades": 8,
                    "confidence_level": 75
                }
            },
            "AUD_JPY": {
                "ema_fast": 10,
                "ema_slow": 20,
                "timeframe": "H4",
                "priority": 3,
                "sl_pips": 35,
                "tp_pips": 70,
                "pip_value": 0.01,
                "expected_performance": {
                    "backtest_win_rate": 63.2,
                    "realistic_win_rate": 50.0,
                    "backtest_profit_factor": 3.88,
                    "realistic_profit_factor": 2.2,
                    "monthly_trades": 6,
                    "confidence_level": 70
                }
            }
        }
        
        # Risk management parameters (from confidence analysis)
        self.risk_management = {
            "max_risk_per_trade": 0.005,  # 0.5% conservative start
            "max_consecutive_losses": 10,  # Exit strategy trigger
            "max_daily_risk": 0.015,  # 1.5% daily maximum
            "position_sizing_method": "fixed_risk",
            "emergency_exit_drawdown": 0.20  # 20% account drawdown
        }
        
        # Performance tracking
        self.trade_history = []
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "consecutive_losses": 0,
            "max_consecutive_losses": 0,
            "total_pips": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0
        }
        
        self.logger.info(f"Enhanced Daily Strategy V2 initialized")
        self.logger.info(f"Account Balance: ${account_balance:,.2f}")
        self.logger.info(f"Risk Per Trade: {risk_per_trade*100:.1f}%")
        self.logger.info(f"Supported Pairs: {list(self.validated_config.keys())}")
    
    def get_pair_config(self, pair: str) -> Optional[Dict]:
        """Get validated configuration for a specific pair"""
        return self.validated_config.get(pair)
    
    def is_supported_pair(self, pair: str) -> bool:
        """Check if pair is supported by V2 strategy"""
        return pair in self.validated_config
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_indicators(self, df: pd.DataFrame, pair: str) -> pd.DataFrame:
        """
        Calculate technical indicators for V2 strategy
        
        Args:
            df: OHLC DataFrame with H4 data
            pair: Currency pair
            
        Returns:
            DataFrame with EMA indicators added
        """
        if not self.is_supported_pair(pair):
            raise ValueError(f"Pair {pair} not supported by Enhanced Daily Strategy V2")
        
        config = self.get_pair_config(pair)
        
        # Calculate EMAs with validated parameters
        df['ema_fast'] = self.calculate_ema(df['close'], config['ema_fast'])
        df['ema_slow'] = self.calculate_ema(df['close'], config['ema_slow'])
        
        # Store configuration metadata
        df.attrs['pair'] = pair
        df.attrs['ema_fast_period'] = config['ema_fast']
        df.attrs['ema_slow_period'] = config['ema_slow']
        df.attrs['strategy_version'] = self.version
        
        return df
    
    def generate_signal(self, df: pd.DataFrame, pair: str) -> Dict[str, Any]:
        """
        Generate trading signal using validated V2 methodology
        
        Args:
            df: OHLC DataFrame with indicators
            pair: Currency pair
            
        Returns:
            Signal dictionary with trade details
        """
        if len(df) < 2:
            return self._no_signal_response(pair, "Insufficient data")
        
        if not self.is_supported_pair(pair):
            return self._no_signal_response(pair, f"Unsupported pair: {pair}")
        
        config = self.get_pair_config(pair)
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # EMA crossover detection (core V2 strategy)
        ema_fast_current = current['ema_fast']
        ema_slow_current = current['ema_slow']
        ema_fast_previous = previous['ema_fast']
        ema_slow_previous = previous['ema_slow']
        
        signal_data = {
            "pair": pair,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strategy_version": self.version,
            "current_price": float(current['close']),
            "signal": "NONE",
            "direction": None,
            "entry_price": float(current['close']),
            "stop_loss": None,
            "take_profit": None,
            "position_size": 0.0,
            "risk_amount": 0.0,
            "confidence": "medium",
            "indicators": {
                "ema_fast": float(ema_fast_current),
                "ema_slow": float(ema_slow_current),
                "ema_fast_prev": float(ema_fast_previous),
                "ema_slow_prev": float(ema_slow_previous)
            }
        }
        
        # Bull signal: EMA fast crosses above EMA slow
        if (ema_fast_current > ema_slow_current and 
            ema_fast_previous <= ema_slow_previous):
            
            entry_price = float(current['close'])
            stop_loss = entry_price - (config['sl_pips'] * config['pip_value'])
            take_profit = entry_price + (config['tp_pips'] * config['pip_value'])
            
            signal_data.update({
                "signal": "BUY",
                "direction": "LONG",
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "sl_pips": config['sl_pips'],
                "tp_pips": config['tp_pips'],
                "risk_reward_ratio": config['tp_pips'] / config['sl_pips']
            })
            
        # Bear signal: EMA fast crosses below EMA slow
        elif (ema_fast_current < ema_slow_current and 
              ema_fast_previous >= ema_slow_previous):
            
            entry_price = float(current['close'])
            stop_loss = entry_price + (config['sl_pips'] * config['pip_value'])
            take_profit = entry_price - (config['tp_pips'] * config['pip_value'])
            
            signal_data.update({
                "signal": "SELL",
                "direction": "SHORT",
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "sl_pips": config['sl_pips'],
                "tp_pips": config['tp_pips'],
                "risk_reward_ratio": config['tp_pips'] / config['sl_pips']
            })
        
        # Calculate position size if signal generated
        if signal_data["signal"] != "NONE":
            position_data = self._calculate_position_size(signal_data, config)
            signal_data.update(position_data)
            
            self.logger.info(f"V2 Signal Generated: {pair} {signal_data['signal']} at {signal_data['entry_price']}")
        
        return signal_data
    
    def _calculate_position_size(self, signal_data: Dict, config: Dict) -> Dict:
        """Calculate position size based on risk management rules"""
        
        entry_price = signal_data['entry_price']
        stop_loss = signal_data['stop_loss']
        
        # Calculate risk amount
        risk_amount = self.account_balance * self.risk_per_trade
        
        # Calculate pip risk
        pip_risk = abs(entry_price - stop_loss) / config['pip_value']
        
        # Calculate position size (lot size)
        # For forex: 1 lot = 100,000 units, 1 pip = $10 for USD pairs
        # Simplified calculation for position sizing
        if pip_risk > 0:
            position_size = risk_amount / (pip_risk * 10)  # Simplified calculation
        else:
            position_size = 0.01  # Minimum position
        
        # Apply position size limits
        position_size = max(0.01, min(position_size, 1.0))  # 0.01 to 1.0 lot range
        
        return {
            "position_size": round(position_size, 2),
            "risk_amount": round(risk_amount, 2),
            "pip_risk": round(pip_risk, 1)
        }
    
    def _no_signal_response(self, pair: str, reason: str) -> Dict[str, Any]:
        """Generate no signal response"""
        return {
            "pair": pair,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strategy_version": self.version,
            "signal": "NONE",
            "reason": reason,
            "direction": None,
            "confidence": "none"
        }
    
    def analyze_pair(self, pair: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main analysis method for Enhanced Daily Strategy V2
        
        Args:
            pair: Currency pair (e.g., 'USD_JPY')
            data: H4 OHLC DataFrame
            
        Returns:
            Complete analysis including signal and metadata
        """
        try:
            # Validate input
            if not self.is_supported_pair(pair):
                return {
                    "pair": pair,
                    "error": f"Pair {pair} not supported by Enhanced Daily Strategy V2",
                    "supported_pairs": list(self.validated_config.keys()),
                    "strategy_version": self.version
                }
            
            if len(data) < 20:  # Need minimum data for EMA calculation
                return {
                    "pair": pair,
                    "error": "Insufficient data for analysis (minimum 20 candles required)",
                    "data_length": len(data),
                    "strategy_version": self.version
                }
            
            # Calculate indicators
            df_with_indicators = self.calculate_indicators(data.copy(), pair)
            
            # Generate signal
            signal_data = self.generate_signal(df_with_indicators, pair)
            
            # Add strategy metadata
            config = self.get_pair_config(pair)
            signal_data.update({
                "strategy_metadata": {
                    "version": self.version,
                    "validation_date": self.validation_date,
                    "validation_trades": self.validation_trades,
                    "pair_priority": config['priority'],
                    "expected_monthly_trades": config['expected_performance']['monthly_trades'],
                    "expected_win_rate": config['expected_performance']['realistic_win_rate'],
                    "confidence_level": config['expected_performance']['confidence_level']
                }
            })
            
            return signal_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing {pair}: {str(e)}")
            return {
                "pair": pair,
                "error": f"Analysis failed: {str(e)}",
                "strategy_version": self.version,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information"""
        return {
            "strategy_name": self.strategy_name,
            "version": self.version,
            "validation_date": self.validation_date,
            "validation_trades": self.validation_trades,
            "supported_pairs": list(self.validated_config.keys()),
            "risk_management": self.risk_management,
            "expected_performance": {
                pair: config['expected_performance'] 
                for pair, config in self.validated_config.items()
            },
            "performance_tracking": self.performance_metrics
        }
    
    def update_performance(self, trade_result: Dict) -> None:
        """Update performance tracking with trade result"""
        self.trade_history.append(trade_result)
        self.performance_metrics['total_trades'] += 1
        
        if trade_result.get('result') == 'win':
            self.performance_metrics['winning_trades'] += 1
            self.performance_metrics['consecutive_losses'] = 0
        else:
            self.performance_metrics['losing_trades'] += 1
            self.performance_metrics['consecutive_losses'] += 1
            self.performance_metrics['max_consecutive_losses'] = max(
                self.performance_metrics['max_consecutive_losses'],
                self.performance_metrics['consecutive_losses']
            )
        
        # Update win rate
        if self.performance_metrics['total_trades'] > 0:
            self.performance_metrics['win_rate'] = (
                self.performance_metrics['winning_trades'] / 
                self.performance_metrics['total_trades'] * 100
            )
        
        # Update total pips
        self.performance_metrics['total_pips'] += trade_result.get('pips', 0)
        
        # Log performance if we hit risk thresholds
        if self.performance_metrics['consecutive_losses'] >= 8:
            self.logger.warning(f"V2 Strategy: {self.performance_metrics['consecutive_losses']} consecutive losses")
        
        if self.performance_metrics['consecutive_losses'] >= self.risk_management['max_consecutive_losses']:
            self.logger.critical(f"V2 Strategy: Emergency exit trigger - {self.performance_metrics['consecutive_losses']} consecutive losses")


# Example usage and testing functions
def test_enhanced_daily_strategy_v2():
    """Test Enhanced Daily Strategy V2 with sample data"""
    
    # Initialize strategy
    strategy = EnhancedDailyStrategyV2(account_balance=10000, risk_per_trade=0.005)
    
    # Create sample H4 data for USD_JPY
    dates = pd.date_range(start='2025-08-01', periods=50, freq='4H')
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(149.0, 151.0, 50),
        'high': np.random.uniform(149.5, 151.5, 50),
        'low': np.random.uniform(148.5, 150.5, 50),
        'close': np.random.uniform(149.0, 151.0, 50),
        'volume': np.random.uniform(1000, 5000, 50)
    })
    sample_data.set_index('timestamp', inplace=True)
    
    # Test strategy analysis
    result = strategy.analyze_pair('USD_JPY', sample_data)
    
    print("Enhanced Daily Strategy V2 Test Results:")
    print("=" * 50)
    print(f"Strategy Version: {result.get('strategy_version')}")
    print(f"Pair: {result.get('pair')}")
    print(f"Signal: {result.get('signal')}")
    print(f"Direction: {result.get('direction')}")
    print(f"Entry Price: {result.get('entry_price')}")
    print(f"Stop Loss: {result.get('stop_loss')}")
    print(f"Take Profit: {result.get('take_profit')}")
    print(f"Position Size: {result.get('position_size')}")
    print(f"Risk Amount: ${result.get('risk_amount')}")
    
    # Test strategy info
    info = strategy.get_strategy_info()
    print(f"\nSupported Pairs: {info['supported_pairs']}")
    print(f"Risk Per Trade: {info['risk_management']['max_risk_per_trade']*100}%")
    
    return strategy, result

if __name__ == "__main__":
    # Run test when script is executed directly
    test_enhanced_daily_strategy_v2()
