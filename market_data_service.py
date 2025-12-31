"""
Market Data Service for DashTrade
Fetches comprehensive market data from Yahoo Finance for trade context
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
import time

logger = logging.getLogger(__name__)

# Sector mapping for stocks (common stocks to their sector ETFs)
SECTOR_ETFS = {
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLV': 'Healthcare',
    'XLY': 'Consumer Discretionary',
    'XLP': 'Consumer Staples',
    'XLI': 'Industrials',
    'XLB': 'Materials',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate',
    'XLC': 'Communication Services'
}

# Market indices symbols
MARKET_INDICES = {
    'sp500': '^GSPC',
    'nasdaq': '^IXIC',
    'dji': '^DJI',
    'russell': '^RUT',
    'vix': '^VIX'
}

# Treasury yield symbols
TREASURY_SYMBOLS = {
    '10y': '^TNX',
    '2y': '^TWO'
}


class MarketDataService:
    """Fetch market data from Yahoo Finance"""

    @staticmethod
    def get_stock_data(symbol: str) -> Dict:
        """
        Get comprehensive stock data including fundamentals and technicals

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict with stock data
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current day's data
            hist = ticker.history(period='1d')
            if hist.empty:
                hist = ticker.history(period='5d')  # Fallback to 5 days

            # Get 52-week data for range
            hist_52w = ticker.history(period='1y')

            # Calculate average volume (20-day)
            hist_20d = ticker.history(period='1mo')
            avg_volume = hist_20d['Volume'].mean() if not hist_20d.empty else None

            current_volume = hist['Volume'].iloc[-1] if not hist.empty else None
            volume_ratio = (current_volume / avg_volume) if current_volume and avg_volume else None

            return {
                # Current day OHLCV
                'stock_open': float(hist['Open'].iloc[-1]) if not hist.empty else None,
                'stock_high': float(hist['High'].iloc[-1]) if not hist.empty else None,
                'stock_low': float(hist['Low'].iloc[-1]) if not hist.empty else None,
                'stock_close': float(hist['Close'].iloc[-1]) if not hist.empty else None,
                'stock_volume': int(current_volume) if current_volume else None,
                'stock_prev_close': info.get('previousClose'),
                'stock_change_percent': info.get('regularMarketChangePercent'),

                # Volume context
                'stock_avg_volume': int(avg_volume) if avg_volume else None,
                'stock_volume_ratio': float(volume_ratio) if volume_ratio else None,

                # Fundamentals
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'eps': info.get('trailingEps'),
                'beta': info.get('beta'),
                'dividend_yield': info.get('dividendYield'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'short_ratio': info.get('shortRatio'),

                # 52-week range
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),

                # Moving averages
                'fifty_day_ma': info.get('fiftyDayAverage'),
                'two_hundred_day_ma': info.get('twoHundredDayAverage'),

                # Calculated technical levels
                'price_vs_50ma_percent': MarketDataService._calc_percent_diff(
                    hist['Close'].iloc[-1] if not hist.empty else None,
                    info.get('fiftyDayAverage')
                ),
                'price_vs_200ma_percent': MarketDataService._calc_percent_diff(
                    hist['Close'].iloc[-1] if not hist.empty else None,
                    info.get('twoHundredDayAverage')
                ),
                'price_vs_52w_high_percent': MarketDataService._calc_percent_diff(
                    hist['Close'].iloc[-1] if not hist.empty else None,
                    info.get('fiftyTwoWeekHigh')
                ),
                'price_vs_52w_low_percent': MarketDataService._calc_percent_diff(
                    hist['Close'].iloc[-1] if not hist.empty else None,
                    info.get('fiftyTwoWeekLow')
                ),

                # Sector
                'sector': info.get('sector'),
                'industry': info.get('industry'),
            }

        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return {'error': str(e)}

    @staticmethod
    def get_market_indices() -> Dict:
        """
        Get current market index values

        Returns:
            Dict with index prices and changes
        """
        result = {}

        try:
            for name, symbol in MARKET_INDICES.items():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info

                    result[f'{name}_price'] = info.get('regularMarketPrice')
                    result[f'{name}_change_percent'] = info.get('regularMarketChangePercent')
                except Exception as e:
                    logger.warning(f"Error fetching {name} ({symbol}): {e}")
                    result[f'{name}_price'] = None
                    result[f'{name}_change_percent'] = None

        except Exception as e:
            logger.error(f"Error fetching market indices: {e}")

        return result

    @staticmethod
    def get_treasury_yields() -> Dict:
        """
        Get treasury yield data

        Returns:
            Dict with treasury yields
        """
        result = {}

        try:
            # 10-year treasury
            tnx = yf.Ticker('^TNX')
            tnx_info = tnx.info
            result['treasury_10y_yield'] = tnx_info.get('regularMarketPrice')

            # 2-year treasury (using different approach - might not be available)
            try:
                twoy = yf.Ticker('^IRX')  # 13-week T-bill rate as proxy
                twoy_info = twoy.info
                result['treasury_2y_yield'] = twoy_info.get('regularMarketPrice')
            except:
                result['treasury_2y_yield'] = None

            # Calculate yield curve spread
            if result.get('treasury_10y_yield') and result.get('treasury_2y_yield'):
                result['yield_curve_spread'] = result['treasury_10y_yield'] - result['treasury_2y_yield']
            else:
                result['yield_curve_spread'] = None

        except Exception as e:
            logger.error(f"Error fetching treasury yields: {e}")

        return result

    @staticmethod
    def get_sector_etfs() -> Dict:
        """
        Get all sector ETF prices

        Returns:
            Dict with sector ETF prices
        """
        result = {}

        for etf_symbol in SECTOR_ETFS.keys():
            try:
                ticker = yf.Ticker(etf_symbol)
                info = ticker.info
                result[f'{etf_symbol.lower()}_price'] = info.get('regularMarketPrice')
            except Exception as e:
                logger.warning(f"Error fetching {etf_symbol}: {e}")
                result[f'{etf_symbol.lower()}_price'] = None

        return result

    @staticmethod
    def get_stock_sector_etf(symbol: str) -> Dict:
        """
        Get the sector ETF that corresponds to a stock

        Args:
            symbol: Stock ticker

        Returns:
            Dict with sector ETF info
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            sector = info.get('sector', '')

            # Map sector to ETF
            sector_to_etf = {
                'Technology': 'XLK',
                'Financial Services': 'XLF',
                'Financials': 'XLF',
                'Energy': 'XLE',
                'Healthcare': 'XLV',
                'Consumer Cyclical': 'XLY',
                'Consumer Discretionary': 'XLY',
                'Consumer Defensive': 'XLP',
                'Consumer Staples': 'XLP',
                'Industrials': 'XLI',
                'Basic Materials': 'XLB',
                'Materials': 'XLB',
                'Utilities': 'XLU',
                'Real Estate': 'XLRE',
                'Communication Services': 'XLC'
            }

            etf_symbol = sector_to_etf.get(sector, 'SPY')  # Default to SPY

            # Get ETF data
            etf_ticker = yf.Ticker(etf_symbol)
            etf_info = etf_ticker.info

            return {
                'sector_etf_symbol': etf_symbol,
                'sector_etf_price': etf_info.get('regularMarketPrice'),
                'sector_etf_change_percent': etf_info.get('regularMarketChangePercent')
            }

        except Exception as e:
            logger.error(f"Error getting sector ETF for {symbol}: {e}")
            return {
                'sector_etf_symbol': None,
                'sector_etf_price': None,
                'sector_etf_change_percent': None
            }

    @staticmethod
    def calculate_rsi(symbol: str, period: int = 14) -> Optional[float]:
        """
        Calculate RSI for a stock

        Args:
            symbol: Stock ticker
            period: RSI period (default 14)

        Returns:
            RSI value or None
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')

            if len(hist) < period + 1:
                return None

            # Calculate price changes
            delta = hist['Close'].diff()

            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = (-delta).where(delta < 0, 0)

            # Calculate average gains and losses
            avg_gain = gains.rolling(window=period).mean()
            avg_loss = losses.rolling(window=period).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1]) if not rsi.empty else None

        except Exception as e:
            logger.error(f"Error calculating RSI for {symbol}: {e}")
            return None

    @staticmethod
    def get_complete_market_context(symbol: str, alpaca_account: Dict = None,
                                     alpaca_position: Dict = None,
                                     alpaca_positions: List = None) -> Dict:
        """
        Get complete market context for a trade

        Args:
            symbol: Stock being traded
            alpaca_account: Account info from Alpaca API
            alpaca_position: Current position info from Alpaca
            alpaca_positions: All positions from Alpaca

        Returns:
            Complete market context dict ready to store in database
        """
        start_time = time.time()
        errors = []
        context = {}

        try:
            # 1. Stock-specific data
            stock_data = MarketDataService.get_stock_data(symbol)
            if 'error' in stock_data:
                errors.append(f"Stock data: {stock_data['error']}")
            else:
                context.update(stock_data)

            # 2. Market indices
            indices = MarketDataService.get_market_indices()
            context.update(indices)

            # 3. Treasury yields
            yields = MarketDataService.get_treasury_yields()
            context.update(yields)

            # 4. Sector ETF for this stock
            sector_etf = MarketDataService.get_stock_sector_etf(symbol)
            context.update(sector_etf)

            # 5. All sector ETFs
            sector_etfs = MarketDataService.get_sector_etfs()
            context.update(sector_etfs)

            # 6. RSI
            rsi = MarketDataService.calculate_rsi(symbol)
            context['rsi_14'] = rsi

            # 7. Account context (from Alpaca)
            if alpaca_account:
                context['account_equity'] = alpaca_account.get('equity')
                context['account_cash'] = alpaca_account.get('cash')
                context['account_buying_power'] = alpaca_account.get('buying_power')
                context['account_portfolio_value'] = alpaca_account.get('portfolio_value')

            # 8. Position context (from Alpaca)
            if alpaca_position:
                context['position_qty_before'] = alpaca_position.get('qty')
                context['position_value_before'] = alpaca_position.get('market_value')
                context['position_avg_entry'] = alpaca_position.get('entry_price')
                context['position_unrealized_pl'] = alpaca_position.get('unrealized_pl')

            # 9. Total positions context
            if alpaca_positions:
                context['total_positions_count'] = len(alpaca_positions)
                context['total_positions_value'] = sum(
                    float(p.get('market_value', 0)) for p in alpaca_positions
                )

            # Metadata
            context['captured_at'] = datetime.utcnow()
            context['data_source'] = 'yfinance'
            context['fetch_latency_ms'] = int((time.time() - start_time) * 1000)
            context['errors'] = '; '.join(errors) if errors else None

        except Exception as e:
            logger.error(f"Error getting complete market context: {e}")
            context['errors'] = str(e)

        return context

    @staticmethod
    def _calc_percent_diff(current: float, reference: float) -> Optional[float]:
        """Calculate percentage difference"""
        if current is None or reference is None or reference == 0:
            return None
        return ((current - reference) / reference) * 100


# Quick test
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("Testing Market Data Service...")
    print("\n1. Stock Data (AAPL):")
    stock = MarketDataService.get_stock_data('AAPL')
    for k, v in stock.items():
        print(f"  {k}: {v}")

    print("\n2. Market Indices:")
    indices = MarketDataService.get_market_indices()
    for k, v in indices.items():
        print(f"  {k}: {v}")

    print("\n3. VIX:")
    print(f"  VIX: {indices.get('vix_price')}")

    print("\n4. Sector ETF for AAPL:")
    sector = MarketDataService.get_stock_sector_etf('AAPL')
    for k, v in sector.items():
        print(f"  {k}: {v}")

    print("\n5. RSI(14) for AAPL:")
    rsi = MarketDataService.calculate_rsi('AAPL')
    print(f"  RSI: {rsi}")
