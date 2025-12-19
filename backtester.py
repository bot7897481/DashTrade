"""
Backtesting Framework for NovAlgo Trading Strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class Trade:
    """Represents a single trade"""
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    position_type: str = 'long'
    shares: int = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_reason: str = ''
    
    def is_open(self) -> bool:
        """Check if trade is still open"""
        return self.exit_date is None
    
    def pnl(self) -> float:
        """Calculate P&L for the trade"""
        if self.exit_price is None:
            return 0.0
        
        if self.position_type == 'long':
            return (self.exit_price - self.entry_price) * self.shares
        else:
            return (self.entry_price - self.exit_price) * self.shares
    
    def pnl_percent(self) -> float:
        """Calculate P&L percentage"""
        if self.exit_price is None:
            return 0.0
        
        if self.position_type == 'long':
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.exit_price) / self.entry_price) * 100
    
    def duration_days(self) -> int:
        """Calculate trade duration in days"""
        if self.exit_date is None:
            return 0
        return (self.exit_date - self.entry_date).days

@dataclass
class BacktestResults:
    """Results from a backtest"""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    initial_capital: float = 10000.0
    final_capital: float = 10000.0
    
    def total_trades(self) -> int:
        """Total number of trades"""
        return len([t for t in self.trades if not t.is_open()])
    
    def winning_trades(self) -> int:
        """Number of winning trades"""
        return len([t for t in self.trades if not t.is_open() and t.pnl() > 0])
    
    def losing_trades(self) -> int:
        """Number of losing trades"""
        return len([t for t in self.trades if not t.is_open() and t.pnl() < 0])
    
    def win_rate(self) -> float:
        """Win rate percentage"""
        total = self.total_trades()
        if total == 0:
            return 0.0
        return (self.winning_trades() / total) * 100
    
    def total_pnl(self) -> float:
        """Total profit/loss"""
        return sum(t.pnl() for t in self.trades if not t.is_open())
    
    def average_win(self) -> float:
        """Average winning trade P&L"""
        wins = [t.pnl() for t in self.trades if not t.is_open() and t.pnl() > 0]
        return np.mean(wins) if wins else 0.0
    
    def average_loss(self) -> float:
        """Average losing trade P&L"""
        losses = [t.pnl() for t in self.trades if not t.is_open() and t.pnl() < 0]
        return np.mean(losses) if losses else 0.0
    
    def profit_factor(self) -> float:
        """Profit factor (total wins / total losses)"""
        wins = sum(t.pnl() for t in self.trades if not t.is_open() and t.pnl() > 0)
        losses = abs(sum(t.pnl() for t in self.trades if not t.is_open() and t.pnl() < 0))
        return wins / losses if losses > 0 else 0.0
    
    def max_drawdown(self) -> float:
        """Maximum drawdown percentage"""
        if self.equity_curve.empty:
            return 0.0
        
        running_max = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - running_max) / running_max * 100
        return drawdown.min()
    
    def sharpe_ratio(self) -> float:
        """Sharpe ratio (annualized)"""
        if self.equity_curve.empty or len(self.equity_curve) < 2:
            return 0.0
        
        returns = self.equity_curve.pct_change().dropna()
        if returns.std() == 0:
            return 0.0
        
        return (returns.mean() / returns.std()) * np.sqrt(252)
    
    def average_trade_duration(self) -> float:
        """Average trade duration in days"""
        durations = [t.duration_days() for t in self.trades if not t.is_open()]
        return np.mean(durations) if durations else 0.0

class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, 
                 df: pd.DataFrame,
                 initial_capital: float = 10000.0,
                 position_size_pct: float = 10.0,
                 strategy_mode: str = 'long_only',
                 use_trend_filter: bool = False,
                 trend_ema_period: int = 200,
                 use_stop_loss: bool = True,
                 stop_loss_pct: float = 2.0,
                 use_take_profit: bool = False,
                 take_profit_pct: float = 5.0):
        """
        Initialize backtester
        
        Args:
            df: DataFrame with OHLCV data and signals
            initial_capital: Starting capital
            position_size_pct: Percentage of capital per trade
            strategy_mode: 'long_only', 'long_short', or 'short_only'
            use_trend_filter: Filter signals by trend (200 EMA)
            trend_ema_period: EMA period for trend filter (default 200)
            use_stop_loss: Whether to use stop losses
            stop_loss_pct: Stop loss percentage
            use_take_profit: Whether to use take profit
            take_profit_pct: Take profit percentage
        """
        self.df = df.copy()
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.strategy_mode = strategy_mode
        self.use_trend_filter = use_trend_filter
        self.trend_ema_period = trend_ema_period
        self.use_stop_loss = use_stop_loss
        self.stop_loss_pct = stop_loss_pct
        self.use_take_profit = use_take_profit
        self.take_profit_pct = take_profit_pct
        
        self.capital = initial_capital
        self.equity = initial_capital
        self.trades: List[Trade] = []
        self.open_trades: List[Trade] = []
        self.equity_curve: List[float] = []

        if self.use_trend_filter:
            self.df['ema_trend'] = self.df['close'].ewm(span=self.trend_ema_period, adjust=False).mean()
    
    def calculate_position_size(self, price: float) -> int:
        """Calculate position size in shares"""
        position_value = self.capital * (self.position_size_pct / 100)
        shares = int(position_value / price)
        return max(1, shares)
    
    def enter_long(self, date: datetime, price: float) -> Trade:
        """Enter a long position"""
        shares = self.calculate_position_size(price)
        cost = shares * price
        
        if cost > self.capital:
            return None
        
        stop_loss = price * (1 - self.stop_loss_pct / 100) if self.use_stop_loss else None
        take_profit = price * (1 + self.take_profit_pct / 100) if self.use_take_profit else None
        
        trade = Trade(
            entry_date=date,
            entry_price=price,
            position_type='long',
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.capital -= cost
        self.open_trades.append(trade)
        self.trades.append(trade)
        
        return trade
    
    def enter_short(self, date: datetime, price: float) -> Trade:
        """Enter a short position"""
        shares = self.calculate_position_size(price)
        
        # Calculate margin requirement (50% of position value)
        margin_required = shares * price * 0.5
        
        if margin_required > self.capital:
            return None  # Insufficient capital
        
        # Deduct margin from available capital
        self.capital -= margin_required
        
        stop_loss = price * (1 + self.stop_loss_pct / 100) if self.use_stop_loss else None
        take_profit = price * (1 - self.take_profit_pct / 100) if self.use_take_profit else None
        
        trade = Trade(
            entry_date=date,
            entry_price=price,
            position_type='short',
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.open_trades.append(trade)
        self.trades.append(trade)
        
        return trade
    
    def exit_trade(self, trade: Trade, date: datetime, price: float, reason: str = 'signal'):
        """Exit a trade"""
        trade.exit_date = date
        trade.exit_price = price
        trade.exit_reason = reason
        
        if trade.position_type == 'long':
            self.capital += trade.shares * price
        else:  # short position
            # Return margin + P&L
            margin = trade.shares * trade.entry_price * 0.5
            self.capital += margin + trade.pnl()
        
        if trade in self.open_trades:
            self.open_trades.remove(trade)
    
    def check_stop_loss_take_profit(self, date: datetime, low: float, high: float):
        """Check if any open trades hit stop loss or take profit"""
        trades_to_exit = []
        
        for trade in list(self.open_trades): # Iterate over a copy to allow modification
            if trade.position_type == 'long':
                if trade.stop_loss and low <= trade.stop_loss:
                    trades_to_exit.append((trade, trade.stop_loss, 'stop_loss'))
                elif trade.take_profit and high >= trade.take_profit:
                    trades_to_exit.append((trade, trade.take_profit, 'take_profit'))
            else:
                if trade.stop_loss and high >= trade.stop_loss:
                    trades_to_exit.append((trade, trade.stop_loss, 'stop_loss'))
                elif trade.take_profit and low <= trade.take_profit:
                    trades_to_exit.append((trade, trade.take_profit, 'take_profit'))
        
        for trade, price, reason in trades_to_exit:
            self.exit_trade(trade, date, price, reason)
    
    def calculate_equity(self, current_price: float) -> float:
        """Calculate current total equity"""
        equity = self.capital
        
        for trade in self.open_trades:
            if trade.position_type == 'long':
                equity += trade.shares * current_price
            else:
                # For short: Equity = Free Capital + Margin + P&L
                # P&L = (Entry - Current) * Shares
                # current code: equity += (Entry - Current) * Shares
                # But it missed adding back the Margin that was deducted from self.capital
                margin = trade.shares * trade.entry_price * 0.5
                pnl = (trade.entry_price - current_price) * trade.shares
                equity += margin + pnl
        
        return equity
    
    def validate_signal_with_trend(self, row, signal_type: str) -> bool:
        """
        Validate if signal aligns with trend filter
        
        Args:
            row: DataFrame row with price data
            signal_type: 'long' or 'short'
            
        Returns:
            bool: True if signal is valid (or no filter), False otherwise
        """
        if not self.use_trend_filter:
            return True  # No filter, all signals valid
        
        if 'ema_trend' not in row:
            return True  # No trend data, allow signal
        
        price = row['close']
        trend_ema = row['ema_trend']
        
        if signal_type == 'long':
            return price > trend_ema  # Only long in uptrend
        elif signal_type == 'short':
            return price < trend_ema  # Only short in downtrend
        
        return True
    
    def run_simple_strategy(self, 
                           long_signal_col: str = 'qqe_long',
                           short_signal_col: str = 'qqe_short',
                           exit_on_opposite: bool = True) -> BacktestResults:
        """
        Run backtest with simple long/short signals
        
        Args:
            long_signal_col: Column name for long entry signals
            short_signal_col: Column name for short entry signals
            exit_on_opposite: Exit on opposite signal
            
        Returns:
            BacktestResults object
        """
        for idx, row in self.df.iterrows():
            date = idx
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            self.check_stop_loss_take_profit(date, low_price, high_price)
            
            has_long_signal = row.get(long_signal_col, False)
            has_short_signal = row.get(short_signal_col, False)
            
            # Validate signals with trend filter
            long_signal_valid = has_long_signal and self.validate_signal_with_trend(row, 'long')
            short_signal_valid = has_short_signal and self.validate_signal_with_trend(row, 'short')
            
            # STRATEGY MODE LOGIC
            if self.strategy_mode == 'long_only':
                # Long-only mode: enter on long signals, exit on short signals (don't actually short)
                if short_signal_valid and self.open_trades:
                    # Exit long positions on short signal
                    for trade in list(self.open_trades):
                        if trade.position_type == 'long':
                            self.exit_trade(trade, date, close_price, 'long_only_exit')
                
                if long_signal_valid and len(self.open_trades) == 0:
                    self.enter_long(date, close_price)
            
            elif self.strategy_mode == 'short_only':
                # Short-only mode: enter on short signals, exit on long signals (don't actually long)
                if long_signal_valid and self.open_trades:
                    # Exit short positions on long signal
                    for trade in list(self.open_trades):
                        if trade.position_type == 'short':
                            self.exit_trade(trade, date, close_price, 'short_only_exit')
                
                if short_signal_valid and len(self.open_trades) == 0:
                    self.enter_short(date, close_price)
            
            else:  # long_short mode
                # Original behavior: both long and short positions
                if exit_on_opposite:
                    if long_signal_valid and self.open_trades:
                        # Exit any short positions
                        for trade in list(self.open_trades):
                            if trade.position_type == 'short':
                                self.exit_trade(trade, date, close_price, 'opposite_signal')
                    
                    elif short_signal_valid and self.open_trades:
                        # Exit any long positions
                        for trade in list(self.open_trades):
                            if trade.position_type == 'long':
                                self.exit_trade(trade, date, close_price, 'opposite_signal')
                
                # Enter new positions if no trades are open
                if long_signal_valid and len(self.open_trades) == 0:
                    self.enter_long(date, close_price)
                
                elif short_signal_valid and len(self.open_trades) == 0:
                    self.enter_short(date, close_price)
            
            self.equity = self.calculate_equity(close_price)
            self.equity_curve.append(self.equity)
        
        for trade in list(self.open_trades):
            last_date = self.df.index[-1]
            last_price = self.df.iloc[-1]['close']
            self.exit_trade(trade, last_date, last_price, 'end_of_data')
        
        results = BacktestResults(
            trades=self.trades,
            equity_curve=pd.Series(self.equity_curve, index=self.df.index),
            initial_capital=self.initial_capital,
            final_capital=self.equity
        )
        
        return results
    
    def run_custom_strategy(self, 
                           entry_conditions: Callable,
                           exit_conditions: Callable) -> BacktestResults:
        """
        Run backtest with custom entry/exit conditions
        
        Args:
            entry_conditions: Function that takes row and returns ('long', 'short', or None)
            exit_conditions: Function that takes row and trade, returns True to exit
            
        Returns:
            BacktestResults object
        """
        for idx, row in self.df.iterrows():
            date = idx
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            self.check_stop_loss_take_profit(date, low_price, high_price)
            
            signal = entry_conditions(row)
            
            if signal == 'long' and len(self.open_trades) == 0:
                self.enter_long(date, close_price)
            elif signal == 'short' and len(self.open_trades) == 0:
                self.enter_short(date, close_price)
            
            for trade in list(self.open_trades):
                if exit_conditions(row, trade):
                    self.exit_trade(trade, date, close_price, 'custom_exit')
            
            self.equity = self.calculate_equity(close_price)
            self.equity_curve.append(self.equity)
        
        for trade in list(self.open_trades):
            last_date = self.df.index[-1]
            last_price = self.df.iloc[-1]['close']
            self.exit_trade(trade, last_date, last_price, 'end_of_data')
        
        results = BacktestResults(
            trades=self.trades,
            equity_curve=pd.Series(self.equity_curve, index=self.df.index),
            initial_capital=self.initial_capital,
            final_capital=self.equity
        )
        
        return results
