#!/usr/bin/env python3
"""
OANDA Historical Data Acquisition & Backtest Generator
Pulls 5 years of data from OANDA and runs comprehensive backtests
for the conservative_moderate_daily strategy (MA 50/200).
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OANDABacktestGenerator:
    """Comprehensive backtest generator using real OANDA data."""
    
    def __init__(self):
        # OANDA Configuration
        self.api_key = os.getenv("OANDA_API_KEY", "")
        self.account_id = os.getenv("OANDA_ACCOUNT_ID", "")
        self.base_url = "https://api-fxpractice.oanda.com"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Strategy Configuration (MA 50/200)
        self.fast_ma = 50
        self.slow_ma = 200
        self.strategy_name = "conservative_moderate_daily"
        
        # Currency pairs to test
        self.pairs = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "EUR_GBP", "GBP_JPY", "NZD_USD", "USD_CAD"]
        
        # Date range (5 years)
        self.end_date = datetime.now(timezone.utc)
        self.start_date = self.end_date - timedelta(days=5*365)  # 5 years
        
        logger.info(f"🚀 OANDA Backtest Generator initialized")
        logger.info(f"📅 Date Range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"💱 Pairs: {', '.join(self.pairs)}")

    async def fetch_historical_data(self, pair: str, granularity: str = "D") -> pd.DataFrame:
        """Fetch historical data from OANDA API."""
        
        # Calculate number of candles needed (approximately)
        days_diff = (self.end_date - self.start_date).days
        max_candles = min(5000, days_diff)  # OANDA limit
        
        logger.info(f"📡 Fetching {max_candles} {granularity} candles for {pair} from OANDA...")
        
        try:
            connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.base_url}/v3/instruments/{pair}/candles"
                params = {
                    "count": max_candles,
                    "granularity": granularity,
                    "price": "M",  # Mid prices
                    "from": self.start_date.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                    "to": self.end_date.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
                }
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ OANDA API error {response.status}: {error_text}")
                        return pd.DataFrame()
                    
                    data = await response.json()
                    candles = data.get("candles", [])
                    
                    if not candles:
                        logger.warning(f"⚠️ No candles returned for {pair}")
                        return pd.DataFrame()
                    
                    # Convert to DataFrame
                    records = []
                    for candle in candles:
                        if candle.get("complete", False):
                            mid = candle["mid"]
                            records.append({
                                "timestamp": datetime.fromisoformat(candle["time"].replace("Z", "+00:00")),
                                "open": float(mid["o"]),
                                "high": float(mid["h"]),
                                "low": float(mid["l"]),
                                "close": float(mid["c"]),
                                "volume": candle.get("volume", 1000)
                            })
                    
                    df = pd.DataFrame(records)
                    df.set_index("timestamp", inplace=True)
                    df.sort_index(inplace=True)
                    
                    logger.info(f"✅ Retrieved {len(df)} candles for {pair}")
                    return df
                    
        except Exception as e:
            logger.error(f"❌ Error fetching data for {pair}: {e}")
            return pd.DataFrame()

    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages for the strategy."""
        
        if len(df) < self.slow_ma:
            logger.warning(f"⚠️ Insufficient data for MA calculation: {len(df)} < {self.slow_ma}")
            return df
        
        df = df.copy()
        df[f"MA_{self.fast_ma}"] = df["close"].rolling(window=self.fast_ma).mean()
        df[f"MA_{self.slow_ma}"] = df["close"].rolling(window=self.slow_ma).mean()
        
        # Generate signals
        df["fast_above_slow"] = df[f"MA_{self.fast_ma}"] > df[f"MA_{self.slow_ma}"]
        df["prev_fast_above_slow"] = df["fast_above_slow"].shift(1)
        
        # Signal generation
        df["signal"] = "HOLD"
        df.loc[(~df["prev_fast_above_slow"]) & (df["fast_above_slow"]), "signal"] = "BUY"
        df.loc[(df["prev_fast_above_slow"]) & (~df["fast_above_slow"]), "signal"] = "SELL"
        
        return df

    def run_backtest(self, df: pd.DataFrame, pair: str) -> Dict[str, Any]:
        """Run backtest simulation on the data."""
        
        if len(df) < self.slow_ma:
            return self._empty_results(pair)
        
        # Calculate moving averages and signals
        df = self.calculate_moving_averages(df)
        
        # Remove rows with NaN values
        df = df.dropna()
        
        if len(df) == 0:
            return self._empty_results(pair)
        
        # Backtest simulation
        initial_balance = 10000.0
        balance = initial_balance
        position = 0  # 0 = no position, 1 = long, -1 = short
        trades = []
        equity_curve = [float(initial_balance)]
        entry_price = 0.0
        
        for i, (timestamp, row) in enumerate(df.iterrows()):
            current_price = row["close"]
            signal = row["signal"]
            
            # Process signals
            if signal == "BUY" and position <= 0:
                # Close short if any, open long
                if position == -1:
                    # Close short position
                    pnl = (entry_price - current_price) / entry_price
                    balance *= (1 + pnl)
                    trades.append({
                        "type": "SELL_CLOSE",
                        "price": current_price,
                        "timestamp": timestamp,
                        "pnl": pnl
                    })
                
                # Open long position
                position = 1
                entry_price = current_price
                trades.append({
                    "type": "BUY_OPEN",
                    "price": current_price,
                    "timestamp": timestamp,
                    "pnl": 0
                })
                
            elif signal == "SELL" and position >= 0:
                # Close long if any, open short
                if position == 1:
                    # Close long position
                    pnl = (current_price - entry_price) / entry_price
                    balance *= (1 + pnl)
                    trades.append({
                        "type": "BUY_CLOSE",
                        "price": current_price,
                        "timestamp": timestamp,
                        "pnl": pnl
                    })
                
                # Open short position
                position = -1
                entry_price = current_price
                trades.append({
                    "type": "SELL_OPEN",
                    "price": current_price,
                    "timestamp": timestamp,
                    "pnl": 0
                })
            
            # Calculate current equity (mark-to-market)
            if position == 1:  # Long position
                unrealized_pnl = (current_price - entry_price) / entry_price
                current_equity = balance * (1 + unrealized_pnl)
            elif position == -1:  # Short position
                unrealized_pnl = (entry_price - current_price) / entry_price
                current_equity = balance * (1 + unrealized_pnl)
            else:  # No position
                current_equity = balance
            
            equity_curve.append(float(current_equity))
        
        # Close any remaining position
        if position != 0:
            final_price = df.iloc[-1]["close"]
            if position == 1:
                pnl = (final_price - entry_price) / entry_price
            else:
                pnl = (entry_price - final_price) / entry_price
            balance *= (1 + pnl)
            trades.append({
                "type": "FINAL_CLOSE",
                "price": final_price,
                "timestamp": df.index[-1],
                "pnl": pnl
            })
        
        # Calculate performance metrics
        return self._calculate_performance_metrics(
            pair, df, trades, equity_curve, initial_balance, balance
        )

    def _calculate_performance_metrics(
        self, pair: str, df: pd.DataFrame, trades: List[Dict], 
        equity_curve: List[float], initial_balance: float, final_balance: float
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        
        # Basic metrics
        total_return = (final_balance - initial_balance) / initial_balance
        annual_return = (final_balance / initial_balance) ** (365 / len(df)) - 1
        
        # Trade statistics
        trade_pnls = [t["pnl"] for t in trades if t["pnl"] != 0]
        total_trades = len(trade_pnls)
        winning_trades = len([pnl for pnl in trade_pnls if pnl > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([pnl for pnl in trade_pnls if pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([pnl for pnl in trade_pnls if pnl < 0]) if losing_trades > 0 else 0
        
        # Risk metrics
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (simplified)
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Other metrics
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 else 0
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            "execution_id": f"{pair}_{self.strategy_name}",
            "currency_pair": pair,
            "strategy": self.strategy_name,
            "timeframe": "D",
            "execution_date": datetime.now(timezone.utc).isoformat(),
            "status": "Completed",
            "performance_metrics": {
                "total_return": round(total_return, 4),
                "annual_return": round(annual_return, 4),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 4),
                "calmar_ratio": round(calmar_ratio, 2),
                "profit_factor": round(profit_factor, 2)
            },
            "trade_statistics": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 3),
                "avg_win": round(avg_win, 4) if avg_win else 0,
                "avg_loss": round(avg_loss, 4) if avg_loss else 0,
                "largest_win": round(max(trade_pnls), 4) if trade_pnls else 0,
                "largest_loss": round(min(trade_pnls), 4) if trade_pnls else 0
            },
            "data_period": {
                "start_date": df.index[0].strftime("%Y-%m-%d"),
                "end_date": df.index[-1].strftime("%Y-%m-%d"),
                "total_days": len(df),
                "data_quality": "OANDA_LIVE"
            },
            "strategy_parameters": {
                "fast_ma": self.fast_ma,
                "slow_ma": self.slow_ma,
                "source": "close"
            },
            "equity_curve": [round(eq, 2) for eq in equity_curve[::max(1, len(equity_curve)//100)]]  # Sample for efficiency
        }

    def _empty_results(self, pair: str) -> Dict[str, Any]:
        """Return empty results for insufficient data."""
        return {
            "execution_id": f"{pair}_{self.strategy_name}",
            "currency_pair": pair,
            "strategy": self.strategy_name,
            "timeframe": "D",
            "execution_date": datetime.now(timezone.utc).isoformat(),
            "status": "Insufficient_Data",
            "performance_metrics": {
                "total_return": 0.0,
                "annual_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "calmar_ratio": 0.0,
                "profit_factor": 0.0
            },
            "trade_statistics": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0
            },
            "data_period": {
                "start_date": "N/A",
                "end_date": "N/A", 
                "total_days": 0,
                "data_quality": "INSUFFICIENT"
            },
            "strategy_parameters": {
                "fast_ma": self.fast_ma,
                "slow_ma": self.slow_ma,
                "source": "close"
            },
            "equity_curve": []
        }

    async def run_comprehensive_backtest(self):
        """Run backtest for all pairs and generate results."""
        
        logger.info("🚀 Starting comprehensive OANDA backtest...")
        
        if not self.api_key:
            logger.error("❌ OANDA API key not found. Please set OANDA_API_KEY environment variable.")
            return
        
        results = {
            "backtest_metadata": {
                "generation_date": datetime.now(timezone.utc).isoformat(),
                "data_source": "OANDA_v20_API",
                "strategy": self.strategy_name,
                "parameters": {
                    "fast_ma": self.fast_ma,
                    "slow_ma": self.slow_ma
                },
                "date_range": {
                    "start": self.start_date.strftime("%Y-%m-%d"),
                    "end": self.end_date.strftime("%Y-%m-%d"),
                    "duration_years": 5
                },
                "pairs_tested": self.pairs
            },
            "backtest_results": []
        }
        
        # Run backtest for each pair
        for pair in self.pairs:
            try:
                logger.info(f"📊 Processing {pair}...")
                
                # Fetch historical data
                df = await self.fetch_historical_data(pair)
                
                if df.empty:
                    logger.warning(f"⚠️ No data available for {pair}")
                    results["backtest_results"].append(self._empty_results(pair))
                    continue
                
                # Run backtest
                result = self.run_backtest(df, pair)
                results["backtest_results"].append(result)
                
                logger.info(f"✅ {pair} - Return: {result['performance_metrics']['annual_return']:.1%}, "
                           f"Sharpe: {result['performance_metrics']['sharpe_ratio']:.2f}, "
                           f"Trades: {result['trade_statistics']['total_trades']}")
                
                # Small delay to respect API limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error processing {pair}: {e}")
                results["backtest_results"].append(self._empty_results(pair))
        
        # Generate summary
        completed_results = [r for r in results["backtest_results"] if r["status"] == "Completed"]
        
        if completed_results:
            avg_return = np.mean([r["performance_metrics"]["annual_return"] for r in completed_results])
            avg_sharpe = np.mean([r["performance_metrics"]["sharpe_ratio"] for r in completed_results])
            avg_drawdown = np.mean([r["performance_metrics"]["max_drawdown"] for r in completed_results])
            avg_win_rate = np.mean([r["trade_statistics"]["win_rate"] for r in completed_results])
            
            results["summary"] = {
                "completed_backtests": len(completed_results),
                "avg_annual_return": round(avg_return, 4),
                "avg_annual_return_pct": f"{avg_return:.1%}",
                "avg_sharpe_ratio": round(avg_sharpe, 2),
                "avg_max_drawdown": round(avg_drawdown, 4),
                "avg_max_drawdown_pct": f"{avg_drawdown:.1%}",
                "avg_win_rate": round(avg_win_rate, 3),
                "avg_win_rate_pct": f"{avg_win_rate:.1%}",
                "best_performing_pair": max(completed_results, key=lambda x: x["performance_metrics"]["annual_return"])["currency_pair"],
                "best_sharpe_pair": max(completed_results, key=lambda x: x["performance_metrics"]["sharpe_ratio"])["currency_pair"]
            }
        
        # Save results
        await self.save_results(results)
        
        logger.info("🎉 Comprehensive backtest completed!")
        return results

    async def save_results(self, results: Dict[str, Any]):
        """Save backtest results to files."""
        
        # Create directories
        output_dir = Path("backtest_data")
        output_dir.mkdir(exist_ok=True)
        
        frontend_dir = Path("4ex.ninja-frontend/public/backtest_data")
        frontend_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate top strategies performance file
        top_strategies = {
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "data_source": "OANDA 5-Year Historical Backtest",
            "total_strategies_analyzed": len(results["backtest_results"]),
            "top_performing_strategies": []
        }
        
        # Sort by annual return and add rankings
        completed = [r for r in results["backtest_results"] if r["status"] == "Completed"]
        completed.sort(key=lambda x: x["performance_metrics"]["annual_return"], reverse=True)
        
        for rank, result in enumerate(completed, 1):
            perf = result["performance_metrics"]
            trades = result["trade_statistics"]
            
            top_strategies["top_performing_strategies"].append({
                "rank": rank,
                "execution_id": result["execution_id"],
                "currency_pair": result["currency_pair"],
                "strategy": result["strategy"],
                "timeframe": result["timeframe"],
                "performance_metrics": {
                    "annual_return": perf["annual_return"],
                    "annual_return_pct": f"{perf['annual_return']:.1%}",
                    "sharpe_ratio": perf["sharpe_ratio"],
                    "max_drawdown": perf["max_drawdown"],
                    "max_drawdown_pct": f"{perf['max_drawdown']:.1%}",
                    "win_rate": trades["win_rate"],
                    "win_rate_pct": f"{trades['win_rate']:.1%}"
                },
                "category": "OANDA Live Data Backtest",
                "description": f"Conservative moderate daily strategy (MA {self.fast_ma}/{self.slow_ma}) with real OANDA data"
            })
        
        # Save files
        files_to_save = [
            ("oanda_backtest_results_full.json", results),
            ("top_strategies_performance.json", top_strategies)
        ]
        
        for filename, data in files_to_save:
            # Save to backtest_data
            with open(output_dir / filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Save to frontend
            with open(frontend_dir / filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"💾 Saved {filename}")
        
        logger.info(f"📁 Results saved to {output_dir} and {frontend_dir}")

async def main():
    """Main execution function."""
    generator = OANDABacktestGenerator()
    await generator.run_comprehensive_backtest()

if __name__ == "__main__":
    asyncio.run(main())
