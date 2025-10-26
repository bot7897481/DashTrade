"""
Custom Strategy Builder for NovAlgo Trading Dashboard
Allows users to create custom strategies by combining indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

@dataclass
class StrategyCondition:
    """Represents a single condition in a strategy"""
    indicator: str
    operator: str
    value: Any
    indicator2: Optional[str] = None
    
    def evaluate(self, row: pd.Series) -> bool:
        """Evaluate the condition on a data row"""
        try:
            if self.indicator2:
                val1 = row.get(self.indicator)
                val2 = row.get(self.indicator2)
                
                if val1 is None or val2 is None:
                    return False
                
                if self.operator == '>':
                    return val1 > val2
                elif self.operator == '<':
                    return val1 < val2
                elif self.operator == '>=':
                    return val1 >= val2
                elif self.operator == '<=':
                    return val1 <= val2
                elif self.operator == '==':
                    return val1 == val2
                elif self.operator == '!=':
                    return val1 != val2
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
                elif self.operator == '!=':
                    if isinstance(self.value, str):
                        return str(val) != self.value
                    return val != self.value
            
            return False
        except:
            return False

@dataclass
class CustomStrategy:
    """Custom trading strategy with multiple conditions"""
    name: str
    long_conditions: List[StrategyCondition] = field(default_factory=list)
    short_conditions: List[StrategyCondition] = field(default_factory=list)
    exit_conditions: List[StrategyCondition] = field(default_factory=list)
    long_logic: str = 'AND'
    short_logic: str = 'AND'
    exit_logic: str = 'OR'
    
    def should_enter_long(self, row: pd.Series) -> bool:
        """Check if long entry conditions are met"""
        if not self.long_conditions:
            return False
        
        results = [cond.evaluate(row) for cond in self.long_conditions]
        
        if self.long_logic == 'AND':
            return all(results)
        else:
            return any(results)
    
    def should_enter_short(self, row: pd.Series) -> bool:
        """Check if short entry conditions are met"""
        if not self.short_conditions:
            return False
        
        results = [cond.evaluate(row) for cond in self.short_conditions]
        
        if self.short_logic == 'AND':
            return all(results)
        else:
            return any(results)
    
    def should_exit(self, row: pd.Series) -> bool:
        """Check if exit conditions are met"""
        if not self.exit_conditions:
            return False
        
        results = [cond.evaluate(row) for cond in self.exit_conditions]
        
        if self.exit_logic == 'AND':
            return all(results)
        else:
            return any(results)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals for the entire dataset"""
        df = df.copy()
        
        df['custom_long'] = df.apply(self.should_enter_long, axis=1)
        df['custom_short'] = df.apply(self.should_enter_short, axis=1)
        df['custom_exit'] = df.apply(self.should_exit, axis=1)
        
        return df
    
    def to_dict(self) -> Dict:
        """Convert strategy to dictionary for storage"""
        return {
            'name': self.name,
            'long_conditions': [
                {
                    'indicator': c.indicator,
                    'operator': c.operator,
                    'value': c.value,
                    'indicator2': c.indicator2
                } for c in self.long_conditions
            ],
            'short_conditions': [
                {
                    'indicator': c.indicator,
                    'operator': c.operator,
                    'value': c.value,
                    'indicator2': c.indicator2
                } for c in self.short_conditions
            ],
            'exit_conditions': [
                {
                    'indicator': c.indicator,
                    'operator': c.operator,
                    'value': c.value,
                    'indicator2': c.indicator2
                } for c in self.exit_conditions
            ],
            'long_logic': self.long_logic,
            'short_logic': self.short_logic,
            'exit_logic': self.exit_logic
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomStrategy':
        """Create strategy from dictionary"""
        long_conditions = [
            StrategyCondition(**c) for c in data.get('long_conditions', [])
        ]
        short_conditions = [
            StrategyCondition(**c) for c in data.get('short_conditions', [])
        ]
        exit_conditions = [
            StrategyCondition(**c) for c in data.get('exit_conditions', [])
        ]
        
        return cls(
            name=data['name'],
            long_conditions=long_conditions,
            short_conditions=short_conditions,
            exit_conditions=exit_conditions,
            long_logic=data.get('long_logic', 'AND'),
            short_logic=data.get('short_logic', 'AND'),
            exit_logic=data.get('exit_logic', 'OR')
        )

class StrategyTemplates:
    """Pre-built strategy templates"""
    
    @staticmethod
    def momentum_breakout() -> CustomStrategy:
        """Momentum breakout strategy"""
        return CustomStrategy(
            name="Momentum Breakout",
            long_conditions=[
                StrategyCondition('qqe_long', '==', True),
                StrategyCondition('close', '>', None, 'ema_20'),
                StrategyCondition('ma_cloud_trend', '==', 'bullish')
            ],
            short_conditions=[
                StrategyCondition('qqe_short', '==', True)
            ],
            exit_conditions=[
                StrategyCondition('close', '<', None, 'ema_50')
            ],
            long_logic='AND',
            short_logic='AND',
            exit_logic='OR'
        )
    
    @staticmethod
    def trend_following() -> CustomStrategy:
        """Trend following strategy"""
        return CustomStrategy(
            name="Trend Following",
            long_conditions=[
                StrategyCondition('ema_20', '>', None, 'ema_50'),
                StrategyCondition('ema_50', '>', None, 'ema_100'),
                StrategyCondition('ma_cloud_trend', '==', 'bullish')
            ],
            exit_conditions=[
                StrategyCondition('ema_20', '<', None, 'ema_50')
            ],
            long_logic='AND',
            exit_logic='OR'
        )
    
    @staticmethod
    def mean_reversion() -> CustomStrategy:
        """Mean reversion strategy"""
        return CustomStrategy(
            name="Mean Reversion",
            long_conditions=[
                StrategyCondition('close', '<', None, 'vwap'),
                StrategyCondition('qqe_long', '==', True)
            ],
            exit_conditions=[
                StrategyCondition('close', '>', None, 'vwap')
            ],
            long_logic='AND',
            exit_logic='OR'
        )
    
    @staticmethod
    def get_all_templates() -> List[CustomStrategy]:
        """Get all available templates"""
        return [
            StrategyTemplates.momentum_breakout(),
            StrategyTemplates.trend_following(),
            StrategyTemplates.mean_reversion()
        ]

class StrategyBuilder:
    """Helper class for building custom strategies"""
    
    AVAILABLE_INDICATORS = {
        'Price': ['close', 'open', 'high', 'low'],
        'EMAs': ['ema_9', 'ema_20', 'ema_50', 'ema_100', 'ema_200'],
        'QQE': ['qqe_long', 'qqe_short'],
        'Trend': ['ma_cloud_trend'],
        'VWAP': ['vwap', 'vwap_upper', 'vwap_lower'],
        'Volume': ['volume']
    }
    
    OPERATORS = {
        'Comparison': ['>', '<', '>=', '<=', '==', '!='],
        'Boolean': ['==']
    }
    
    @staticmethod
    def get_indicator_list() -> List[str]:
        """Get flat list of all indicators"""
        indicators = []
        for category, inds in StrategyBuilder.AVAILABLE_INDICATORS.items():
            indicators.extend(inds)
        return sorted(indicators)
    
    @staticmethod
    def get_indicator_type(indicator: str) -> str:
        """Get the type of an indicator (numeric or boolean)"""
        boolean_indicators = ['qqe_long', 'qqe_short']
        string_indicators = ['ma_cloud_trend']
        
        if indicator in boolean_indicators:
            return 'boolean'
        elif indicator in string_indicators:
            return 'string'
        else:
            return 'numeric'
    
    @staticmethod
    def validate_condition(condition: StrategyCondition) -> Tuple[bool, str]:
        """Validate a strategy condition"""
        available = StrategyBuilder.get_indicator_list()
        
        if condition.indicator not in available:
            return False, f"Invalid indicator: {condition.indicator}"
        
        if condition.indicator2 and condition.indicator2 not in available:
            return False, f"Invalid indicator: {condition.indicator2}"
        
        return True, "Valid"
