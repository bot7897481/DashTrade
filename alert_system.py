"""
Alert System for NovAlgo Trading Dashboard
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AlertCondition:
    """Represents an alert condition"""
    alert_type: str
    indicator: str
    operator: str
    value: float
    indicator2: Optional[str] = None
    
    def check(self, row: pd.Series) -> bool:
        """Check if alert condition is met"""
        try:
            if self.indicator2:
                val1 = row.get(self.indicator)
                val2 = row.get(self.indicator2)
                
                if val1 is None or val2 is None:
                    return False
                
                if self.operator == 'crosses_above':
                    return val1 > val2
                elif self.operator == 'crosses_below':
                    return val1 < val2
                elif self.operator == '>':
                    return val1 > val2
                elif self.operator == '<':
                    return val1 < val2
            else:
                val = row.get(self.indicator)
                
                if val is None:
                    return False
                
                if isinstance(val, bool):
                    return val == self.value
                
                if self.operator == '>':
                    return val > self.value
                elif self.operator == '<':
                    return val < self.value
                elif self.operator == '>=':
                    return val >= self.value
                elif self.operator == '<=':
                    return val <= self.value
                elif self.operator == '==':
                    if isinstance(self.value, str):
                        return str(val) == self.value
                    return val == self.value
            
            return False
        except:
            return False

class AlertMonitor:
    """Monitor market data for alert conditions"""
    
    ALERT_TYPES = {
        'Price': {
            'description': 'Price alerts',
            'conditions': [
                'price_above',
                'price_below',
                'price_crosses_above',
                'price_crosses_below'
            ]
        },
        'Indicator': {
            'description': 'Technical indicator alerts',
            'conditions': [
                'ema_crossover',
                'qqe_long_signal',
                'qqe_short_signal',
                'trend_change_bullish',
                'trend_change_bearish'
            ]
        },
        'Pattern': {
            'description': 'Pattern formation alerts',
            'conditions': [
                'bullish_pattern_detected',
                'bearish_pattern_detected',
                'support_level_touched',
                'resistance_level_touched'
            ]
        },
        'Volume': {
            'description': 'Volume alerts',
            'conditions': [
                'volume_surge',
                'volume_above_average',
                'unusual_volume'
            ]
        }
    }
    
    @staticmethod
    def check_price_alerts(df: pd.DataFrame, target_price: float, alert_type: str) -> List[Dict]:
        """Check for price-based alerts"""
        alerts = []
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        current_price = latest['close']
        prev_price = prev['close']
        
        if alert_type == 'price_above' and current_price > target_price:
            alerts.append({
                'type': 'Price Above',
                'message': f"Price is above ${target_price:.2f}",
                'value': current_price,
                'timestamp': latest.name
            })
        
        elif alert_type == 'price_below' and current_price < target_price:
            alerts.append({
                'type': 'Price Below',
                'message': f"Price is below ${target_price:.2f}",
                'value': current_price,
                'timestamp': latest.name
            })
        
        elif alert_type == 'price_crosses_above' and prev_price <= target_price and current_price > target_price:
            alerts.append({
                'type': 'Price Crosses Above',
                'message': f"Price crossed above ${target_price:.2f}",
                'value': current_price,
                'timestamp': latest.name
            })
        
        elif alert_type == 'price_crosses_below' and prev_price >= target_price and current_price < target_price:
            alerts.append({
                'type': 'Price Crosses Below',
                'message': f"Price crossed below ${target_price:.2f}",
                'value': current_price,
                'timestamp': latest.name
            })
        
        return alerts
    
    @staticmethod
    def check_indicator_alerts(df: pd.DataFrame) -> List[Dict]:
        """Check for indicator-based alerts"""
        alerts = []
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        if latest.get('qqe_long', False) and not prev.get('qqe_long', False):
            alerts.append({
                'type': 'QQE Long Signal',
                'message': 'QQE long signal triggered - Bullish momentum',
                'value': latest['close'],
                'timestamp': latest.name
            })
        
        if latest.get('qqe_short', False) and not prev.get('qqe_short', False):
            alerts.append({
                'type': 'QQE Short Signal',
                'message': 'QQE short signal triggered - Bearish momentum',
                'value': latest['close'],
                'timestamp': latest.name
            })
        
        if 'ema_20' in latest and 'ema_50' in latest and 'ema_20' in prev and 'ema_50' in prev:
            if latest['ema_20'] > latest['ema_50'] and prev['ema_20'] <= prev['ema_50']:
                alerts.append({
                    'type': 'EMA Crossover',
                    'message': 'EMA 20 crossed above EMA 50 - Bullish signal',
                    'value': latest['close'],
                    'timestamp': latest.name
                })
            
            if latest['ema_20'] < latest['ema_50'] and prev['ema_20'] >= prev['ema_50']:
                alerts.append({
                    'type': 'EMA Crossunder',
                    'message': 'EMA 20 crossed below EMA 50 - Bearish signal',
                    'value': latest['close'],
                    'timestamp': latest.name
                })
        
        if latest.get('ma_cloud_trend') == 'bullish' and prev.get('ma_cloud_trend') != 'bullish':
            alerts.append({
                'type': 'Trend Change',
                'message': 'Trend changed to BULLISH',
                'value': latest['close'],
                'timestamp': latest.name
            })
        
        if latest.get('ma_cloud_trend') == 'bearish' and prev.get('ma_cloud_trend') != 'bearish':
            alerts.append({
                'type': 'Trend Change',
                'message': 'Trend changed to BEARISH',
                'value': latest['close'],
                'timestamp': latest.name
            })
        
        return alerts
    
    @staticmethod
    def check_pattern_alerts(df: pd.DataFrame, patterns: Dict) -> List[Dict]:
        """Check for pattern formation alerts"""
        alerts = []
        
        if not patterns:
            return alerts
        
        latest = df.iloc[-1]
        
        for pattern_name, pattern_data in patterns.items():
            if pattern_data and 'type' in pattern_data:
                pattern_type = pattern_data['type']
                
                if pattern_type in ['bullish', 'reversal_bullish']:
                    alerts.append({
                        'type': 'Bullish Pattern',
                        'message': f"{pattern_name} detected - Potential bullish move",
                        'value': latest['close'],
                        'timestamp': latest.name
                    })
                
                elif pattern_type in ['bearish', 'reversal_bearish']:
                    alerts.append({
                        'type': 'Bearish Pattern',
                        'message': f"{pattern_name} detected - Potential bearish move",
                        'value': latest['close'],
                        'timestamp': latest.name
                    })
        
        return alerts
    
    @staticmethod
    def check_volume_alerts(df: pd.DataFrame, lookback: int = 20) -> List[Dict]:
        """Check for volume-based alerts"""
        alerts = []
        
        if len(df) < lookback:
            return alerts
        
        latest = df.iloc[-1]
        avg_volume = df['volume'].tail(lookback).mean()
        
        if latest['volume'] > avg_volume * 2:
            alerts.append({
                'type': 'Volume Surge',
                'message': f'Volume is {latest["volume"]/avg_volume:.1f}x above average',
                'value': latest['volume'],
                'timestamp': latest.name
            })
        
        return alerts
    
    @staticmethod
    def check_support_resistance_alerts(df: pd.DataFrame, 
                                       support_levels: List[float],
                                       resistance_levels: List[float],
                                       tolerance: float = 0.5) -> List[Dict]:
        """Check if price is near support/resistance levels"""
        alerts = []
        latest = df.iloc[-1]
        current_price = latest['close']
        
        for level in support_levels:
            distance_pct = abs((current_price - level) / level) * 100
            if distance_pct < tolerance:
                alerts.append({
                    'type': 'Near Support',
                    'message': f'Price near support level ${level:.2f}',
                    'value': current_price,
                    'timestamp': latest.name
                })
        
        for level in resistance_levels:
            distance_pct = abs((current_price - level) / level) * 100
            if distance_pct < tolerance:
                alerts.append({
                    'type': 'Near Resistance',
                    'message': f'Price near resistance level ${level:.2f}',
                    'value': current_price,
                    'timestamp': latest.name
                })
        
        return alerts
    
    @staticmethod
    def check_all_alerts(df: pd.DataFrame, 
                        patterns: Optional[Dict] = None,
                        support_levels: Optional[List[float]] = None,
                        resistance_levels: Optional[List[float]] = None,
                        price_targets: Optional[List[Tuple[float, str]]] = None) -> List[Dict]:
        """Check all types of alerts"""
        all_alerts = []
        
        all_alerts.extend(AlertMonitor.check_indicator_alerts(df))
        
        if patterns:
            all_alerts.extend(AlertMonitor.check_pattern_alerts(df, patterns))
        
        all_alerts.extend(AlertMonitor.check_volume_alerts(df))
        
        if support_levels or resistance_levels:
            all_alerts.extend(AlertMonitor.check_support_resistance_alerts(
                df,
                support_levels or [],
                resistance_levels or []
            ))
        
        if price_targets:
            for price, alert_type in price_targets:
                all_alerts.extend(AlertMonitor.check_price_alerts(df, price, alert_type))
        
        return all_alerts
