#!/usr/bin/env python3
"""
Comprehensive 10-Pair Strategy Validation Test
Tests our refined Enhanced Daily Strategy across all available currency pairs
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_historical_data(pair):
    """Load historical data for a specific pair"""
    file_path = f'../backtest_data/historical_data/{pair}_H4_5Y.json'
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data['data'])
        df['time'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('time')
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        return df
    except Exception as e:
        print(f"Error loading data for {pair}: {e}")
        return None

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_signals(df):
    """Generate trading signals using our refined strategy"""
    # Calculate EMAs (using faster periods from validation)
    df['ema_10'] = calculate_ema(df['close'], 10)
    df['ema_20'] = calculate_ema(df['close'], 20)
    df['rsi'] = calculate_rsi(df['close'])
    
    # Generate signals
    df['signal'] = 0
    
    # Long signal: EMA 10 crosses above EMA 20
    df.loc[(df['ema_10'] > df['ema_20']) & 
           (df['ema_10'].shift(1) <= df['ema_20'].shift(1)), 'signal'] = 1
    
    # Short signal: EMA 10 crosses below EMA 20
    df.loc[(df['ema_10'] < df['ema_20']) & 
           (df['ema_10'].shift(1) >= df['ema_20'].shift(1)), 'signal'] = -1
    
    return df

def simulate_trades(df, pair):
    """Simulate trades with realistic parameters"""
    trades = []
    position = None
    entry_price = None
    entry_time = None
    
    # Pair-specific parameters based on typical spreads and volatility
    pair_configs = {
        'EUR_USD': {'sl_pips': 30, 'tp_pips': 60, 'pip_value': 0.0001},
        'GBP_USD': {'sl_pips': 35, 'tp_pips': 70, 'pip_value': 0.0001},
        'USD_JPY': {'sl_pips': 25, 'tp_pips': 50, 'pip_value': 0.01},
        'GBP_JPY': {'sl_pips': 40, 'tp_pips': 80, 'pip_value': 0.01},
        'EUR_JPY': {'sl_pips': 35, 'tp_pips': 70, 'pip_value': 0.01},
        'AUD_JPY': {'sl_pips': 35, 'tp_pips': 70, 'pip_value': 0.01},
        'EUR_GBP': {'sl_pips': 25, 'tp_pips': 50, 'pip_value': 0.0001},
        'AUD_USD': {'sl_pips': 30, 'tp_pips': 60, 'pip_value': 0.0001},
        'USD_CAD': {'sl_pips': 30, 'tp_pips': 60, 'pip_value': 0.0001},
        'USD_CHF': {'sl_pips': 30, 'tp_pips': 60, 'pip_value': 0.0001}
    }
    
    config = pair_configs.get(pair, {'sl_pips': 30, 'tp_pips': 60, 'pip_value': 0.0001})
    sl_pips = config['sl_pips']
    tp_pips = config['tp_pips']
    pip_value = config['pip_value']
    
    for i, row in df.iterrows():
        current_signal = row['signal']
        
        # Close existing position if signal changes
        if position is not None and current_signal != 0 and current_signal != position:
            # Close at current price
            exit_price = row['open']  # Use next candle open
            pips = (exit_price - entry_price) / pip_value if position == 1 else (entry_price - exit_price) / pip_value
            profit = pips * position
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': i,
                'direction': 'long' if position == 1 else 'short',
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pips': profit,
                'result': 'win' if profit > 0 else 'loss',
                'exit_reason': 'signal_reversal'
            })
            position = None
        
        # Enter new position
        if current_signal != 0 and position is None:
            position = current_signal
            entry_price = row['open']  # Use next candle open
            entry_time = i
        
        # Check SL/TP for existing positions
        elif position is not None:
            if position == 1:  # Long position
                sl_price = entry_price - (sl_pips * pip_value)
                tp_price = entry_price + (tp_pips * pip_value)
                
                if row['low'] <= sl_price:
                    # Stop loss hit
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': i,
                        'direction': 'long',
                        'entry_price': entry_price,
                        'exit_price': sl_price,
                        'pips': -sl_pips,
                        'result': 'loss',
                        'exit_reason': 'stop_loss'
                    })
                    position = None
                elif row['high'] >= tp_price:
                    # Take profit hit
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': i,
                        'direction': 'long',
                        'entry_price': entry_price,
                        'exit_price': tp_price,
                        'pips': tp_pips,
                        'result': 'win',
                        'exit_reason': 'take_profit'
                    })
                    position = None
            
            elif position == -1:  # Short position
                sl_price = entry_price + (sl_pips * pip_value)
                tp_price = entry_price - (tp_pips * pip_value)
                
                if row['high'] >= sl_price:
                    # Stop loss hit
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': i,
                        'direction': 'short',
                        'entry_price': entry_price,
                        'exit_price': sl_price,
                        'pips': -sl_pips,
                        'result': 'loss',
                        'exit_reason': 'stop_loss'
                    })
                    position = None
                elif row['low'] <= tp_price:
                    # Take profit hit
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': i,
                        'direction': 'short',
                        'entry_price': entry_price,
                        'exit_price': tp_price,
                        'pips': tp_pips,
                        'result': 'win',
                        'exit_reason': 'take_profit'
                    })
                    position = None
    
    return trades

def analyze_performance(trades, pair):
    """Analyze trading performance"""
    if not trades:
        return {
            'pair': pair,
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'total_pips': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_consecutive_losses': 0,
            'status': 'No trades generated'
        }
    
    df_trades = pd.DataFrame(trades)
    
    total_trades = len(trades)
    wins = len(df_trades[df_trades['result'] == 'win'])
    losses = len(df_trades[df_trades['result'] == 'loss'])
    
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    
    total_pips = df_trades['pips'].sum()
    gross_profit = df_trades[df_trades['pips'] > 0]['pips'].sum()
    gross_loss = abs(df_trades[df_trades['pips'] < 0]['pips'].sum())
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    avg_win = df_trades[df_trades['pips'] > 0]['pips'].mean() if wins > 0 else 0
    avg_loss = df_trades[df_trades['pips'] < 0]['pips'].mean() if losses > 0 else 0
    
    # Calculate max consecutive losses
    consecutive_losses = 0
    max_consecutive_losses = 0
    for trade in trades:
        if trade['result'] == 'loss':
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0
    
    return {
        'pair': pair,
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'total_pips': round(total_pips, 1),
        'gross_profit': round(gross_profit, 1),
        'gross_loss': round(gross_loss, 1),
        'avg_win': round(avg_win, 1),
        'avg_loss': round(avg_loss, 1),
        'max_consecutive_losses': max_consecutive_losses,
        'status': 'Valid' if total_trades >= 20 else 'Insufficient trades'
    }

def run_comprehensive_test():
    """Run comprehensive test on all 10 pairs"""
    pairs = [
        'EUR_USD', 'GBP_USD', 'USD_JPY', 'GBP_JPY', 'EUR_JPY',
        'AUD_JPY', 'EUR_GBP', 'AUD_USD', 'USD_CAD', 'USD_CHF'
    ]
    
    results = []
    
    print("=" * 80)
    print("COMPREHENSIVE 10-PAIR STRATEGY VALIDATION")
    print("=" * 80)
    print(f"Testing Enhanced Daily Strategy on H4 timeframe")
    print(f"Parameters: EMA 10/20 crossover, Risk:Reward ~1:2")
    print(f"Data: 5 years of historical data per pair")
    print("=" * 80)
    
    for pair in pairs:
        print(f"\nProcessing {pair}...")
        
        # Load data
        df = load_historical_data(pair)
        if df is None:
            continue
        
        print(f"  Loaded {len(df)} H4 candles from {df.index[0]} to {df.index[-1]}")
        
        # Generate signals
        df = generate_signals(df)
        signal_count = len(df[df['signal'] != 0])
        print(f"  Generated {signal_count} signals")
        
        # Simulate trades
        trades = simulate_trades(df, pair)
        print(f"  Simulated {len(trades)} completed trades")
        
        # Analyze performance
        performance = analyze_performance(trades, pair)
        results.append(performance)
        
        print(f"  Win Rate: {performance['win_rate']}% | Profit Factor: {performance['profit_factor']} | Total Pips: {performance['total_pips']}")
    
    return results

def display_summary(results):
    """Display comprehensive summary"""
    print("\n" + "=" * 100)
    print("COMPREHENSIVE STRATEGY PERFORMANCE SUMMARY")
    print("=" * 100)
    
    # Sort by profit factor
    results_sorted = sorted(results, key=lambda x: x['profit_factor'], reverse=True)
    
    print(f"{'Pair':<8} {'Trades':<7} {'Win%':<6} {'PF':<6} {'Pips':<8} {'AvgWin':<8} {'AvgLoss':<8} {'MaxLoss':<8} {'Status':<15}")
    print("-" * 100)
    
    total_trades = 0
    total_wins = 0
    total_pips = 0
    profitable_pairs = 0
    
    for result in results_sorted:
        status_color = "✓" if result['profit_factor'] > 1.0 else "✗"
        if result['profit_factor'] > 1.0:
            profitable_pairs += 1
        
        print(f"{result['pair']:<8} {result['total_trades']:<7} {result['win_rate']:<6} {result['profit_factor']:<6} "
              f"{result['total_pips']:<8} {result['avg_win']:<8} {result['avg_loss']:<8} "
              f"{result['max_consecutive_losses']:<8} {status_color} {result['status']:<13}")
        
        total_trades += result['total_trades']
        total_wins += result['wins']
        total_pips += result['total_pips']
    
    print("-" * 100)
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    print(f"\nOVERALL STRATEGY PERFORMANCE:")
    print(f"  • Total Trades Across All Pairs: {total_trades}")
    print(f"  • Overall Win Rate: {overall_win_rate:.1f}%")
    print(f"  • Total Pips Generated: {total_pips:.1f}")
    print(f"  • Profitable Pairs: {profitable_pairs}/10 ({profitable_pairs*10}%)")
    print(f"  • Average Pips Per Pair: {total_pips/10:.1f}")
    
    print(f"\nTOP PERFORMING PAIRS:")
    for i, result in enumerate(results_sorted[:3]):
        if result['profit_factor'] > 1.0:
            print(f"  {i+1}. {result['pair']}: {result['win_rate']}% WR, PF {result['profit_factor']}, {result['total_pips']} pips")
    
    print(f"\nSTRATEGY VIABILITY ASSESSMENT:")
    if profitable_pairs >= 6:
        print("  ✓ EXCELLENT: Strategy is profitable on majority of pairs")
    elif profitable_pairs >= 4:
        print("  ✓ GOOD: Strategy shows consistent profitability")
    elif profitable_pairs >= 2:
        print("  ⚠ MODERATE: Strategy needs refinement for broader applicability")
    else:
        print("  ✗ POOR: Strategy requires significant revision")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    results = run_comprehensive_test()
    display_summary(results)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comprehensive_test_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {output_file}")
