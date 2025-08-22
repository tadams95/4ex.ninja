#!/usr/bin/env python3
"""
Confidence Analysis Risk Management for Enhanced Daily Strategy V2

This module implements the risk management framework based on our comprehensive
confidence analysis. It provides realistic performance expectations and 
conservative risk controls to ensure V2 strategy success in live trading.

Key Features:
- Reality-adjusted performance expectations
- Conservative position sizing
- Adaptive risk management based on live performance
- Emergency exit protocols
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import numpy as np

class ConfidenceAnalysisRiskManager:
    """
    Risk Management based on comprehensive confidence analysis
    
    Implements conservative risk controls with realistic performance expectations
    derived from our 4,436 trade validation and confidence analysis.
    """
    
    def __init__(self, account_balance: float = 10000):
        """
        Initialize confidence-based risk manager
        
        Args:
            account_balance: Current account balance for risk calculations
        """
        self.logger = logging.getLogger(__name__)
        self.account_balance = account_balance
        self.initial_balance = account_balance
        
        # Confidence analysis parameters (from our detailed analysis)
        self.confidence_parameters = {
            "reality_adjustment_factor": -0.14,  # 14% reduction from backtest
            "spread_impact": -0.05,              # 5% reduction for spreads
            "slippage_impact": -0.03,            # 3% reduction for slippage
            "market_regime_risk": -0.06,         # 6% reduction for regime changes
            "overall_confidence": 0.75           # 75% confidence level
        }
        
        # Conservative risk limits (learned from confidence analysis)
        self.risk_limits = {
            "max_risk_per_trade": 0.005,         # 0.5% per trade (conservative)
            "max_daily_risk": 0.015,             # 1.5% daily maximum
            "max_weekly_risk": 0.05,             # 5% weekly maximum
            "max_monthly_risk": 0.15,            # 15% monthly maximum
            "emergency_exit_drawdown": 0.20,     # 20% account drawdown emergency
            "max_consecutive_losses": 10,        # Stop trading after 10 losses
            "min_account_balance": 500           # Minimum account to continue
        }
        
        # Performance tracking for adaptive management
        self.performance_tracking = {
            "trades_today": 0,
            "daily_risk_used": 0.0,
            "weekly_risk_used": 0.0,
            "monthly_risk_used": 0.0,
            "consecutive_losses": 0,
            "current_drawdown": 0.0,
            "max_drawdown": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "live_win_rate": 0.0,
            "live_profit_factor": 0.0
        }
        
        # Emergency protocols
        self.emergency_status = {
            "emergency_mode": False,
            "stop_new_trades": False,
            "reason": None,
            "triggered_at": None
        }
        
        self.logger.info("Confidence Analysis Risk Manager initialized")
        self.logger.info(f"Account Balance: ${account_balance:,.2f}")
        self.logger.info(f"Conservative Risk Per Trade: {self.risk_limits['max_risk_per_trade']*100:.1f}%")
    
    def adjust_backtest_expectations(self, backtest_performance: Dict) -> Dict:
        """
        Apply confidence analysis adjustments to backtest results
        
        Args:
            backtest_performance: Raw backtest performance metrics
            
        Returns:
            Adjusted realistic performance expectations
        """
        
        adjusted_performance = backtest_performance.copy()
        
        # Adjust win rate with confidence factors
        original_win_rate = backtest_performance.get('win_rate', 60.0)
        reality_adjustment = original_win_rate * self.confidence_parameters['reality_adjustment_factor']
        spread_adjustment = original_win_rate * self.confidence_parameters['spread_impact']
        slippage_adjustment = original_win_rate * self.confidence_parameters['slippage_impact']
        regime_adjustment = original_win_rate * self.confidence_parameters['market_regime_risk']
        
        adjusted_win_rate = original_win_rate + reality_adjustment + spread_adjustment + slippage_adjustment + regime_adjustment
        
        # Adjust profit factor similarly
        original_pf = backtest_performance.get('profit_factor', 2.0)
        adjusted_pf = original_pf * (1 + self.confidence_parameters['reality_adjustment_factor'] * 0.5)
        
        adjusted_performance.update({
            'realistic_win_rate': max(40.0, adjusted_win_rate),  # Floor at 40%
            'realistic_profit_factor': max(1.2, adjusted_pf),   # Floor at 1.2
            'confidence_level': self.confidence_parameters['overall_confidence'] * 100,
            'adjustments_applied': {
                'reality_adjustment': reality_adjustment,
                'spread_impact': spread_adjustment,
                'slippage_impact': slippage_adjustment,
                'market_regime_impact': regime_adjustment,
                'total_adjustment': reality_adjustment + spread_adjustment + slippage_adjustment + regime_adjustment
            }
        })
        
        self.logger.info(f"Applied confidence adjustments: {original_win_rate:.1f}% → {adjusted_win_rate:.1f}% win rate")
        return adjusted_performance
    
    def calculate_position_size(self, trade_signal: Dict) -> Dict:
        """
        Calculate conservative position size based on confidence analysis
        
        Args:
            trade_signal: Trading signal with entry, SL, TP
            
        Returns:
            Position sizing information with risk controls
        """
        
        # Check if trading is allowed
        if not self.is_trading_allowed():
            return {
                "position_size": 0.0,
                "risk_amount": 0.0,
                "allowed": False,
                "reason": self.get_trading_restriction_reason()
            }
        
        # Base risk calculation
        base_risk_amount = self.account_balance * self.risk_limits['max_risk_per_trade']
        
        # Adjust risk based on recent performance
        risk_multiplier = self.get_adaptive_risk_multiplier()
        adjusted_risk_amount = base_risk_amount * risk_multiplier
        
        # Check daily risk limits
        remaining_daily_risk = (self.account_balance * self.risk_limits['max_daily_risk']) - self.performance_tracking['daily_risk_used']
        final_risk_amount = min(adjusted_risk_amount, remaining_daily_risk, base_risk_amount)
        
        # Calculate position size
        entry_price = trade_signal.get('entry_price', 0)
        stop_loss = trade_signal.get('stop_loss', 0)
        
        if entry_price > 0 and stop_loss > 0:
            pip_value = trade_signal.get('pip_value', 0.0001)
            pip_risk = abs(entry_price - stop_loss) / pip_value
            
            if pip_risk > 0:
                # Simplified position size calculation
                position_size = final_risk_amount / (pip_risk * 10)  # $10 per pip assumption
                position_size = max(0.01, min(position_size, 1.0))  # 0.01 to 1.0 lot range
            else:
                position_size = 0.01
        else:
            position_size = 0.01
        
        # Apply additional conservative limits based on confidence
        if self.performance_tracking['consecutive_losses'] >= 5:
            position_size *= 0.5  # Reduce position size after 5 losses
        
        if self.performance_tracking['consecutive_losses'] >= 8:
            position_size *= 0.25  # Further reduce after 8 losses
        
        return {
            "position_size": round(position_size, 2),
            "risk_amount": round(final_risk_amount, 2),
            "risk_multiplier": risk_multiplier,
            "pip_risk": round(pip_risk, 1) if 'pip_risk' in locals() else 0,
            "allowed": True,
            "confidence_adjusted": True
        }
    
    def get_adaptive_risk_multiplier(self) -> float:
        """
        Calculate adaptive risk multiplier based on live performance
        
        Returns:
            Risk multiplier (0.25 to 1.0)
        """
        
        base_multiplier = 1.0
        
        # Adjust based on live win rate vs expected
        if self.performance_tracking['total_trades'] >= 10:
            expected_win_rate = 50.0  # Conservative baseline
            actual_win_rate = self.performance_tracking['live_win_rate']
            
            if actual_win_rate < expected_win_rate - 10:
                base_multiplier *= 0.5  # Reduce risk if underperforming
            elif actual_win_rate < expected_win_rate - 5:
                base_multiplier *= 0.75
        
        # Adjust based on consecutive losses
        if self.performance_tracking['consecutive_losses'] >= 3:
            base_multiplier *= 0.8
        if self.performance_tracking['consecutive_losses'] >= 5:
            base_multiplier *= 0.6
        if self.performance_tracking['consecutive_losses'] >= 8:
            base_multiplier *= 0.4
        
        # Adjust based on current drawdown
        if self.performance_tracking['current_drawdown'] > 0.10:  # 10% drawdown
            base_multiplier *= 0.7
        if self.performance_tracking['current_drawdown'] > 0.15:  # 15% drawdown
            base_multiplier *= 0.5
        
        return max(0.25, min(base_multiplier, 1.0))
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed based on risk limits"""
        
        # Emergency mode check
        if self.emergency_status['emergency_mode']:
            return False
        
        # Account balance check
        if self.account_balance < self.risk_limits['min_account_balance']:
            return False
        
        # Consecutive losses check
        if self.performance_tracking['consecutive_losses'] >= self.risk_limits['max_consecutive_losses']:
            return False
        
        # Drawdown check
        if self.performance_tracking['current_drawdown'] >= self.risk_limits['emergency_exit_drawdown']:
            return False
        
        # Daily risk limit check
        if self.performance_tracking['daily_risk_used'] >= (self.account_balance * self.risk_limits['max_daily_risk']):
            return False
        
        return True
    
    def get_trading_restriction_reason(self) -> str:
        """Get reason for trading restriction"""
        
        if self.emergency_status['emergency_mode']:
            return f"Emergency mode: {self.emergency_status['reason']}"
        
        if self.account_balance < self.risk_limits['min_account_balance']:
            return f"Account balance too low: ${self.account_balance}"
        
        if self.performance_tracking['consecutive_losses'] >= self.risk_limits['max_consecutive_losses']:
            return f"Too many consecutive losses: {self.performance_tracking['consecutive_losses']}"
        
        if self.performance_tracking['current_drawdown'] >= self.risk_limits['emergency_exit_drawdown']:
            return f"Emergency drawdown reached: {self.performance_tracking['current_drawdown']*100:.1f}%"
        
        daily_risk_used_pct = (self.performance_tracking['daily_risk_used'] / self.account_balance) * 100
        if daily_risk_used_pct >= self.risk_limits['max_daily_risk'] * 100:
            return f"Daily risk limit reached: {daily_risk_used_pct:.1f}%"
        
        return "Unknown restriction"
    
    def update_trade_result(self, trade_result: Dict) -> None:
        """
        Update performance tracking with trade result
        
        Args:
            trade_result: Trade result with outcome, pips, etc.
        """
        
        self.performance_tracking['total_trades'] += 1
        
        pips = trade_result.get('pips', 0)
        risk_amount = trade_result.get('risk_amount', 0)
        
        if trade_result.get('result') == 'win':
            self.performance_tracking['winning_trades'] += 1
            self.performance_tracking['consecutive_losses'] = 0
        else:
            self.performance_tracking['consecutive_losses'] += 1
            self.performance_tracking['daily_risk_used'] += risk_amount
        
        # Update account balance
        pip_value = 10  # Simplified $10 per pip
        balance_change = pips * pip_value
        self.account_balance += balance_change
        
        # Update drawdown
        if self.account_balance > self.initial_balance:
            peak_balance = self.account_balance
        else:
            peak_balance = self.initial_balance
        
        current_drawdown = (peak_balance - self.account_balance) / peak_balance
        self.performance_tracking['current_drawdown'] = current_drawdown
        self.performance_tracking['max_drawdown'] = max(
            self.performance_tracking['max_drawdown'],
            current_drawdown
        )
        
        # Update win rate
        if self.performance_tracking['total_trades'] > 0:
            self.performance_tracking['live_win_rate'] = (
                self.performance_tracking['winning_trades'] / 
                self.performance_tracking['total_trades'] * 100
            )
        
        # Check for emergency conditions
        self.check_emergency_conditions()
        
        self.logger.info(f"Trade result updated: {trade_result.get('result')} | "
                        f"Win Rate: {self.performance_tracking['live_win_rate']:.1f}% | "
                        f"Consecutive Losses: {self.performance_tracking['consecutive_losses']}")
    
    def check_emergency_conditions(self) -> None:
        """Check and trigger emergency conditions if needed"""
        
        # Consecutive losses emergency
        if self.performance_tracking['consecutive_losses'] >= self.risk_limits['max_consecutive_losses']:
            self.trigger_emergency("Too many consecutive losses")
        
        # Drawdown emergency
        if self.performance_tracking['current_drawdown'] >= self.risk_limits['emergency_exit_drawdown']:
            self.trigger_emergency("Emergency drawdown level reached")
        
        # Account balance emergency
        if self.account_balance <= self.risk_limits['min_account_balance']:
            self.trigger_emergency("Account balance below minimum")
    
    def trigger_emergency(self, reason: str) -> None:
        """Trigger emergency mode"""
        
        self.emergency_status.update({
            "emergency_mode": True,
            "stop_new_trades": True,
            "reason": reason,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        })
        
        self.logger.critical(f"EMERGENCY MODE TRIGGERED: {reason}")
        self.logger.critical(f"Account Balance: ${self.account_balance:,.2f}")
        self.logger.critical(f"Current Drawdown: {self.performance_tracking['current_drawdown']*100:.1f}%")
        self.logger.critical(f"Consecutive Losses: {self.performance_tracking['consecutive_losses']}")
    
    def get_risk_status(self) -> Dict:
        """Get comprehensive risk status"""
        
        return {
            "account_balance": self.account_balance,
            "initial_balance": self.initial_balance,
            "trading_allowed": self.is_trading_allowed(),
            "emergency_status": self.emergency_status,
            "performance_tracking": self.performance_tracking,
            "risk_limits": self.risk_limits,
            "confidence_parameters": self.confidence_parameters,
            "adaptive_risk_multiplier": self.get_adaptive_risk_multiplier(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def reset_daily_tracking(self) -> None:
        """Reset daily tracking metrics (call at start of each day)"""
        
        self.performance_tracking['trades_today'] = 0
        self.performance_tracking['daily_risk_used'] = 0.0
        
        self.logger.info("Daily risk tracking reset")


# Test function
def test_confidence_risk_manager():
    """Test the confidence analysis risk manager"""
    
    # Initialize risk manager
    risk_manager = ConfidenceAnalysisRiskManager(account_balance=10000)
    
    # Test backtest adjustment
    backtest_performance = {
        'win_rate': 68.0,
        'profit_factor': 4.14,
        'total_trades': 462
    }
    
    adjusted = risk_manager.adjust_backtest_expectations(backtest_performance)
    print("Confidence Analysis Risk Manager Test")
    print("=" * 50)
    print(f"Original Win Rate: {backtest_performance['win_rate']:.1f}%")
    print(f"Adjusted Win Rate: {adjusted['realistic_win_rate']:.1f}%")
    print(f"Confidence Level: {adjusted['confidence_level']:.0f}%")
    
    # Test position sizing
    test_signal = {
        'entry_price': 150.0,
        'stop_loss': 149.0,
        'take_profit': 152.0,
        'pip_value': 0.01
    }
    
    position_info = risk_manager.calculate_position_size(test_signal)
    print(f"\nPosition Size: {position_info['position_size']}")
    print(f"Risk Amount: ${position_info['risk_amount']}")
    print(f"Trading Allowed: {position_info['allowed']}")
    
    # Test risk status
    status = risk_manager.get_risk_status()
    print(f"\nEmergency Mode: {status['emergency_status']['emergency_mode']}")
    print(f"Current Drawdown: {status['performance_tracking']['current_drawdown']*100:.1f}%")
    
    return risk_manager

if __name__ == "__main__":
    test_confidence_risk_manager()
