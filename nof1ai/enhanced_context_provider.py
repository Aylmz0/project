import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

class EnhancedContextProvider:
    """
    Provides enhanced context to help AI make better decisions
    NO manipulation - only better data and suggestions
    """
    
    def __init__(self):
        self.cycle_history_file = "cycle_history.json"
        self.trade_history_file = "trade_history.json"
        self.portfolio_state_file = "portfolio_state.json"
        self.performance_file = "performance_report.json"
        
    def safe_file_read(self, file_path: str, default_data=None):
        """Safely read JSON file with error handling"""
        try:
            if os.path.exists(file_path):
                if os.path.getsize(file_path) == 0:
                    return default_data if default_data is not None else []
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return default_data if default_data is not None else []
                    
                    return json.loads(content)
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
        return default_data if default_data is not None else []
    
    def get_enhanced_position_context(self, portfolio_state: Dict) -> Dict[str, Any]:
        """Provides enhanced context for current positions"""
        positions = portfolio_state.get('positions', {})
        enhanced_context = {}
        
        for symbol, position in positions.items():
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            profit_target = position.get('exit_plan', {}).get('profit_target', 0)
            stop_loss = position.get('exit_plan', {}).get('stop_loss', 0)
            
            # Profit target progress
            if profit_target > 0:
                if position.get('direction') == 'long':
                    progress = ((current_price - entry_price) / (profit_target - entry_price)) * 100
                else:  # short
                    progress = ((entry_price - current_price) / (entry_price - profit_target)) * 100
            else:
                progress = 0
            
            # Time in trade
            entry_time_str = position.get('entry_time', '')
            if entry_time_str:
                try:
                    entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
                    time_in_trade = (datetime.now() - entry_time).total_seconds() / 60  # minutes
                except:
                    time_in_trade = 0
            else:
                time_in_trade = 0
            
            enhanced_context[symbol] = {
                'unrealized_pnl': unrealized_pnl,
                'profit_target_progress': round(progress, 2),
                'time_in_trade_minutes': round(time_in_trade, 2),
                'distance_to_target_pct': round(abs(profit_target - current_price) / current_price * 100, 2),
                'distance_to_stop_pct': round(abs(stop_loss - current_price) / current_price * 100, 2),
                'risk_reward_ratio': round(abs(profit_target - entry_price) / abs(stop_loss - entry_price), 2) if stop_loss != entry_price else 0
            }
        
        return enhanced_context
    
    def get_market_regime_context(self, cycle_history: List) -> Dict[str, Any]:
        """Market regime detection based on recent cycles"""
        if not cycle_history:
            return {"current_regime": "unknown", "regime_strength": 0}
        
        recent_cycles = cycle_history[-5:]  # Son 5 cycle
        
        # Analyze trend patterns from chain_of_thoughts
        bearish_count = 0
        bullish_count = 0
        ranging_count = 0
        
        for cycle in recent_cycles:
            thoughts = cycle.get('chain_of_thoughts', '').lower()
            if 'bearish' in thoughts:
                bearish_count += 1
            if 'bullish' in thoughts:
                bullish_count += 1
            if 'ranging' in thoughts or 'consolidation' in thoughts:
                ranging_count += 1
        
        total_cycles = len(recent_cycles)
        bearish_score = bearish_count / total_cycles
        bullish_score = bullish_count / total_cycles
        ranging_score = ranging_count / total_cycles
        
        # Determine dominant regime
        if bearish_score > 0.6:
            regime = "bearish"
            strength = bearish_score
        elif bullish_score > 0.6:
            regime = "bullish" 
            strength = bullish_score
        elif ranging_score > 0.6:
            regime = "ranging"
            strength = ranging_score
        else:
            regime = "mixed"
            strength = max(bearish_score, bullish_score, ranging_score)
        
        return {
            "current_regime": regime,
            "regime_strength": round(strength, 2),
            "bearish_score": round(bearish_score, 2),
            "bullish_score": round(bullish_score, 2),
            "ranging_score": round(ranging_score, 2)
        }
    
    def get_performance_insights(self, trade_history: List, portfolio_state: Dict) -> Dict[str, Any]:
        """Performance-based insights for better decision making"""
        if not trade_history:
            return {"insights": ["No trading history available"]}
        
        # Calculate win rate by coin
        coin_performance = {}
        for trade in trade_history:
            symbol = trade.get('symbol')
            pnl = trade.get('pnl', 0)
            
            if symbol not in coin_performance:
                coin_performance[symbol] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
            
            coin_performance[symbol]['trades'] += 1
            coin_performance[symbol]['total_pnl'] += pnl
            if pnl > 0:
                coin_performance[symbol]['wins'] += 1
        
        # Generate insights
        insights = []
        
        # Best performing coins
        profitable_coins = [coin for coin, stats in coin_performance.items() if stats['total_pnl'] > 0]
        if profitable_coins:
            insights.append(f"Historically profitable coins: {', '.join(profitable_coins)}")
        
        # Worst performing coins
        unprofitable_coins = [coin for coin, stats in coin_performance.items() if stats['total_pnl'] < -1.0]
        if unprofitable_coins:
            insights.append(f"Historically challenging coins: {', '.join(unprofitable_coins)}")
        
        # Current portfolio performance
        total_return = portfolio_state.get('total_return', 0)
        if total_return < -5:
            insights.append("Portfolio experiencing significant drawdown - consider defensive positioning")
        elif total_return > 5:
            insights.append("Portfolio performing well - current strategy effective")
        
        return {"insights": insights, "coin_performance": coin_performance}
    
    def get_risk_context(self, portfolio_state: Dict) -> Dict[str, Any]:
        """Enhanced risk management context"""
        positions = portfolio_state.get('positions', {})
        current_balance = portfolio_state.get('current_balance', 0)
        total_value = portfolio_state.get('total_value', 0)
        
        # Calculate risk metrics
        total_risk = sum(pos.get('risk_usd', 0) for pos in positions.values())
        risk_percentage = (total_risk / current_balance * 100) if current_balance > 0 else 0
        
        # Position concentration
        position_count = len(positions)
        max_recommended_positions = 3
        
        # Correlation analysis (simplified)
        short_positions = [sym for sym, pos in positions.items() if pos.get('direction') == 'short']
        long_positions = [sym for sym, pos in positions.items() if pos.get('direction') == 'long']
        
        return {
            "total_risk_usd": round(total_risk, 2),
            "risk_percentage": round(risk_percentage, 2),
            "position_count": position_count,
            "max_recommended_positions": max_recommended_positions,
            "short_positions": short_positions,
            "long_positions": long_positions,
            "diversification_score": round((1 - (position_count / max_recommended_positions)) * 100, 2) if position_count > 0 else 100
        }
    
    def generate_enhanced_context(self) -> Dict[str, Any]:
        """Main enhanced context generation function"""
        try:
            # Load data
            portfolio_state = self.safe_file_read(self.portfolio_state_file, {})
            cycle_history = self.safe_file_read(self.cycle_history_file, [])
            trade_history = self.safe_file_read(self.trade_history_file, [])
            
            enhanced_context = {
                "timestamp": datetime.now().isoformat(),
                "position_context": self.get_enhanced_position_context(portfolio_state),
                "market_regime": self.get_market_regime_context(cycle_history),
                "performance_insights": self.get_performance_insights(trade_history, portfolio_state),
                "risk_context": self.get_risk_context(portfolio_state),
                "suggestions": self.generate_suggestions(portfolio_state, cycle_history)
            }
            
            return enhanced_context
            
        except Exception as e:
            print(f"❌ Enhanced context generation error: {e}")
            return {"error": f"Context generation failed: {str(e)}"}
    
    def generate_suggestions(self, portfolio_state: Dict, cycle_history: List) -> List[str]:
        """Non-manipulative suggestions for AI"""
        suggestions = []
        positions = portfolio_state.get('positions', {})
        
        # Position management suggestions
        for symbol, position in positions.items():
            unrealized_pnl = position.get('unrealized_pnl', 0)
            profit_target = position.get('exit_plan', {}).get('profit_target', 0)
            current_price = position.get('current_price', 0)
            
            # Profit target approaching
            if unrealized_pnl > 0:
                direction = position.get('direction', '')
                if direction == 'long' and current_price >= profit_target * 0.95:
                    suggestions.append(f"{symbol} approaching profit target - consider reviewing exit strategy")
                elif direction == 'short' and current_price <= profit_target * 1.05:
                    suggestions.append(f"{symbol} approaching profit target - consider reviewing exit strategy")
        
        # Market regime suggestions
        market_regime = self.get_market_regime_context(cycle_history)
        current_regime = market_regime.get('current_regime', 'unknown')
        
        if current_regime == "bearish" and len(positions) >= 3:
            suggestions.append("Bearish market with multiple positions - consider risk management")
        elif current_regime == "bullish" and len(positions) == 0:
            suggestions.append("Bullish market detected - potential long opportunities")
        
        # Risk management suggestions
        risk_context = self.get_risk_context(portfolio_state)
        if risk_context['risk_percentage'] > 30:
            suggestions.append("High risk exposure - consider position reduction")
        
        return suggestions
    
    def print_enhanced_context(self, context: Dict):
        """Prints enhanced context in formatted way"""
        if "error" in context:
            print(f"❌ Enhanced context error: {context['error']}")
            return
        
        print(f"\n{'='*60}")
        print(f"🎯 ENHANCED CONTEXT FOR AI DECISION MAKING")
        print(f"{'='*60}")
        
        # Position Context
        position_context = context.get('position_context', {})
        if position_context:
            print(f"\n📊 POSITION CONTEXT:")
            for symbol, data in position_context.items():
                pnl = data.get('unrealized_pnl', 0)
                progress = data.get('profit_target_progress', 0)
                time_in_trade = data.get('time_in_trade_minutes', 0)
                print(f"   {symbol}: ${pnl:.2f} PnL, {progress}% to target, {time_in_trade}min in trade")
        
        # Market Regime
        market_regime = context.get('market_regime', {})
        print(f"\n🌐 MARKET REGIME:")
        print(f"   Current: {market_regime.get('current_regime', 'unknown')}")
        print(f"   Strength: {market_regime.get('regime_strength', 0)}")
        
        # Performance Insights
        performance = context.get('performance_insights', {})
        insights = performance.get('insights', [])
        if insights:
            print(f"\n💡 PERFORMANCE INSIGHTS:")
            for insight in insights:
                print(f"   • {insight}")
        
        # Risk Context
        risk_context = context.get('risk_context', {})
        print(f"\n🛡️ RISK CONTEXT:")
        print(f"   Total Risk: ${risk_context.get('total_risk_usd', 0):.2f}")
        print(f"   Risk %: {risk_context.get('risk_percentage', 0):.1f}%")
        print(f"   Positions: {risk_context.get('position_count', 0)}")
        
        # Suggestions
        suggestions = context.get('suggestions', [])
        if suggestions:
            print(f"\n🎯 SUGGESTIONS (Non-binding):")
            for suggestion in suggestions:
                print(f"   • {suggestion}")
        
        print(f"\n{'='*60}")

# Main function for testing
def main():
    """Test enhanced context provider"""
    provider = EnhancedContextProvider()
    print("🔍 Generating enhanced context for AI decision making...")
    context = provider.generate_enhanced_context()
    provider.print_enhanced_context(context)

if __name__ == "__main__":
    main()
