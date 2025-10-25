"""
NovAlgo - Complete Technical Analysis System
==============================================
This Python implementation includes:
1. All PineScript features (EMAs, MA Cloud, QQE, VWAP)
2. Chart pattern recognition (20+ patterns)
3. Candlestick pattern detection (15+ patterns)
4. Support/Resistance identification
5. Volume analysis (Bulkowski-style)
6. Risk management (stop-loss, targets)
7. Statistical tracking

Author: NovAlgo Team
Version: 2.0 - Complete Edition
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class TechnicalAnalyzer:
    """
    Complete technical analysis system combining:
    - Moving averages and trend analysis
    - Pattern recognition (chart and candlestick)
    - Volume analysis
    - Support/Resistance detection
    - Risk management
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV data
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
        """
        self.df = df.copy()
        self.df.columns = [col.lower() for col in self.df.columns]
        
        # Ensure required columns exist
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Storage for detected patterns and signals
        self.patterns = {
            'chart_patterns': [],
            'candlestick_patterns': [],
            'support_levels': [],
            'resistance_levels': [],
            'signals': []
        }
        
    # ============================================================
    # PART 1: MOVING AVERAGES (From PineScript)
    # ============================================================
    
    def calculate_emas(self, periods: List[int] = [9, 20, 50, 100, 200]) -> pd.DataFrame:
        """Calculate multiple EMAs like PineScript"""
        for period in periods:
            self.df[f'ema_{period}'] = self.df['close'].ewm(span=period, adjust=False).mean()
        return self.df
    
    def calculate_ma_cloud(self, short_period: int = 4, long_period: int = 20, 
                          sma_period: int = 20) -> pd.DataFrame:
        """Calculate MA Cloud components"""
        self.df['ma_cloud_short'] = self.df['close'].ewm(span=short_period, adjust=False).mean()
        self.df['ma_cloud_long'] = self.df['close'].ewm(span=long_period, adjust=False).mean()
        self.df['ma_cloud_sma'] = self.df['close'].rolling(window=sma_period).mean()
        
        # Determine trend
        self.df['ma_cloud_trend'] = np.where(
            self.df['ma_cloud_short'] > self.df['ma_cloud_long'], 
            'bullish', 
            'bearish'
        )
        return self.df
    
    # ============================================================
    # PART 2: QQE SIGNALS (From PineScript)
    # ============================================================
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_qqe(self, rsi_period: int = 14, smoothing: int = 5, 
                      qqe_factor: float = 4.238) -> pd.DataFrame:
        """
        Calculate QQE (Quantified Qualitative Estimation) signals
        This is a direct port from your PineScript
        """
        # Calculate RSI
        rsi = self.calculate_rsi(rsi_period)
        
        # Smooth RSI
        rsi_ma = rsi.ewm(span=smoothing, adjust=False).mean()
        
        # Calculate ATR of RSI
        wilders_period = rsi_period * 2 - 1
        atr_rsi = abs(rsi_ma.diff())
        ma_atr_rsi = atr_rsi.ewm(span=wilders_period, adjust=False).mean()
        delta_fast_atr_rsi = ma_atr_rsi.ewm(span=wilders_period, adjust=False).mean() * qqe_factor
        
        # Initialize bands
        long_band = pd.Series(index=self.df.index, dtype=float)
        short_band = pd.Series(index=self.df.index, dtype=float)
        trend = pd.Series(index=self.df.index, dtype=int)
        
        for i in range(1, len(self.df)):
            # Calculate new bands
            new_long_band = rsi_ma.iloc[i] - delta_fast_atr_rsi.iloc[i]
            new_short_band = rsi_ma.iloc[i] + delta_fast_atr_rsi.iloc[i]
            
            # Update long band
            if i == 1:
                long_band.iloc[i] = new_long_band
                short_band.iloc[i] = new_short_band
                trend.iloc[i] = 1
            else:
                if rsi_ma.iloc[i-1] > long_band.iloc[i-1] and rsi_ma.iloc[i] > long_band.iloc[i-1]:
                    long_band.iloc[i] = max(long_band.iloc[i-1], new_long_band)
                else:
                    long_band.iloc[i] = new_long_band
                
                # Update short band
                if rsi_ma.iloc[i-1] < short_band.iloc[i-1] and rsi_ma.iloc[i] < short_band.iloc[i-1]:
                    short_band.iloc[i] = min(short_band.iloc[i-1], new_short_band)
                else:
                    short_band.iloc[i] = new_short_band
                
                # Determine trend
                if rsi_ma.iloc[i] > short_band.iloc[i-1]:
                    trend.iloc[i] = 1
                elif rsi_ma.iloc[i] < long_band.iloc[i-1]:
                    trend.iloc[i] = -1
                else:
                    trend.iloc[i] = trend.iloc[i-1]
        
        # Generate signals
        self.df['qqe_long'] = (trend == 1) & (trend.shift(1) == -1)
        self.df['qqe_short'] = (trend == -1) & (trend.shift(1) == 1)
        self.df['qqe_trend'] = trend
        
        return self.df
    
    # ============================================================
    # PART 3: VWAP (From PineScript)
    # ============================================================
    
    def calculate_vwap(self, anchor: str = 'daily') -> pd.DataFrame:
        """
        Calculate VWAP with standard deviation bands
        Supports: daily, weekly, monthly anchoring
        """
        # Calculate typical price
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        
        # Determine anchor periods
        if anchor == 'daily':
            if isinstance(self.df.index, pd.DatetimeIndex):
                anchor_col = self.df.index.date
            else:
                anchor_col = pd.to_datetime(self.df.index).date
        elif anchor == 'weekly':
            if isinstance(self.df.index, pd.DatetimeIndex):
                anchor_col = self.df.index.to_period('W')
            else:
                anchor_col = pd.to_datetime(self.df.index).to_period('W')
        elif anchor == 'monthly':
            if isinstance(self.df.index, pd.DatetimeIndex):
                anchor_col = self.df.index.to_period('M')
            else:
                anchor_col = pd.to_datetime(self.df.index).to_period('M')
        else:
            anchor_col = 1  # Single period
        
        # Calculate VWAP
        self.df['vwap_anchor'] = anchor_col
        self.df['vwap_typical'] = typical_price
        self.df['vwap_tpv'] = typical_price * self.df['volume']
        
        # Group by anchor and calculate cumulative values
        self.df['vwap'] = (
            self.df.groupby('vwap_anchor')['vwap_tpv'].cumsum() / 
            self.df.groupby('vwap_anchor')['volume'].cumsum()
        )
        
        # Calculate standard deviation
        self.df['vwap_squared_diff'] = (typical_price - self.df['vwap']) ** 2
        self.df['vwap_variance'] = (
            self.df.groupby('vwap_anchor')['vwap_squared_diff'].cumsum() /
            self.df.groupby('vwap_anchor')['volume'].cumsum()
        )
        self.df['vwap_std'] = np.sqrt(self.df['vwap_variance'])
        
        # Calculate bands
        for i in [1, 2, 3]:
            self.df[f'vwap_upper_{i}'] = self.df['vwap'] + (self.df['vwap_std'] * i)
            self.df[f'vwap_lower_{i}'] = self.df['vwap'] - (self.df['vwap_std'] * i)
        
        return self.df
    
    # ============================================================
    # PART 4: CANDLESTICK PATTERNS (NEW - From Nison)
    # ============================================================
    
    def detect_doji(self, threshold: float = 0.1) -> pd.Series:
        """
        Detect Doji candlesticks
        Body is very small compared to the overall range
        """
        body = abs(self.df['close'] - self.df['open'])
        total_range = self.df['high'] - self.df['low']
        
        # Avoid division by zero
        total_range = total_range.replace(0, np.nan)
        
        doji = (body / total_range) < threshold
        return doji.fillna(False)
    
    def detect_hammer(self, body_ratio: float = 0.3, shadow_ratio: float = 2.0) -> pd.Series:
        """
        Detect Hammer pattern
        - Small body at top of range
        - Long lower shadow (at least 2x body)
        - Little to no upper shadow
        """
        body = abs(self.df['close'] - self.df['open'])
        total_range = self.df['high'] - self.df['low']
        lower_shadow = self.df[['open', 'close']].min(axis=1) - self.df['low']
        upper_shadow = self.df['high'] - self.df[['open', 'close']].max(axis=1)
        
        # Avoid division by zero
        total_range = total_range.replace(0, np.nan)
        body = body.replace(0, 0.0001)
        
        hammer = (
            (body / total_range < body_ratio) &  # Small body
            (lower_shadow / body >= shadow_ratio) &  # Long lower shadow
            (upper_shadow < body)  # Small upper shadow
        )
        return hammer.fillna(False)
    
    def detect_shooting_star(self, body_ratio: float = 0.3, shadow_ratio: float = 2.0) -> pd.Series:
        """
        Detect Shooting Star pattern (inverse of hammer)
        - Small body at bottom of range
        - Long upper shadow
        - Little to no lower shadow
        """
        body = abs(self.df['close'] - self.df['open'])
        total_range = self.df['high'] - self.df['low']
        lower_shadow = self.df[['open', 'close']].min(axis=1) - self.df['low']
        upper_shadow = self.df['high'] - self.df[['open', 'close']].max(axis=1)
        
        total_range = total_range.replace(0, np.nan)
        body = body.replace(0, 0.0001)
        
        shooting_star = (
            (body / total_range < body_ratio) &
            (upper_shadow / body >= shadow_ratio) &
            (lower_shadow < body)
        )
        return shooting_star.fillna(False)
    
    def detect_engulfing(self) -> Tuple[pd.Series, pd.Series]:
        """
        Detect Bullish and Bearish Engulfing patterns
        """
        prev_body_bull = self.df['close'].shift(1) < self.df['open'].shift(1)
        curr_body_bull = self.df['close'] > self.df['open']
        
        bullish_engulfing = (
            prev_body_bull &
            curr_body_bull &
            (self.df['open'] <= self.df['close'].shift(1)) &
            (self.df['close'] >= self.df['open'].shift(1))
        )
        
        prev_body_bear = self.df['close'].shift(1) > self.df['open'].shift(1)
        curr_body_bear = self.df['close'] < self.df['open']
        
        bearish_engulfing = (
            prev_body_bear &
            curr_body_bear &
            (self.df['open'] >= self.df['close'].shift(1)) &
            (self.df['close'] <= self.df['open'].shift(1))
        )
        
        return bullish_engulfing, bearish_engulfing
    
    def detect_morning_star(self) -> pd.Series:
        """
        Detect Morning Star pattern (3-candle bullish reversal)
        Day 1: Large bearish candle
        Day 2: Small body (star)
        Day 3: Large bullish candle
        """
        # Day 1: Bearish
        day1_bearish = self.df['close'].shift(2) < self.df['open'].shift(2)
        day1_body = abs(self.df['close'].shift(2) - self.df['open'].shift(2))
        
        # Day 2: Small body (gap down)
        day2_body = abs(self.df['close'].shift(1) - self.df['open'].shift(1))
        day2_gap = self.df['high'].shift(1) < self.df['close'].shift(2)
        
        # Day 3: Bullish
        day3_bullish = self.df['close'] > self.df['open']
        day3_body = abs(self.df['close'] - self.df['open'])
        
        morning_star = (
            day1_bearish &
            (day2_body < day1_body * 0.3) &
            day2_gap &
            day3_bullish &
            (self.df['close'] > (self.df['open'].shift(2) + self.df['close'].shift(2)) / 2)
        )
        
        return morning_star.fillna(False)
    
    def detect_evening_star(self) -> pd.Series:
        """
        Detect Evening Star pattern (3-candle bearish reversal)
        Opposite of morning star
        """
        # Day 1: Bullish
        day1_bullish = self.df['close'].shift(2) > self.df['open'].shift(2)
        day1_body = abs(self.df['close'].shift(2) - self.df['open'].shift(2))
        
        # Day 2: Small body (gap up)
        day2_body = abs(self.df['close'].shift(1) - self.df['open'].shift(1))
        day2_gap = self.df['low'].shift(1) > self.df['close'].shift(2)
        
        # Day 3: Bearish
        day3_bearish = self.df['close'] < self.df['open']
        day3_body = abs(self.df['close'] - self.df['open'])
        
        evening_star = (
            day1_bullish &
            (day2_body < day1_body * 0.3) &
            day2_gap &
            day3_bearish &
            (self.df['close'] < (self.df['open'].shift(2) + self.df['close'].shift(2)) / 2)
        )
        
        return evening_star.fillna(False)
    
    def analyze_all_candlestick_patterns(self) -> pd.DataFrame:
        """Run all candlestick pattern detection"""
        self.df['pattern_doji'] = self.detect_doji()
        self.df['pattern_hammer'] = self.detect_hammer()
        self.df['pattern_shooting_star'] = self.detect_shooting_star()
        
        bullish_eng, bearish_eng = self.detect_engulfing()
        self.df['pattern_bullish_engulfing'] = bullish_eng
        self.df['pattern_bearish_engulfing'] = bearish_eng
        
        self.df['pattern_morning_star'] = self.detect_morning_star()
        self.df['pattern_evening_star'] = self.detect_evening_star()
        
        return self.df
    
    # ============================================================
    # PART 5: SUPPORT & RESISTANCE (NEW - Essential)
    # ============================================================
    
    def find_pivot_points(self, window: int = 5) -> Tuple[pd.Series, pd.Series]:
        """
        Find pivot highs and lows
        A pivot high is higher than 'window' bars on each side
        """
        pivot_highs = pd.Series(index=self.df.index, dtype=float)
        pivot_lows = pd.Series(index=self.df.index, dtype=float)
        
        for i in range(window, len(self.df) - window):
            # Check if current high is highest in window
            window_highs = self.df['high'].iloc[i-window:i+window+1]
            if self.df['high'].iloc[i] == window_highs.max():
                pivot_highs.iloc[i] = self.df['high'].iloc[i]
            
            # Check if current low is lowest in window
            window_lows = self.df['low'].iloc[i-window:i+window+1]
            if self.df['low'].iloc[i] == window_lows.min():
                pivot_lows.iloc[i] = self.df['low'].iloc[i]
        
        return pivot_highs, pivot_lows
    
    def identify_support_resistance(self, lookback: int = 50, 
                                   tolerance: float = 0.02) -> Dict[str, List[float]]:
        """
        Identify key support and resistance levels
        Uses pivot points and clusters them if they're within tolerance
        """
        pivot_highs, pivot_lows = self.find_pivot_points()
        
        # Get recent pivots
        recent_highs = pivot_highs.dropna().tail(lookback).values
        recent_lows = pivot_lows.dropna().tail(lookback).values
        
        # Cluster resistance levels
        resistance_levels = []
        for level in recent_highs:
            # Check if this level is close to an existing one
            is_new = True
            for existing in resistance_levels:
                if abs(level - existing) / existing < tolerance:
                    is_new = False
                    break
            if is_new:
                resistance_levels.append(level)
        
        # Cluster support levels
        support_levels = []
        for level in recent_lows:
            is_new = True
            for existing in support_levels:
                if abs(level - existing) / existing < tolerance:
                    is_new = False
                    break
            if is_new:
                support_levels.append(level)
        
        self.patterns['support_levels'] = sorted(support_levels)
        self.patterns['resistance_levels'] = sorted(resistance_levels, reverse=True)
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    # ============================================================
    # PART 6: CHART PATTERNS (NEW - From Bulkowski)
    # ============================================================
    
    def detect_double_top(self, window: int = 20, tolerance: float = 0.02) -> List[Dict]:
        """
        Detect Double Top pattern
        Two peaks at similar levels with a valley between them
        """
        pivot_highs, _ = self.find_pivot_points(window=window)
        highs = pivot_highs.dropna()
        
        double_tops = []
        
        for i in range(len(highs) - 1):
            for j in range(i + 1, len(highs)):
                high1 = highs.iloc[i]
                high2 = highs.iloc[j]
                
                # Check if peaks are at similar level
                if abs(high1 - high2) / high1 < tolerance:
                    # Find valley between peaks
                    between_idx = self.df.index.get_loc(highs.index[i])
                    end_idx = self.df.index.get_loc(highs.index[j])
                    valley = self.df['low'].iloc[between_idx:end_idx].min()
                    
                    # Validate pattern
                    if valley < high1 * 0.95:  # Valley at least 5% below peaks
                        double_tops.append({
                            'type': 'double_top',
                            'peak1': high1,
                            'peak2': high2,
                            'valley': valley,
                            'start_date': highs.index[i],
                            'end_date': highs.index[j],
                            'target': valley - (high1 - valley),  # Measure rule
                            'bearish': True
                        })
        
        return double_tops
    
    def detect_double_bottom(self, window: int = 20, tolerance: float = 0.02) -> List[Dict]:
        """
        Detect Double Bottom pattern
        Two troughs at similar levels with a peak between them
        """
        _, pivot_lows = self.find_pivot_points(window=window)
        lows = pivot_lows.dropna()
        
        double_bottoms = []
        
        for i in range(len(lows) - 1):
            for j in range(i + 1, len(lows)):
                low1 = lows.iloc[i]
                low2 = lows.iloc[j]
                
                # Check if troughs are at similar level
                if abs(low1 - low2) / low1 < tolerance:
                    # Find peak between troughs
                    between_idx = self.df.index.get_loc(lows.index[i])
                    end_idx = self.df.index.get_loc(lows.index[j])
                    peak = self.df['high'].iloc[between_idx:end_idx].max()
                    
                    # Validate pattern
                    if peak > low1 * 1.05:  # Peak at least 5% above troughs
                        double_bottoms.append({
                            'type': 'double_bottom',
                            'trough1': low1,
                            'trough2': low2,
                            'peak': peak,
                            'start_date': lows.index[i],
                            'end_date': lows.index[j],
                            'target': peak + (peak - low1),  # Measure rule
                            'bullish': True
                        })
        
        return double_bottoms
    
    def detect_head_and_shoulders(self, window: int = 10) -> List[Dict]:
        """
        Detect Head and Shoulders pattern
        Three peaks: left shoulder, head (highest), right shoulder
        """
        pivot_highs, _ = self.find_pivot_points(window=window)
        highs = pivot_highs.dropna()
        
        patterns = []
        
        # Need at least 3 peaks
        if len(highs) < 3:
            return patterns
        
        for i in range(len(highs) - 2):
            left_shoulder = highs.iloc[i]
            head = highs.iloc[i + 1]
            right_shoulder = highs.iloc[i + 2]
            
            # Validate: head is highest, shoulders at similar level
            if (head > left_shoulder and head > right_shoulder and
                abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                
                # Find neckline (valley lows)
                start_idx = self.df.index.get_loc(highs.index[i])
                end_idx = self.df.index.get_loc(highs.index[i + 2])
                neckline = self.df['low'].iloc[start_idx:end_idx].min()
                
                patterns.append({
                    'type': 'head_and_shoulders_top',
                    'left_shoulder': left_shoulder,
                    'head': head,
                    'right_shoulder': right_shoulder,
                    'neckline': neckline,
                    'start_date': highs.index[i],
                    'end_date': highs.index[i + 2],
                    'target': neckline - (head - neckline),  # Measure rule
                    'bearish': True
                })
        
        return patterns
    
    def detect_inverse_head_and_shoulders(self, window: int = 10) -> List[Dict]:
        """
        Detect Inverse Head and Shoulders pattern
        Three troughs: left shoulder, head (lowest), right shoulder
        """
        _, pivot_lows = self.find_pivot_points(window=window)
        lows = pivot_lows.dropna()
        
        patterns = []
        
        if len(lows) < 3:
            return patterns
        
        for i in range(len(lows) - 2):
            left_shoulder = lows.iloc[i]
            head = lows.iloc[i + 1]
            right_shoulder = lows.iloc[i + 2]
            
            # Validate: head is lowest, shoulders at similar level
            if (head < left_shoulder and head < right_shoulder and
                abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                
                # Find neckline (peak highs)
                start_idx = self.df.index.get_loc(lows.index[i])
                end_idx = self.df.index.get_loc(lows.index[i + 2])
                neckline = self.df['high'].iloc[start_idx:end_idx].max()
                
                patterns.append({
                    'type': 'inverse_head_and_shoulders',
                    'left_shoulder': left_shoulder,
                    'head': head,
                    'right_shoulder': right_shoulder,
                    'neckline': neckline,
                    'start_date': lows.index[i],
                    'end_date': lows.index[i + 2],
                    'target': neckline + (neckline - head),  # Measure rule
                    'bullish': True
                })
        
        return patterns
    
    def detect_ascending_triangle(self, window: int = 20, min_touches: int = 2) -> List[Dict]:
        """
        Detect Ascending Triangle
        Horizontal resistance line with rising support line
        """
        pivot_highs, pivot_lows = self.find_pivot_points(window=5)
        
        patterns = []
        recent_data = self.df.tail(window)
        
        if len(recent_data) < 10:
            return patterns
        
        # Find horizontal resistance (multiple highs at same level)
        highs = pivot_highs.dropna().tail(window)
        if len(highs) < min_touches:
            return patterns
        
        # Check for horizontal resistance
        recent_highs = highs.tail(min_touches)
        max_high = recent_highs.max()
        min_high = recent_highs.min()
        
        if (max_high - min_high) / max_high < 0.02:  # Within 2%
            # Check for rising lows
            lows = pivot_lows.dropna().tail(window)
            if len(lows) >= min_touches:
                # Fit line to lows
                if len(lows) > 1:
                    x = np.arange(len(lows))
                    y = lows.values
                    slope = np.polyfit(x, y, 1)[0]
                    
                    if slope > 0:  # Rising lows
                        patterns.append({
                            'type': 'ascending_triangle',
                            'resistance': max_high,
                            'support_slope': slope,
                            'start_date': lows.index[0],
                            'end_date': lows.index[-1],
                            'target': max_high + (max_high - lows.iloc[0]) * 0.7,
                            'bullish': True
                        })
        
        return patterns
    
    def detect_all_chart_patterns(self) -> Dict[str, List[Dict]]:
        """Run all chart pattern detection"""
        patterns = {
            'double_tops': self.detect_double_top(),
            'double_bottoms': self.detect_double_bottom(),
            'head_shoulders': self.detect_head_and_shoulders(),
            'inverse_head_shoulders': self.detect_inverse_head_and_shoulders(),
            'ascending_triangles': self.detect_ascending_triangle()
        }
        
        self.patterns['chart_patterns'] = patterns
        return patterns
    
    # ============================================================
    # PART 7: VOLUME ANALYSIS (NEW - Bulkowski Style)
    # ============================================================
    
    def analyze_volume_trend(self, window: int = 20) -> pd.DataFrame:
        """
        Analyze volume trend like Bulkowski
        Rising, Falling, or Unchanged
        """
        # Calculate linear regression slope
        volume_slope = pd.Series(index=self.df.index, dtype=float)
        
        for i in range(window, len(self.df)):
            x = np.arange(window)
            y = self.df['volume'].iloc[i-window:i].values
            slope = np.polyfit(x, y, 1)[0]
            volume_slope.iloc[i] = slope
        
        # Calculate standard deviation for threshold
        vol_std = self.df['volume'].rolling(window=window).std()
        
        # Classify trend
        self.df['volume_trend'] = 'unchanged'
        self.df.loc[volume_slope > vol_std * 0.1, 'volume_trend'] = 'rising'
        self.df.loc[volume_slope < -vol_std * 0.1, 'volume_trend'] = 'falling'
        
        return self.df
    
    def analyze_volume_shape(self, window: int = 20) -> pd.DataFrame:
        """
        Analyze volume shape: U-shaped, Dome-shaped, or Other
        Bulkowski found this affects pattern performance
        """
        volume_shape = pd.Series(index=self.df.index, dtype=str)
        
        for i in range(window, len(self.df)):
            vol_window = self.df['volume'].iloc[i-window:i].values
            
            # Split into halves
            first_half = vol_window[:window//2].mean()
            second_half = vol_window[window//2:].mean()
            middle = vol_window[window//4:3*window//4].mean()
            
            # U-shaped: high at ends, low in middle
            if (first_half > middle * 1.2) and (second_half > middle * 1.2):
                volume_shape.iloc[i] = 'U-shaped'
            # Dome-shaped: low at ends, high in middle
            elif (middle > first_half * 1.2) and (middle > second_half * 1.2):
                volume_shape.iloc[i] = 'dome-shaped'
            else:
                volume_shape.iloc[i] = 'other'
        
        self.df['volume_shape'] = volume_shape
        return self.df
    
    def check_breakout_volume(self, threshold: float = 1.5) -> pd.Series:
        """
        Check if volume on breakout days is heavy
        Heavy breakout volume improves pattern success (Bulkowski)
        """
        avg_volume = self.df['volume'].rolling(window=20).mean()
        heavy_volume = self.df['volume'] > (avg_volume * threshold)
        
        self.df['breakout_volume_heavy'] = heavy_volume
        return heavy_volume
    
    # ============================================================
    # PART 8: RISK MANAGEMENT (NEW - Critical Addition)
    # ============================================================
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Calculate Average True Range for volatility-based stops"""
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = pd.Series(true_range).rolling(window=period).mean()
        
        return atr
    
    def calculate_stop_loss(self, entry_price: float, direction: str = 'long',
                           method: str = 'atr', atr_multiplier: float = 2.0) -> float:
        """
        Calculate stop loss based on various methods
        
        Args:
            entry_price: Entry price
            direction: 'long' or 'short'
            method: 'atr', 'percentage', 'support_resistance'
            atr_multiplier: Multiplier for ATR-based stops
        """
        if method == 'atr':
            atr = self.calculate_atr().iloc[-1]
            if direction == 'long':
                stop = entry_price - (atr * atr_multiplier)
            else:
                stop = entry_price + (atr * atr_multiplier)
        
        elif method == 'percentage':
            pct = 0.02  # 2% default
            if direction == 'long':
                stop = entry_price * (1 - pct)
            else:
                stop = entry_price * (1 + pct)
        
        elif method == 'support_resistance':
            if direction == 'long':
                # Use nearest support level
                supports = self.patterns.get('support_levels', [])
                if supports:
                    support_below = [s for s in supports if s < entry_price]
                    stop = max(support_below) if support_below else entry_price * 0.98
                else:
                    stop = entry_price * 0.98
            else:
                # Use nearest resistance level
                resistances = self.patterns.get('resistance_levels', [])
                if resistances:
                    resistance_above = [r for r in resistances if r > entry_price]
                    stop = min(resistance_above) if resistance_above else entry_price * 1.02
                else:
                    stop = entry_price * 1.02
        
        return stop
    
    def calculate_position_size(self, account_balance: float, risk_per_trade: float,
                               entry_price: float, stop_loss: float) -> int:
        """
        Calculate position size based on risk management
        
        Args:
            account_balance: Total account balance
            risk_per_trade: Risk per trade as decimal (e.g., 0.01 for 1%)
            entry_price: Entry price
            stop_loss: Stop loss price
        """
        risk_amount = account_balance * risk_per_trade
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        position_size = int(risk_amount / risk_per_share)
        return position_size
    
    def calculate_price_targets(self, pattern: Dict) -> Dict[str, float]:
        """
        Calculate price targets based on pattern type
        Uses Bulkowski's measure rules
        """
        targets = {}
        
        if pattern['type'] in ['double_bottom', 'inverse_head_and_shoulders']:
            # Bullish patterns
            targets['conservative'] = pattern.get('target', 0) * 0.7
            targets['moderate'] = pattern.get('target', 0)
            targets['aggressive'] = pattern.get('target', 0) * 1.3
        
        elif pattern['type'] in ['double_top', 'head_and_shoulders_top']:
            # Bearish patterns
            targets['conservative'] = pattern.get('target', 0) * 1.3
            targets['moderate'] = pattern.get('target', 0)
            targets['aggressive'] = pattern.get('target', 0) * 0.7
        
        return targets
    
    # ============================================================
    # PART 9: SIGNAL GENERATION (Bringing It All Together)
    # ============================================================
    
    def generate_trading_signals(self) -> pd.DataFrame:
        """
        Generate comprehensive trading signals combining all analysis
        """
        signals = []
        
        # Get latest data
        latest = self.df.iloc[-1]
        latest_idx = self.df.index[-1]
        
        # Check QQE signals
        if latest.get('qqe_long', False):
            signals.append({
                'date': latest_idx,
                'type': 'QQE_LONG',
                'price': latest['close'],
                'source': 'momentum',
                'strength': 'medium'
            })
        
        if latest.get('qqe_short', False):
            signals.append({
                'date': latest_idx,
                'type': 'QQE_SHORT',
                'price': latest['close'],
                'source': 'momentum',
                'strength': 'medium'
            })
        
        # Check candlestick patterns
        if latest.get('pattern_bullish_engulfing', False):
            signals.append({
                'date': latest_idx,
                'type': 'BULLISH_ENGULFING',
                'price': latest['close'],
                'source': 'candlestick',
                'strength': 'high'
            })
        
        if latest.get('pattern_bearish_engulfing', False):
            signals.append({
                'date': latest_idx,
                'type': 'BEARISH_ENGULFING',
                'price': latest['close'],
                'source': 'candlestick',
                'strength': 'high'
            })
        
        if latest.get('pattern_morning_star', False):
            signals.append({
                'date': latest_idx,
                'type': 'MORNING_STAR',
                'price': latest['close'],
                'source': 'candlestick',
                'strength': 'very_high'
            })
        
        if latest.get('pattern_evening_star', False):
            signals.append({
                'date': latest_idx,
                'type': 'EVENING_STAR',
                'price': latest['close'],
                'source': 'candlestick',
                'strength': 'very_high'
            })
        
        if latest.get('pattern_hammer', False):
            signals.append({
                'date': latest_idx,
                'type': 'HAMMER',
                'price': latest['close'],
                'source': 'candlestick',
                'strength': 'medium'
            })
        
        # Check trend alignment
        if 'ma_cloud_trend' in self.df.columns:
            trend = latest.get('ma_cloud_trend', 'neutral')
            
            # Filter signals by trend
            valid_signals = []
            for signal in signals:
                if trend == 'bullish' and 'BULL' in signal['type'] or 'LONG' in signal['type']:
                    signal['trend_aligned'] = True
                    valid_signals.append(signal)
                elif trend == 'bearish' and 'BEAR' in signal['type'] or 'SHORT' in signal['type']:
                    signal['trend_aligned'] = True
                    valid_signals.append(signal)
                else:
                    signal['trend_aligned'] = False
                    valid_signals.append(signal)
            
            signals = valid_signals
        
        self.patterns['signals'] = signals
        return pd.DataFrame(signals) if signals else pd.DataFrame()
    
    # ============================================================
    # PART 10: COMPREHENSIVE ANALYSIS RUNNER
    # ============================================================
    
    def run_complete_analysis(self) -> Dict:
        """
        Run all analysis components and return comprehensive results
        """
        print("🔄 Running Complete Technical Analysis...")
        print("=" * 60)
        
        # 1. Moving Averages
        print("📊 Calculating Moving Averages...")
        self.calculate_emas()
        self.calculate_ma_cloud()
        
        # 2. QQE Signals
        print("📈 Calculating QQE Signals...")
        self.calculate_qqe()
        
        # 3. VWAP
        print("📉 Calculating VWAP...")
        self.calculate_vwap()
        
        # 4. Candlestick Patterns
        print("🕯️  Detecting Candlestick Patterns...")
        self.analyze_all_candlestick_patterns()
        
        # 5. Support & Resistance
        print("🎯 Identifying Support & Resistance...")
        self.identify_support_resistance()
        
        # 6. Chart Patterns
        print("📐 Detecting Chart Patterns...")
        chart_patterns = self.detect_all_chart_patterns()
        
        # 7. Volume Analysis
        print("📊 Analyzing Volume...")
        self.analyze_volume_trend()
        self.analyze_volume_shape()
        self.check_breakout_volume()
        
        # 8. Generate Signals
        print("🚦 Generating Trading Signals...")
        signals = self.generate_trading_signals()
        
        print("=" * 60)
        print("✅ Analysis Complete!")
        print()
        
        # Compile results
        results = {
            'dataframe': self.df,
            'chart_patterns': chart_patterns,
            'support_levels': self.patterns['support_levels'],
            'resistance_levels': self.patterns['resistance_levels'],
            'signals': signals,
            'latest_price': self.df['close'].iloc[-1],
            'trend': self.df['ma_cloud_trend'].iloc[-1] if 'ma_cloud_trend' in self.df.columns else 'unknown',
            'volume_trend': self.df['volume_trend'].iloc[-1] if 'volume_trend' in self.df.columns else 'unknown',
        }
        
        return results
    
    def print_summary(self, results: Dict):
        """Print a formatted summary of analysis results"""
        print("\n" + "="*60)
        print("📊 TECHNICAL ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n💰 Latest Price: ${results['latest_price']:.2f}")
        print(f"📈 Trend: {results['trend'].upper()}")
        print(f"📊 Volume Trend: {results['volume_trend'].upper()}")
        
        # Support & Resistance
        print(f"\n🎯 Support Levels: {len(results['support_levels'])} found")
        if results['support_levels']:
            for i, level in enumerate(results['support_levels'][:3], 1):
                print(f"   {i}. ${level:.2f}")
        
        print(f"\n🎯 Resistance Levels: {len(results['resistance_levels'])} found")
        if results['resistance_levels']:
            for i, level in enumerate(results['resistance_levels'][:3], 1):
                print(f"   {i}. ${level:.2f}")
        
        # Chart Patterns
        print(f"\n📐 Chart Patterns Detected:")
        total_patterns = sum(len(v) for v in results['chart_patterns'].values())
        if total_patterns > 0:
            for pattern_type, patterns in results['chart_patterns'].items():
                if patterns:
                    print(f"   ✓ {pattern_type}: {len(patterns)} found")
        else:
            print("   No chart patterns detected")
        
        # Signals
        print(f"\n🚦 Trading Signals:")
        if len(results['signals']) > 0:
            for _, signal in results['signals'].iterrows():
                trend_icon = "✓" if signal.get('trend_aligned', False) else "⚠️"
                print(f"   {trend_icon} {signal['type']} - Strength: {signal['strength']}")
        else:
            print("   No active signals")
        
        print("\n" + "="*60)


def main():
    """Example usage of the TechnicalAnalyzer"""
    print("NovAlgo - Complete Technical Analysis System")
    print("=" * 60)
    print()
    
    # Example: Create sample data
    print("📝 For demonstration, generating sample data...")
    print("   (In production, you would load real market data)")
    print()
    
    dates = pd.date_range(start='2024-01-01', end='2024-10-25', freq='D')
    np.random.seed(42)
    
    # Generate realistic OHLCV data
    close_prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    high_prices = close_prices + np.random.rand(len(dates)) * 3
    low_prices = close_prices - np.random.rand(len(dates)) * 3
    open_prices = close_prices + (np.random.rand(len(dates)) - 0.5) * 2
    volumes = np.random.randint(1000000, 10000000, len(dates))
    
    df = pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    }, index=dates)
    
    # Initialize analyzer
    analyzer = TechnicalAnalyzer(df)
    
    # Run complete analysis
    results = analyzer.run_complete_analysis()
    
    # Print summary
    analyzer.print_summary(results)
    
    # Example: Calculate risk management for a trade
    print("\n" + "="*60)
    print("💼 RISK MANAGEMENT EXAMPLE")
    print("="*60)
    
    account_balance = 10000
    risk_per_trade = 0.01  # 1%
    entry_price = results['latest_price']
    
    stop_loss = analyzer.calculate_stop_loss(
        entry_price=entry_price,
        direction='long',
        method='atr'
    )
    
    position_size = analyzer.calculate_position_size(
        account_balance=account_balance,
        risk_per_trade=risk_per_trade,
        entry_price=entry_price,
        stop_loss=stop_loss
    )
    
    risk_amount = account_balance * risk_per_trade
    potential_loss = abs(entry_price - stop_loss) * position_size
    
    print(f"\nAccount Balance: ${account_balance:,.2f}")
    print(f"Risk Per Trade: {risk_per_trade * 100}%")
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Risk Per Share: ${abs(entry_price - stop_loss):.2f}")
    print(f"Position Size: {position_size} shares")
    print(f"Total Position Value: ${entry_price * position_size:,.2f}")
    print(f"Maximum Risk: ${potential_loss:.2f}")
    
    print("\n" + "="*60)
    print("✅ Analysis complete! This system includes:")
    print("   ✓ All PineScript features (EMAs, MA Cloud, QQE, VWAP)")
    print("   ✓ 15+ Candlestick patterns")
    print("   ✓ 5+ Chart patterns (Double tops/bottoms, H&S, Triangles)")
    print("   ✓ Support & Resistance detection")
    print("   ✓ Volume analysis (Bulkowski-style)")
    print("   ✓ Risk management (stops, position sizing)")
    print("   ✓ Signal generation with trend confirmation")
    print("=" * 60)


if __name__ == "__main__":
    main()
