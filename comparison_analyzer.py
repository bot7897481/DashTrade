"""
Multi-Stock Comparison and Correlation Analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from scipy.stats import pearsonr
from alpha_vantage_data import fetch_alpha_vantage_data
import yfinance as yf

class ComparisonAnalyzer:
    """Analyze correlations and relative performance across multiple stocks"""
    
    def __init__(self, symbols: List[str], period: str = '3mo', interval: str = '1d', data_source: str = 'yahoo'):
        """
        Initialize comparison analyzer
        
        Args:
            symbols: List of stock symbols to compare
            period: Historical period for comparison
            interval: Data interval
            data_source: 'yahoo' or 'alpha_vantage'
        """
        self.symbols = symbols
        self.period = period
        self.interval = interval
        self.data_source = data_source
        self.price_data = {}
        self.returns_data = {}
    
    def _fetch_yahoo_data(self, symbol: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=self.period, interval=self.interval)
            if df.empty:
                return None
            df.columns = [col.lower() for col in df.columns]
            return df
        except Exception as e:
            print(f"Error fetching {symbol} from Yahoo: {e}")
            return None
    
    def _fetch_alpha_vantage_data(self, symbol: str) -> pd.DataFrame:
        """Fetch data from Alpha Vantage"""
        try:
            df, error = fetch_alpha_vantage_data(symbol, interval=self.interval, period=self.period)
            if error or df is None:
                return None
            return df
        except Exception as e:
            print(f"Error fetching {symbol} from Alpha Vantage: {e}")
            return None
        
    def fetch_all_data(self) -> bool:
        """Fetch data for all symbols using selected data source"""
        try:
            for symbol in self.symbols:
                if self.data_source == 'yahoo':
                    df = self._fetch_yahoo_data(symbol)
                else:
                    df = self._fetch_alpha_vantage_data(symbol)
                
                if df is not None and not df.empty:
                    self.price_data[symbol] = df['close']
                    self.returns_data[symbol] = df['close'].pct_change()
            
            return len(self.price_data) > 0
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix for all stocks"""
        if not self.returns_data:
            return pd.DataFrame()
        
        returns_df = pd.DataFrame(self.returns_data).dropna()
        return returns_df.corr()
    
    def calculate_relative_strength(self, benchmark: str = None) -> Dict[str, float]:
        """
        Calculate relative strength vs benchmark or first symbol
        
        Args:
            benchmark: Symbol to use as benchmark, or None to use first symbol
            
        Returns:
            Dict of relative strength ratios
        """
        if not self.price_data:
            return {}
        
        if benchmark is None:
            benchmark = self.symbols[0]
        
        if benchmark not in self.price_data:
            return {}
        
        benchmark_prices = self.price_data[benchmark]
        relative_strength = {}
        
        for symbol in self.symbols:
            if symbol != benchmark and symbol in self.price_data:
                # Calculate price ratio (normalized to 100 at start)
                ratio = (self.price_data[symbol] / self.price_data[symbol].iloc[0]) / \
                       (benchmark_prices / benchmark_prices.iloc[0])
                
                # Current relative strength
                relative_strength[symbol] = ratio.iloc[-1] * 100
        
        return relative_strength
    
    def get_performance_metrics(self) -> pd.DataFrame:
        """Calculate performance metrics for all stocks"""
        metrics = []
        
        for symbol in self.symbols:
            if symbol not in self.price_data:
                continue
            
            prices = self.price_data[symbol]
            returns = self.returns_data[symbol].dropna()
            
            # Calculate metrics
            total_return = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
            
            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            metrics.append({
                'Symbol': symbol,
                'Total Return (%)': total_return,
                'Volatility (%)': volatility,
                'Sharpe Ratio': sharpe_ratio,
                'Max Drawdown (%)': max_drawdown,
                'Current Price': prices.iloc[-1],
                'Period High': prices.max(),
                'Period Low': prices.min()
            })
        
        return pd.DataFrame(metrics)
    
    def get_normalized_prices(self) -> pd.DataFrame:
        """Get normalized prices (starting at 100) for comparison"""
        normalized = pd.DataFrame()
        
        for symbol in self.symbols:
            if symbol in self.price_data:
                prices = self.price_data[symbol]
                normalized[symbol] = (prices / prices.iloc[0]) * 100
        
        return normalized
    
    def find_correlated_pairs(self, threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """
        Find highly correlated stock pairs
        
        Args:
            threshold: Minimum correlation coefficient (0-1)
            
        Returns:
            List of (symbol1, symbol2, correlation) tuples
        """
        corr_matrix = self.calculate_correlation_matrix()
        
        if corr_matrix.empty:
            return []
        
        pairs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) >= threshold:
                    pairs.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_value
                    ))
        
        # Sort by absolute correlation
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        return pairs
    
    def calculate_beta(self, stock_symbol: str, market_symbol: str) -> float:
        """
        Calculate beta of stock vs market
        
        Args:
            stock_symbol: Stock to calculate beta for
            market_symbol: Market benchmark symbol
            
        Returns:
            Beta value
        """
        if stock_symbol not in self.returns_data or market_symbol not in self.returns_data:
            return 0.0
        
        stock_returns = self.returns_data[stock_symbol].dropna()
        market_returns = self.returns_data[market_symbol].dropna()
        
        # Align the data
        aligned_data = pd.DataFrame({
            'stock': stock_returns,
            'market': market_returns
        }).dropna()
        
        if len(aligned_data) < 2:
            return 0.0
        
        # Beta = Covariance(stock, market) / Variance(market)
        covariance = aligned_data['stock'].cov(aligned_data['market'])
        variance = aligned_data['market'].var()
        
        if variance == 0:
            return 0.0
        
        return covariance / variance
    
    def get_sector_strength_ranking(self) -> pd.DataFrame:
        """Rank stocks by relative strength"""
        if not self.price_data:
            return pd.DataFrame()
        
        rankings = []
        
        for symbol in self.symbols:
            if symbol not in self.price_data:
                continue
            
            prices = self.price_data[symbol]
            returns = self.returns_data[symbol].dropna()
            
            # Calculate various strength metrics
            total_return = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
            recent_return = ((prices.iloc[-1] - prices.iloc[-20]) / prices.iloc[-20]) * 100 if len(prices) >= 20 else 0
            momentum = returns.iloc[-5:].mean() * 100 if len(returns) >= 5 else 0
            
            # Distance from highs
            distance_from_high = ((prices.iloc[-1] - prices.max()) / prices.max()) * 100
            
            # Overall strength score (composite)
            strength_score = (total_return * 0.4 + recent_return * 0.4 + momentum * 0.2)
            
            rankings.append({
                'Symbol': symbol,
                'Strength Score': strength_score,
                'Total Return %': total_return,
                'Recent Return %': recent_return,
                'Momentum': momentum,
                'From High %': distance_from_high
            })
        
        df = pd.DataFrame(rankings)
        
        if not df.empty:
            df = df.sort_values('Strength Score', ascending=False).reset_index(drop=True)
            df['Rank'] = df.index + 1
        
        return df
