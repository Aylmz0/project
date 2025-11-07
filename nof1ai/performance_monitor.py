import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

def safe_file_read(file_path: str, default_data=None):
    """Safely read JSON file with error handling - handles empty files gracefully"""
    try:
        if os.path.exists(file_path):
            # Check if file is empty (0 bytes)
            if os.path.getsize(file_path) == 0:
                print(f"ℹ️ Empty file detected: {file_path} - returning default data")
                return default_data if default_data is not None else []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Check if file contains only whitespace
                if not content:
                    print(f"ℹ️ Empty content in {file_path} - returning default data")
                    return default_data if default_data is not None else []
                
                return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in {file_path}: {e}")
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
    return default_data if default_data is not None else []

def safe_file_write(file_path: str, data):
    """Safely write JSON file with error handling"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error writing {file_path}: {e}")
        return False

class PerformanceMonitor:
    """Performance monitoring system for Alpha Arena DeepSeek"""
    
    def __init__(self):
        self.cycle_history_file = "cycle_history.json"
        self.trade_history_file = "trade_history.json"
        self.portfolio_state_file = "portfolio_state.json"
        self.performance_file = "performance_report.json"
        
    def analyze_performance(self, last_n_cycles: int = 10) -> Dict[str, Any]:
        """Analyze performance for the last N cycles"""
        try:
            # Load data
            cycles = safe_file_read(self.cycle_history_file, [])
            trades = safe_file_read(self.trade_history_file, [])
            portfolio = safe_file_read(self.portfolio_state_file, {})
            
            if not cycles:
                return {"info": "No trading data available yet. Run Alpha Arena DeepSeek to generate performance data."}
            
            # Get last N cycles
            recent_cycles = cycles[-last_n_cycles:] if len(cycles) > last_n_cycles else cycles
            
            # Calculate basic metrics
            total_cycles = len(cycles)
            recent_cycle_count = len(recent_cycles)
            
            # Count trading decisions
            total_decisions = 0
            total_entries = 0
            total_holds = 0
            total_closes = 0
            
            for cycle in recent_cycles:
                decisions = cycle.get('decisions', {})
                if isinstance(decisions, dict):
                    total_decisions += len(decisions)
                    for coin, trade in decisions.items():
                        if isinstance(trade, dict):
                            signal = trade.get('signal', '')
                            if signal == 'buy_to_enter' or signal == 'sell_to_enter':
                                total_entries += 1
                            elif signal == 'hold':
                                total_holds += 1
                            elif signal == 'close_position':
                                total_closes += 1
            
            # Analyze trade performance
            if trades:
                # Calculate win rate
                winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
                losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
                break_even_trades = [t for t in trades if t.get('pnl', 0) == 0]
                
                win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
                
                # Calculate average PnL
                total_pnl = sum(t.get('pnl', 0) for t in trades)
                avg_pnl = total_pnl / len(trades) if trades else 0
                
                # Calculate profit factor
                total_profit = sum(t.get('pnl', 0) for t in winning_trades)
                total_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
                profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
                
                # Calculate largest win/loss
                largest_win = max(t.get('pnl', 0) for t in trades) if trades else 0
                largest_loss = min(t.get('pnl', 0) for t in trades) if trades else 0
                
            else:
                win_rate = 0
                avg_pnl = 0
                profit_factor = 0
                largest_win = 0
                largest_loss = 0
                winning_trades = []
                losing_trades = []
                break_even_trades = []
            
            # Portfolio performance
            initial_balance = portfolio.get('initial_balance', 200.0)
            current_balance = portfolio.get('current_balance', 0.0)
            total_value = portfolio.get('total_value', 0.0)
            total_return = portfolio.get('total_return', 0.0)
            sharpe_ratio = portfolio.get('sharpe_ratio', 0.0)
            
            # Position analysis
            positions = portfolio.get('positions', {})
            open_positions_count = len(positions)
            
            # Coin performance analysis
            coin_performance = {}
            for trade in trades:
                coin = trade.get('symbol')
                if coin:
                    if coin not in coin_performance:
                        coin_performance[coin] = {'trades': 0, 'total_pnl': 0, 'wins': 0, 'losses': 0}
                    
                    coin_performance[coin]['trades'] += 1
                    coin_performance[coin]['total_pnl'] += trade.get('pnl', 0)
                    
                    if trade.get('pnl', 0) > 0:
                        coin_performance[coin]['wins'] += 1
                    elif trade.get('pnl', 0) < 0:
                        coin_performance[coin]['losses'] += 1
            
            # Calculate coin win rates
            for coin, stats in coin_performance.items():
                stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
                stats['avg_pnl'] = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
            
            # Compile performance report
            performance_report = {
                "analysis_period": f"Last {recent_cycle_count} cycles (Total: {total_cycles})",
                "timestamp": datetime.now().isoformat(),
                
                # Trading Activity
                "trading_activity": {
                    "total_decisions": total_decisions,
                    "entry_signals": total_entries,
                    "hold_signals": total_holds,
                    "close_signals": total_closes,
                    "decision_rate": (total_entries / total_decisions * 100) if total_decisions > 0 else 0
                },
                
                # Trade Performance
                "trade_performance": {
                    "total_trades": len(trades),
                    "winning_trades": len(winning_trades),
                    "losing_trades": len(losing_trades),
                    "break_even_trades": len(break_even_trades),
                    "win_rate": round(win_rate, 2),
                    "total_pnl": round(total_pnl, 2),
                    "average_pnl": round(avg_pnl, 2),
                    "profit_factor": round(profit_factor, 2),
                    "largest_win": round(largest_win, 2),
                    "largest_loss": round(largest_loss, 2)
                },
                
                # Portfolio Performance
                "portfolio_performance": {
                    "initial_balance": initial_balance,
                    "current_balance": current_balance,
                    "total_value": total_value,
                    "total_return": round(total_return, 2),
                    "sharpe_ratio": round(sharpe_ratio, 3),
                    "open_positions": open_positions_count
                },
                
                # Coin Performance
                "coin_performance": coin_performance,
                
                # Recommendations
                "recommendations": self._generate_recommendations(
                    win_rate, profit_factor, coin_performance, open_positions_count
                )
            }
            
            # Save performance report
            safe_file_write(self.performance_file, performance_report)
            
            return performance_report
            
        except Exception as e:
            print(f"❌ Performance analysis error: {e}")
            return {"error": f"Performance analysis failed: {str(e)}"}
    
    def _generate_recommendations(self, win_rate: float, profit_factor: float, 
                                coin_performance: Dict, open_positions: int) -> List[str]:
        """Generate honest performance-based recommendations in English"""
        recommendations = []
        
        # Get current portfolio data for dynamic values
        portfolio = safe_file_read(self.portfolio_state_file, {})
        current_balance = portfolio.get('current_balance', 0.0)
        initial_balance = portfolio.get('initial_balance', 200.0)
        total_return = portfolio.get('total_return', 0.0)
        
        # Dynamic cash balance warning
        if current_balance < initial_balance * 0.5:
            recommendations.append(f"⚠️ Low cash balance (${current_balance:.2f}/{initial_balance}) - be selective")
        
        # 3 positions threshold (more conservative)
        if open_positions >= 3:
            recommendations.append(f"📊 High position count ({open_positions}) - quality over quantity")
        
        # Performance feedback
        if total_return < 5:
            recommendations.append(f"📈 Low return ({total_return:.2f}%) - seek better setups")
        
        # Coin performance - simple and clear
        if coin_performance:
            unprofitable_coins = [coin for coin, stats in coin_performance.items() 
                                if stats.get('total_pnl', 0) < 0]
            if unprofitable_coins:
                recommendations.append(f"⚠️ Review strategy for: {', '.join(unprofitable_coins)}")
        
        # General recommendation if no specific issues
        if not recommendations:
            recommendations.append("📊 Performance stable - continue current approach")
        
        return recommendations
    
    def print_performance_summary(self, report: Dict):
        """Print a formatted performance summary"""
        if "error" in report:
            print(f"❌ Performance analysis failed: {report['error']}")
            return
        
        if "info" in report:
            print(f"ℹ️ {report['info']}")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 PERFORMANCE REPORT - {report.get('analysis_period', 'N/A')}")
        print(f"{'='*60}")
        
        # Trading Activity
        activity = report.get('trading_activity', {})
        print(f"\n🎯 TRADING ACTIVITY:")
        print(f"   Total Decisions: {activity.get('total_decisions', 0)}")
        print(f"   Entry Signals: {activity.get('entry_signals', 0)}")
        print(f"   Hold Signals: {activity.get('hold_signals', 0)}")
        print(f"   Decision Rate: {activity.get('decision_rate', 0):.1f}%")
        
        # Trade Performance
        trade_perf = report.get('trade_performance', {})
        print(f"\n💰 TRADE PERFORMANCE:")
        print(f"   Total Trades: {trade_perf.get('total_trades', 0)}")
        print(f"   Win Rate: {trade_perf.get('win_rate', 0):.1f}%")
        print(f"   Total PnL: ${trade_perf.get('total_pnl', 0):.2f}")
        print(f"   Avg PnL/Trade: ${trade_perf.get('average_pnl', 0):.2f}")
        print(f"   Profit Factor: {trade_perf.get('profit_factor', 0):.2f}")
        
        # Portfolio Performance
        portfolio_perf = report.get('portfolio_performance', {})
        print(f"\n📈 PORTFOLIO PERFORMANCE:")
        print(f"   Total Return: {portfolio_perf.get('total_return', 0):.2f}%")
        print(f"   Sharpe Ratio: {portfolio_perf.get('sharpe_ratio', 0):.3f}")
        print(f"   Open Positions: {portfolio_perf.get('open_positions', 0)}")
        
        # Coin Performance
        coin_perf = report.get('coin_performance', {})
        if coin_perf:
            print(f"\n🪙 COIN PERFORMANCE:")
            for coin, stats in coin_perf.items():
                win_rate = stats.get('win_rate', 0)
                total_pnl = stats.get('total_pnl', 0)
                trades = stats.get('trades', 0)
                print(f"   {coin}: {trades} trades, {win_rate:.1f}% win rate, PnL: ${total_pnl:.2f}")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        # Adaptive strategy suggestions
        adaptive_suggestions = self._generate_adaptive_suggestions(report)
        if adaptive_suggestions:
            print(f"\n🎯 ADAPTIVE STRATEGY SUGGESTIONS:")
            for suggestion in adaptive_suggestions:
                print(f"   • {suggestion}")
        
        print(f"\n📄 Full report saved to: {self.performance_file}")
        print(f"{'='*60}")

    def _generate_adaptive_suggestions(self, report: Dict) -> List[str]:
        """Generate adaptive strategy suggestions based on performance patterns"""
        suggestions = []
        
        # Get performance metrics
        trade_perf = report.get('trade_performance', {})
        portfolio_perf = report.get('portfolio_performance', {})
        activity = report.get('trading_activity', {})
        coin_perf = report.get('coin_performance', {})
        
        win_rate = trade_perf.get('win_rate', 0)
        profit_factor = trade_perf.get('profit_factor', 0)
        total_return = portfolio_perf.get('total_return', 0)
        sharpe_ratio = portfolio_perf.get('sharpe_ratio', 0)
        decision_rate = activity.get('decision_rate', 0)
        open_positions = portfolio_perf.get('open_positions', 0)
        
        # Strategy suggestions based on performance patterns
        
        # High win rate but low profit factor (small wins, big losses)
        if win_rate > 50 and profit_factor < 1.2:
            suggestions.append("High win rate but low profit factor - focus on improving risk/reward ratio")
        
        # Low win rate but positive profit factor (big wins, small losses)
        elif win_rate < 40 and profit_factor > 1.5:
            suggestions.append("Low win rate but positive profit factor - strategy is working, maintain discipline")
        
        # High decision rate but poor performance
        if decision_rate > 60 and total_return < 0:
            suggestions.append("High trading frequency with negative returns - consider reducing activity")
        
        # Low decision rate with good performance
        elif decision_rate < 30 and total_return > 5:
            suggestions.append("Low frequency with good returns - current selective approach is effective")
        
        # Sharpe ratio analysis
        if sharpe_ratio < 0:
            suggestions.append("Negative Sharpe ratio - strategy is underperforming risk-free rate")
        elif sharpe_ratio > 1.0:
            suggestions.append("Good Sharpe ratio (>1.0) - strategy provides good risk-adjusted returns")
        
        # Position management suggestions
        if open_positions >= 4 and total_return < 0:
            suggestions.append("High position count with negative returns - reduce exposure and focus on quality setups")
        elif open_positions <= 2 and total_return > 0:
            suggestions.append("Low position count with positive returns - consider scaling up gradually")
        
        # Coin-specific suggestions
        if coin_perf:
            # Find best and worst performing coins
            coin_pnls = [(coin, stats.get('total_pnl', 0)) for coin, stats in coin_perf.items()]
            coin_pnls.sort(key=lambda x: x[1], reverse=True)
            
            if coin_pnls:
                best_coin, best_pnl = coin_pnls[0]
                worst_coin, worst_pnl = coin_pnls[-1]
                
                if best_pnl > 0:
                    suggestions.append(f"Strong performer: {best_coin} (${best_pnl:.2f}) - consider increasing allocation")
                
                if worst_pnl < -10:  # Significant loss
                    suggestions.append(f"Weak performer: {worst_coin} (${worst_pnl:.2f}) - review strategy or reduce exposure")
        
        # Market regime suggestions
        if total_return > 10:
            suggestions.append("Strong positive returns - current market conditions favorable, maintain strategy")
        elif total_return < -5:
            suggestions.append("Negative returns - consider defensive positioning or strategy adjustment")
        
        # Risk management suggestions
        if profit_factor < 0.8:
            suggestions.append("Poor risk management - focus on position sizing and stop-loss discipline")
        
        return suggestions

# Main function for standalone usage
def main():
    """Standalone performance analysis"""
    monitor = PerformanceMonitor()
    print("🔍 Analyzing trading performance...")
    report = monitor.analyze_performance(last_n_cycles=10)
    monitor.print_performance_summary(report)

if __name__ == "__main__":
    main()
