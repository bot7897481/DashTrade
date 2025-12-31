"""
AI Strategy Analyzer for DashTrade
Hybrid approach: SQL pattern detection + Claude API for insight generation

This service:
1. Queries the database for trade patterns and statistics
2. Sends patterns to Claude API for natural language analysis
3. Stores actionable insights for users
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

# Claude API
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Warning: anthropic package not installed. Run: pip install anthropic")

from database import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class AIStrategyAnalyzer:
    """
    Analyzes trading patterns and generates insights using Claude API
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the analyzer

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if CLAUDE_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Claude API not available - insights will be statistical only")

    # =========================================================================
    # PATTERN DETECTION (SQL-based)
    # =========================================================================

    def get_performance_by_rsi_threshold(self, user_id: int = None, min_trades: int = 10) -> List[Dict]:
        """Find optimal RSI entry thresholds"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    user_filter = "AND o.user_id = %s" if user_id else ""
                    params = [min_trades, user_id] if user_id else [min_trades]

                    cur.execute(f"""
                        SELECT
                            CASE
                                WHEN p.rsi_value_at_entry < 25 THEN 'RSI < 25 (Oversold)'
                                WHEN p.rsi_value_at_entry BETWEEN 25 AND 35 THEN 'RSI 25-35'
                                WHEN p.rsi_value_at_entry BETWEEN 35 AND 50 THEN 'RSI 35-50'
                                WHEN p.rsi_value_at_entry BETWEEN 50 AND 65 THEN 'RSI 50-65'
                                WHEN p.rsi_value_at_entry BETWEEN 65 AND 75 THEN 'RSI 65-75'
                                WHEN p.rsi_value_at_entry > 75 THEN 'RSI > 75 (Overbought)'
                                ELSE 'Unknown'
                            END as rsi_range,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl
                        FROM trade_outcomes o
                        JOIN trade_strategy_params p ON o.trade_id = p.trade_id
                        WHERE o.status = 'closed'
                          AND p.rsi_value_at_entry IS NOT NULL
                          {user_filter}
                        GROUP BY rsi_range
                        HAVING COUNT(*) >= %s
                        ORDER BY win_rate DESC
                    """, params[::-1])  # Reverse params order for SQL
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting RSI performance: {e}")
            return []

    def get_performance_by_vix_level(self, user_id: int = None, min_trades: int = 10) -> List[Dict]:
        """Find performance across different VIX levels"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    user_filter = "AND o.user_id = %s" if user_id else ""
                    params = [min_trades, user_id] if user_id else [min_trades]

                    cur.execute(f"""
                        SELECT
                            CASE
                                WHEN c.vix_price < 12 THEN 'Very Low VIX (<12)'
                                WHEN c.vix_price BETWEEN 12 AND 16 THEN 'Low VIX (12-16)'
                                WHEN c.vix_price BETWEEN 16 AND 20 THEN 'Normal VIX (16-20)'
                                WHEN c.vix_price BETWEEN 20 AND 25 THEN 'Elevated VIX (20-25)'
                                WHEN c.vix_price BETWEEN 25 AND 30 THEN 'High VIX (25-30)'
                                WHEN c.vix_price > 30 THEN 'Very High VIX (>30)'
                                ELSE 'Unknown'
                            END as vix_regime,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl,
                            ROUND(AVG(c.vix_price)::numeric, 2) as avg_vix
                        FROM trade_outcomes o
                        JOIN trade_market_context c ON o.trade_id = c.trade_id
                        WHERE o.status = 'closed'
                          AND c.vix_price IS NOT NULL
                          {user_filter}
                        GROUP BY vix_regime
                        HAVING COUNT(*) >= %s
                        ORDER BY avg_return DESC
                    """, params[::-1])
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting VIX performance: {e}")
            return []

    def get_performance_by_timeframe(self, user_id: int = None, min_trades: int = 10) -> List[Dict]:
        """Compare performance across timeframes"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    user_filter = "AND o.user_id = %s" if user_id else ""
                    params = [min_trades, user_id] if user_id else [min_trades]

                    cur.execute(f"""
                        SELECT
                            t.timeframe,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl,
                            ROUND(AVG(o.hold_duration_minutes)::numeric, 0) as avg_hold_minutes
                        FROM trade_outcomes o
                        JOIN bot_trades t ON o.trade_id = t.id
                        WHERE o.status = 'closed'
                          {user_filter}
                        GROUP BY t.timeframe
                        HAVING COUNT(*) >= %s
                        ORDER BY win_rate DESC
                    """, params[::-1])
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting timeframe performance: {e}")
            return []

    def get_performance_by_time_of_day(self, user_id: int = None, min_trades: int = 10) -> List[Dict]:
        """Find best trading times"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    user_filter = "AND o.user_id = %s" if user_id else ""
                    params = [min_trades, user_id] if user_id else [min_trades]

                    cur.execute(f"""
                        SELECT
                            CASE
                                WHEN EXTRACT(HOUR FROM o.entry_time) BETWEEN 9 AND 10 THEN 'Market Open (9-10 AM)'
                                WHEN EXTRACT(HOUR FROM o.entry_time) BETWEEN 10 AND 12 THEN 'Morning (10 AM-12 PM)'
                                WHEN EXTRACT(HOUR FROM o.entry_time) BETWEEN 12 AND 14 THEN 'Midday (12-2 PM)'
                                WHEN EXTRACT(HOUR FROM o.entry_time) BETWEEN 14 AND 15 THEN 'Afternoon (2-3 PM)'
                                WHEN EXTRACT(HOUR FROM o.entry_time) >= 15 THEN 'Power Hour (3-4 PM)'
                                ELSE 'Pre/Post Market'
                            END as time_period,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl
                        FROM trade_outcomes o
                        WHERE o.status = 'closed'
                          AND o.entry_time IS NOT NULL
                          {user_filter}
                        GROUP BY time_period
                        HAVING COUNT(*) >= %s
                        ORDER BY win_rate DESC
                    """, params[::-1])
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting time of day performance: {e}")
            return []

    def get_performance_by_trend(self, user_id: int = None, min_trades: int = 10) -> List[Dict]:
        """Find performance by trend direction"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    user_filter = "AND o.user_id = %s" if user_id else ""
                    params = [min_trades, user_id] if user_id else [min_trades]

                    cur.execute(f"""
                        SELECT
                            COALESCE(p.trend_medium, 'unknown') as trend,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl
                        FROM trade_outcomes o
                        JOIN trade_strategy_params p ON o.trade_id = p.trade_id
                        WHERE o.status = 'closed'
                          AND p.trend_medium IS NOT NULL
                          {user_filter}
                        GROUP BY p.trend_medium
                        HAVING COUNT(*) >= %s
                        ORDER BY win_rate DESC
                    """, params[::-1])
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting trend performance: {e}")
            return []

    def get_overall_stats(self, user_id: int = None) -> Dict:
        """Get overall trading statistics"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    user_filter = "WHERE o.user_id = %s" if user_id else ""
                    params = [user_id] if user_id else []

                    cur.execute(f"""
                        SELECT
                            COUNT(*) as total_trades,
                            SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) as winning_trades,
                            SUM(CASE WHEN NOT o.is_winner AND NOT COALESCE(o.is_breakeven, FALSE) THEN 1 ELSE 0 END) as losing_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as win_rate,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return,
                            ROUND(AVG(CASE WHEN o.is_winner THEN o.pnl_percent END)::numeric, 2) as avg_win,
                            ROUND(AVG(CASE WHEN NOT o.is_winner THEN o.pnl_percent END)::numeric, 2) as avg_loss,
                            ROUND(AVG(o.hold_duration_minutes)::numeric, 0) as avg_hold_minutes
                        FROM trade_outcomes o
                        {user_filter}
                        AND o.status = 'closed'
                    """, params)
                    result = cur.fetchone()
                    return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting overall stats: {e}")
            return {}

    # =========================================================================
    # CLAUDE API INTEGRATION
    # =========================================================================

    def generate_insight_with_claude(self, pattern_data: Dict, pattern_type: str) -> Optional[Dict]:
        """
        Use Claude to generate a natural language insight from pattern data

        Args:
            pattern_data: Statistical data about the pattern
            pattern_type: Type of pattern (rsi, vix, timeframe, etc.)

        Returns:
            Dict with title, description, recommendation
        """
        if not self.client:
            return self._generate_fallback_insight(pattern_data, pattern_type)

        try:
            # Build the prompt
            prompt = self._build_analysis_prompt(pattern_data, pattern_type)

            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            response_text = message.content[0].text
            return self._parse_claude_response(response_text, pattern_data)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._generate_fallback_insight(pattern_data, pattern_type)

    def _build_analysis_prompt(self, pattern_data: Dict, pattern_type: str) -> str:
        """Build the prompt for Claude"""

        overall = pattern_data.get('overall_stats', {})
        patterns = pattern_data.get('patterns', [])

        prompt = f"""You are a trading strategy analyst. Analyze the following trading performance data and provide actionable insights.

## Overall Statistics
- Total Trades: {overall.get('total_trades', 0)}
- Win Rate: {overall.get('win_rate', 0)}%
- Average Return: {overall.get('avg_return', 0)}%
- Total P&L: ${overall.get('total_pnl', 0)}

## Pattern Analysis: {pattern_type.upper()}

"""
        for p in patterns:
            prompt += f"- {p.get('category', 'Unknown')}: {p.get('total_trades', 0)} trades, {p.get('win_rate', 0)}% win rate, {p.get('avg_return', 0)}% avg return\n"

        prompt += """

Based on this data, provide:

1. **Title**: A short, actionable insight title (max 10 words)
2. **Description**: 2-3 sentences explaining the pattern and why it matters
3. **Recommendation**: 1-2 specific, actionable recommendations

Format your response as:
TITLE: [your title]
DESCRIPTION: [your description]
RECOMMENDATION: [your recommendation]

Focus on the most statistically significant finding. Be specific about numbers and conditions."""

        return prompt

    def _parse_claude_response(self, response: str, pattern_data: Dict) -> Dict:
        """Parse Claude's response into structured data"""
        try:
            lines = response.strip().split('\n')
            title = ""
            description = ""
            recommendation = ""

            for line in lines:
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('DESCRIPTION:'):
                    description = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    recommendation = line.replace('RECOMMENDATION:', '').strip()

            # Get the best performing pattern
            patterns = pattern_data.get('patterns', [])
            best_pattern = patterns[0] if patterns else {}

            return {
                'title': title or "Trading Pattern Detected",
                'description': description or "Analysis found a notable pattern in your trading data.",
                'recommendation': recommendation or "Review your strategy parameters.",
                'observed_win_rate': best_pattern.get('win_rate'),
                'observed_avg_return': best_pattern.get('avg_return'),
                'observed_trades': best_pattern.get('total_trades'),
                'conditions': best_pattern
            }
        except Exception as e:
            logger.error(f"Error parsing Claude response: {e}")
            return self._generate_fallback_insight(pattern_data, "unknown")

    def _generate_fallback_insight(self, pattern_data: Dict, pattern_type: str) -> Dict:
        """Generate a basic insight without Claude API"""
        patterns = pattern_data.get('patterns', [])
        if not patterns:
            return None

        best = patterns[0]
        worst = patterns[-1] if len(patterns) > 1 else None

        # Generate basic insight
        title = f"Best {pattern_type.upper()} condition: {best.get('category', 'Unknown')}"
        description = f"With {best.get('total_trades', 0)} trades, this condition achieved a {best.get('win_rate', 0)}% win rate and {best.get('avg_return', 0)}% average return."

        recommendation = f"Consider focusing trades when {best.get('category', 'this condition')} is met."
        if worst and float(worst.get('win_rate', 0)) < 50:
            recommendation += f" Avoid trading when {worst.get('category', 'unfavorable conditions')} (only {worst.get('win_rate', 0)}% win rate)."

        return {
            'title': title,
            'description': description,
            'recommendation': recommendation,
            'observed_win_rate': best.get('win_rate'),
            'observed_avg_return': best.get('avg_return'),
            'observed_trades': best.get('total_trades'),
            'conditions': best
        }

    # =========================================================================
    # MAIN ANALYSIS FUNCTION
    # =========================================================================

    def run_full_analysis(self, user_id: int = None, min_trades: int = 10) -> List[Dict]:
        """
        Run complete analysis and generate insights

        Args:
            user_id: Specific user to analyze (None for all users)
            min_trades: Minimum trades required for pattern to be significant

        Returns:
            List of generated insights
        """
        insights = []
        overall_stats = self.get_overall_stats(user_id)

        # Need minimum trades to analyze
        if overall_stats.get('total_trades', 0) < min_trades:
            logger.info(f"Not enough trades ({overall_stats.get('total_trades', 0)}) for analysis")
            return []

        # Analyze different patterns
        analyses = [
            ('rsi', self.get_performance_by_rsi_threshold(user_id, min_trades)),
            ('vix', self.get_performance_by_vix_level(user_id, min_trades)),
            ('timeframe', self.get_performance_by_timeframe(user_id, min_trades)),
            ('time_of_day', self.get_performance_by_time_of_day(user_id, min_trades)),
            ('trend', self.get_performance_by_trend(user_id, min_trades)),
        ]

        for pattern_type, patterns in analyses:
            if not patterns:
                continue

            # Convert Decimal to float for JSON serialization
            patterns = self._convert_decimals(patterns)

            # Prepare data for Claude
            pattern_data = {
                'overall_stats': self._convert_decimals(overall_stats),
                'patterns': [
                    {
                        'category': p.get(list(p.keys())[0]),  # First key is usually the category
                        **{k: v for k, v in p.items()}
                    }
                    for p in patterns
                ]
            }

            # Generate insight
            insight = self.generate_insight_with_claude(pattern_data, pattern_type)
            if insight:
                insight['insight_type'] = pattern_type
                insight['sample_size'] = overall_stats.get('total_trades', 0)
                insight['confidence_score'] = self._calculate_confidence(patterns)
                insights.append(insight)

        return insights

    def _calculate_confidence(self, patterns: List[Dict]) -> float:
        """Calculate confidence score based on sample size and consistency"""
        if not patterns:
            return 0

        total_trades = sum(p.get('total_trades', 0) for p in patterns)
        best_pattern = patterns[0]
        best_trades = best_pattern.get('total_trades', 0)

        # Base confidence on sample size
        if total_trades < 20:
            base_confidence = 30
        elif total_trades < 50:
            base_confidence = 50
        elif total_trades < 100:
            base_confidence = 65
        elif total_trades < 200:
            base_confidence = 75
        else:
            base_confidence = 85

        # Boost if best pattern has significant edge
        win_rate = float(best_pattern.get('win_rate', 50))
        if win_rate > 65:
            base_confidence += 10
        elif win_rate > 60:
            base_confidence += 5

        return min(base_confidence, 95)

    def _convert_decimals(self, obj):
        """Convert Decimal objects to floats for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(v) for v in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    def save_insights_to_db(self, insights: List[Dict], user_id: int = None) -> int:
        """
        Save generated insights to the database

        Args:
            insights: List of insight dicts
            user_id: User ID (None for global insights)

        Returns:
            Number of insights saved
        """
        from bot_database import AIStrategyInsightsDB

        saved = 0
        for insight in insights:
            try:
                insight_id = AIStrategyInsightsDB.save_insight({
                    'insight_type': insight.get('insight_type'),
                    'confidence_score': insight.get('confidence_score'),
                    'sample_size': insight.get('sample_size'),
                    'title': insight.get('title'),
                    'description': insight.get('description'),
                    'recommendation': insight.get('recommendation'),
                    'observed_win_rate': insight.get('observed_win_rate'),
                    'observed_avg_return': insight.get('observed_avg_return'),
                    'observed_trades': insight.get('observed_trades'),
                    'conditions': insight.get('conditions'),
                    'recommended_params': insight.get('recommended_params')
                })
                if insight_id:
                    saved += 1
            except Exception as e:
                logger.error(f"Error saving insight: {e}")

        return saved


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == '__main__':
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("AI Strategy Analyzer - Test Run")
    print("=" * 60)

    analyzer = AIStrategyAnalyzer()

    print("\n1. Getting overall stats...")
    stats = analyzer.get_overall_stats()
    print(f"   Total trades: {stats.get('total_trades', 0)}")
    print(f"   Win rate: {stats.get('win_rate', 0)}%")
    print(f"   Total P&L: ${stats.get('total_pnl', 0)}")

    print("\n2. Getting VIX performance...")
    vix_perf = analyzer.get_performance_by_vix_level()
    for p in vix_perf[:3]:
        print(f"   {p}")

    print("\n3. Running full analysis...")
    insights = analyzer.run_full_analysis(min_trades=5)
    print(f"   Generated {len(insights)} insights")

    for i, insight in enumerate(insights, 1):
        print(f"\n   Insight {i}:")
        print(f"   Title: {insight.get('title')}")
        print(f"   Type: {insight.get('insight_type')}")
        print(f"   Confidence: {insight.get('confidence_score')}%")
        print(f"   Description: {insight.get('description')[:100]}...")

    if insights:
        print("\n4. Saving insights to database...")
        saved = analyzer.save_insights_to_db(insights)
        print(f"   Saved {saved} insights")

    print("\n" + "=" * 60)
    print("Analysis complete!")
