"""
Pine Script Signal Monitor
Implements NovAlgo - Fast Signals indicator from TradingView
Provides real-time monitoring and notifications for QQE signals
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from notification_handler import NotificationHandler


class PineScriptMonitor:
    """Monitor and detect signals based on NovAlgo Fast Signals Pine Script"""

    def __init__(self, symbol: str, interval: str = '1h'):
        """
        Initialize Pine Script Monitor

        Args:
            symbol: Stock symbol to monitor
            interval: Data interval (1m, 5m, 15m, 1h, 1d, etc.)
        """
        self.symbol = symbol
        self.interval = interval
        self.df = None

        # Default Pine Script parameters matching TradingView script
        self.params = {
            # QQE Parameters (optimized for faster signals)
            'rsi_period': 8,
            'rsi_smooth_period': 3,
            'qqe_factor': 3.2,

            # EMA Parameters
            'ema1_period': 20,
            'ema2_period': 50,
            'ema3_period': 100,
            'ema4_period': 200,
            'ema5_period': 9,

            # MA Cloud Parameters
            'ma_cloud_short': 4,
            'ma_cloud_long': 20,
            'ma_cloud_sma': 20,

            # VWAP Parameters
            'vwap_anchor': 'Session',  # Session, Week, Month, Quarter, Year
            'vwap_stdev_mult1': 1.0,
            'vwap_stdev_mult2': 2.0,
            'vwap_stdev_mult3': 3.0,
        }

        self.signals = []
        self.last_signal = None
        self.monitoring_enabled = False

        # Notification handler
        self.notifier = NotificationHandler()
        self.notification_settings = {
            'webhook_enabled': False,
            'email_enabled': False,
            'notify_on_long': True,
            'notify_on_short': True
        }

    def update_parameters(self, params: Dict):
        """Update Pine Script parameters"""
        self.params.update(params)

    def configure_notifications(self, webhook_url: str = None, email_config: Dict = None,
                                notify_on_long: bool = True, notify_on_short: bool = True):
        """
        Configure notification settings

        Args:
            webhook_url: Webhook URL for notifications
            email_config: Dictionary with email configuration
            notify_on_long: Enable notifications for LONG signals
            notify_on_short: Enable notifications for SHORT signals
        """
        if webhook_url:
            self.notifier.configure_webhook(webhook_url)
            self.notification_settings['webhook_enabled'] = True

        if email_config:
            self.notifier.configure_email(
                smtp_server=email_config.get('smtp_server'),
                smtp_port=email_config.get('smtp_port'),
                sender_email=email_config.get('sender_email'),
                sender_password=email_config.get('sender_password'),
                recipient_emails=email_config.get('recipient_emails', [])
            )
            self.notification_settings['email_enabled'] = True

        self.notification_settings['notify_on_long'] = notify_on_long
        self.notification_settings['notify_on_short'] = notify_on_short

    def send_signal_notification(self, signal: Dict) -> Dict:
        """
        Send notifications for a detected signal

        Args:
            signal: Signal dictionary with type, price, timestamp, etc.

        Returns:
            Dictionary with notification results
        """
        # Check if we should notify for this signal type
        if signal['type'] == 'LONG' and not self.notification_settings['notify_on_long']:
            return {'skipped': True, 'reason': 'LONG notifications disabled'}

        if signal['type'] == 'SHORT' and not self.notification_settings['notify_on_short']:
            return {'skipped': True, 'reason': 'SHORT notifications disabled'}

        # Prepare signal data for notification
        signal_data = {
            'symbol': self.symbol,
            'type': signal['type'],
            'price': signal['price'],
            'volume': signal.get('volume', 0),
            'rsi': signal.get('rsi', 0),
            'trend': signal.get('trend', 'unknown'),
            'timestamp': signal['timestamp']
        }

        # Send notifications
        return self.notifier.notify_signal(
            signal_data,
            send_webhook=self.notification_settings['webhook_enabled'],
            send_email=self.notification_settings['email_enabled']
        )

    def fetch_data(self, period: str = '5d') -> pd.DataFrame:
        """
        Fetch market data for the symbol

        Args:
            period: Data period (1d, 5d, 1mo, 3mo, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period=period, interval=self.interval)

            if df.empty:
                raise ValueError(f"No data returned for {self.symbol}")

            self.df = df
            return df
        except Exception as e:
            raise Exception(f"Error fetching data for {self.symbol}: {str(e)}")

    def calculate_qqe(self) -> pd.DataFrame:
        """
        Calculate QQE (Quantified Qualitative Estimation) signals
        Implements the exact logic from the Pine Script

        Returns:
            DataFrame with QQE calculations and signals
        """
        if self.df is None or self.df.empty:
            raise ValueError("No data available. Call fetch_data() first.")

        df = self.df.copy()

        # Parameters
        rsi_period = self.params['rsi_period']
        rsi_smooth_period = self.params['rsi_smooth_period']
        qqe_factor = self.params['qqe_factor']
        wilders_period = rsi_period * 2 - 1

        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        avg_gain = gain.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(alpha=1/rsi_period, min_periods=rsi_period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['rsi'] = rsi

        # Smooth RSI
        rsi_ma = rsi.ewm(span=rsi_smooth_period, adjust=False).mean()
        df['rsi_ma'] = rsi_ma

        # Calculate ATR of RSI
        atr_rsi = abs(rsi_ma - rsi_ma.shift(1))
        ma_atr_rsi = atr_rsi.ewm(span=wilders_period, adjust=False).mean()

        # Calculate QQE bands
        delta_fast_atr_rsi = ma_atr_rsi.ewm(span=wilders_period, adjust=False).mean() * qqe_factor
        df['delta_fast_atr_rsi'] = delta_fast_atr_rsi

        # Initialize bands
        long_band = pd.Series(index=df.index, dtype=float)
        short_band = pd.Series(index=df.index, dtype=float)
        trend = pd.Series(index=df.index, dtype=float)

        # Calculate bands iteratively (matching Pine Script logic)
        for i in range(len(df)):
            if i == 0:
                long_band.iloc[i] = rsi_ma.iloc[i] - delta_fast_atr_rsi.iloc[i]
                short_band.iloc[i] = rsi_ma.iloc[i] + delta_fast_atr_rsi.iloc[i]
                trend.iloc[i] = 1
            else:
                new_long_band = rsi_ma.iloc[i] - delta_fast_atr_rsi.iloc[i]
                new_short_band = rsi_ma.iloc[i] + delta_fast_atr_rsi.iloc[i]

                # Long band logic
                if rsi_ma.iloc[i-1] > long_band.iloc[i-1] and rsi_ma.iloc[i] > long_band.iloc[i-1]:
                    long_band.iloc[i] = max(long_band.iloc[i-1], new_long_band)
                else:
                    long_band.iloc[i] = new_long_band

                # Short band logic
                if rsi_ma.iloc[i-1] < short_band.iloc[i-1] and rsi_ma.iloc[i] < short_band.iloc[i-1]:
                    short_band.iloc[i] = min(short_band.iloc[i-1], new_short_band)
                else:
                    short_band.iloc[i] = new_short_band

                # Trend logic
                if rsi_ma.iloc[i] > short_band.iloc[i-1]:
                    trend.iloc[i] = 1
                elif rsi_ma.iloc[i] < long_band.iloc[i-1]:
                    trend.iloc[i] = -1
                else:
                    trend.iloc[i] = trend.iloc[i-1]

        df['qqe_long_band'] = long_band
        df['qqe_short_band'] = short_band
        df['qqe_trend'] = trend

        # Fast ATR RSI Trend Line
        df['qqe_fast_atr_rsi_tl'] = df.apply(
            lambda row: row['qqe_long_band'] if row['qqe_trend'] == 1 else row['qqe_short_band'],
            axis=1
        )

        # Detect signals (with anti-repainting protection)
        df['qqe_x_long'] = 0
        df['qqe_x_short'] = 0

        for i in range(1, len(df)):
            # Long signal counter
            if df['qqe_fast_atr_rsi_tl'].iloc[i] < df['rsi_ma'].iloc[i]:
                df.loc[df.index[i], 'qqe_x_long'] = df['qqe_x_long'].iloc[i-1] + 1

            # Short signal counter
            if df['qqe_fast_atr_rsi_tl'].iloc[i] > df['rsi_ma'].iloc[i]:
                df.loc[df.index[i], 'qqe_x_short'] = df['qqe_x_short'].iloc[i-1] + 1

        # Generate confirmed signals (only on bar close)
        df['qqe_long'] = False
        df['qqe_short'] = False

        for i in range(2, len(df)):
            # Long signal: first cross above
            if df['qqe_x_long'].iloc[i-1] == 1:
                df.loc[df.index[i-1], 'qqe_long'] = True

            # Short signal: first cross below
            if df['qqe_x_short'].iloc[i-1] == 1:
                df.loc[df.index[i-1], 'qqe_short'] = True

        self.df = df
        return df

    def calculate_emas(self) -> pd.DataFrame:
        """Calculate all EMAs from Pine Script"""
        if self.df is None or self.df.empty:
            raise ValueError("No data available. Call fetch_data() first.")

        df = self.df.copy()

        # Calculate EMAs
        df['ema1'] = df['Close'].ewm(span=self.params['ema1_period'], adjust=False).mean()
        df['ema2'] = df['Close'].ewm(span=self.params['ema2_period'], adjust=False).mean()
        df['ema3'] = df['Close'].ewm(span=self.params['ema3_period'], adjust=False).mean()
        df['ema4'] = df['Close'].ewm(span=self.params['ema4_period'], adjust=False).mean()
        df['ema5'] = df['Close'].ewm(span=self.params['ema5_period'], adjust=False).mean()

        self.df = df
        return df

    def calculate_ma_cloud(self) -> pd.DataFrame:
        """Calculate MA Cloud from Pine Script"""
        if self.df is None or self.df.empty:
            raise ValueError("No data available. Call fetch_data() first.")

        df = self.df.copy()

        # Calculate MA Cloud components
        df['ma_cloud_short'] = df['Close'].ewm(span=self.params['ma_cloud_short'], adjust=False).mean()
        df['ma_cloud_long'] = df['Close'].ewm(span=self.params['ma_cloud_long'], adjust=False).mean()
        df['ma_cloud_sma'] = df['Close'].rolling(window=self.params['ma_cloud_sma']).mean()

        # Determine trend
        df['ma_cloud_trend'] = df.apply(
            lambda row: 'bullish' if row['ma_cloud_short'] > row['ma_cloud_long'] else 'bearish',
            axis=1
        )

        self.df = df
        return df

    def calculate_vwap(self) -> pd.DataFrame:
        """Calculate VWAP with standard deviation bands"""
        if self.df is None or self.df.empty:
            raise ValueError("No data available. Call fetch_data() first.")

        df = self.df.copy()

        # Typical price
        df['typical_price'] = (df['High'] + df['Low'] + df['Close']) / 3

        # VWAP calculation
        df['tp_volume'] = df['typical_price'] * df['Volume']
        df['cumulative_tp_volume'] = df['tp_volume'].cumsum()
        df['cumulative_volume'] = df['Volume'].cumsum()
        df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']

        # Calculate standard deviation for bands
        df['vwap_diff_sq'] = (df['typical_price'] - df['vwap']) ** 2
        df['cumulative_diff_sq'] = (df['vwap_diff_sq'] * df['Volume']).cumsum()
        df['vwap_variance'] = df['cumulative_diff_sq'] / df['cumulative_volume']
        df['vwap_stdev'] = np.sqrt(df['vwap_variance'])

        # Standard deviation bands
        df['vwap_upper1'] = df['vwap'] + (df['vwap_stdev'] * self.params['vwap_stdev_mult1'])
        df['vwap_lower1'] = df['vwap'] - (df['vwap_stdev'] * self.params['vwap_stdev_mult1'])
        df['vwap_upper2'] = df['vwap'] + (df['vwap_stdev'] * self.params['vwap_stdev_mult2'])
        df['vwap_lower2'] = df['vwap'] - (df['vwap_stdev'] * self.params['vwap_stdev_mult2'])
        df['vwap_upper3'] = df['vwap'] + (df['vwap_stdev'] * self.params['vwap_stdev_mult3'])
        df['vwap_lower3'] = df['vwap'] - (df['vwap_stdev'] * self.params['vwap_stdev_mult3'])

        self.df = df
        return df

    def run_complete_analysis(self) -> pd.DataFrame:
        """Run all Pine Script calculations"""
        self.calculate_emas()
        self.calculate_ma_cloud()
        self.calculate_vwap()
        self.calculate_qqe()
        return self.df

    def get_latest_signal(self) -> Optional[Dict]:
        """
        Get the most recent QQE signal

        Returns:
            Dictionary with signal details or None
        """
        if self.df is None or self.df.empty:
            return None

        # Look for the most recent signal
        df = self.df.copy()

        # Get last 10 bars to check for recent signals
        recent_df = df.tail(10)

        long_signals = recent_df[recent_df['qqe_long'] == True]
        short_signals = recent_df[recent_df['qqe_short'] == True]

        last_long = None
        last_short = None

        if not long_signals.empty:
            last_long_idx = long_signals.index[-1]
            last_long = {
                'type': 'LONG',
                'timestamp': last_long_idx,
                'price': long_signals.loc[last_long_idx, 'Close'],
                'rsi': long_signals.loc[last_long_idx, 'rsi_ma'],
                'trend': long_signals.loc[last_long_idx, 'ma_cloud_trend']
            }

        if not short_signals.empty:
            last_short_idx = short_signals.index[-1]
            last_short = {
                'type': 'SHORT',
                'timestamp': last_short_idx,
                'price': short_signals.loc[last_short_idx, 'Close'],
                'rsi': short_signals.loc[last_short_idx, 'rsi_ma'],
                'trend': short_signals.loc[last_short_idx, 'ma_cloud_trend']
            }

        # Return the most recent signal
        if last_long and last_short:
            return last_long if last_long['timestamp'] > last_short['timestamp'] else last_short
        elif last_long:
            return last_long
        elif last_short:
            return last_short
        else:
            return None

    def get_all_signals(self, lookback_hours: int = 24) -> List[Dict]:
        """
        Get all signals within the lookback period

        Args:
            lookback_hours: Hours to look back for signals

        Returns:
            List of signal dictionaries
        """
        if self.df is None or self.df.empty:
            return []

        df = self.df.copy()

        # Handle timezone-aware datetime comparison
        if df.index.tz is not None:
            # If index is timezone-aware, make cutoff_time timezone-aware too
            from datetime import timezone
            cutoff_time = datetime.now(df.index.tz) - timedelta(hours=lookback_hours)
        else:
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        # Filter by time
        recent_df = df[df.index >= cutoff_time]

        signals = []

        # Get all long signals
        long_signals = recent_df[recent_df['qqe_long'] == True]
        for idx in long_signals.index:
            signals.append({
                'type': 'LONG',
                'timestamp': idx,
                'price': long_signals.loc[idx, 'Close'],
                'volume': long_signals.loc[idx, 'Volume'],
                'rsi': long_signals.loc[idx, 'rsi_ma'],
                'trend': long_signals.loc[idx, 'ma_cloud_trend'],
                'open': long_signals.loc[idx, 'Open'],
                'high': long_signals.loc[idx, 'High'],
                'low': long_signals.loc[idx, 'Low'],
                'webhook_message': self._generate_webhook_message('BUY', idx, long_signals.loc[idx, 'Close'], long_signals.loc[idx, 'Volume'])
            })

        # Get all short signals
        short_signals = recent_df[recent_df['qqe_short'] == True]
        for idx in short_signals.index:
            signals.append({
                'type': 'SHORT',
                'timestamp': idx,
                'price': short_signals.loc[idx, 'Close'],
                'volume': short_signals.loc[idx, 'Volume'],
                'rsi': short_signals.loc[idx, 'rsi_ma'],
                'trend': short_signals.loc[idx, 'ma_cloud_trend'],
                'open': short_signals.loc[idx, 'Open'],
                'high': short_signals.loc[idx, 'High'],
                'low': short_signals.loc[idx, 'Low'],
                'webhook_message': self._generate_webhook_message('SELL', idx, short_signals.loc[idx, 'Close'], short_signals.loc[idx, 'Volume'])
            })

        # Sort by timestamp
        signals.sort(key=lambda x: x['timestamp'], reverse=True)

        self.signals = signals
        return signals

    def _generate_webhook_message(self, action: str, timestamp, price: float, volume: float = 0) -> str:
        """Generate webhook message matching TradingView format"""
        message = {
            'action': action,
            'symbol': self.symbol,
            'timestamp': str(timestamp),
            'price': float(price),
            'volume': float(volume),
            'secret': 'my_secret_key_123'
        }
        return json.dumps(message, indent=2)

    def get_current_status(self) -> Dict:
        """
        Get current market status based on Pine Script indicators

        Returns:
            Dictionary with current status and indicators
        """
        if self.df is None or self.df.empty:
            return {'status': 'NO_DATA', 'message': 'No data available'}

        latest = self.df.iloc[-1]

        # Determine current signal
        current_signal = 'NEUTRAL'
        if latest['qqe_trend'] == 1:
            current_signal = 'LONG'
        elif latest['qqe_trend'] == -1:
            current_signal = 'SHORT'

        # Get EMA alignment
        ema_bullish = (latest['ema5'] > latest['ema1'] > latest['ema2'] > latest['ema3'])
        ema_bearish = (latest['ema5'] < latest['ema1'] < latest['ema2'] < latest['ema3'])

        status = {
            'status': current_signal,
            'timestamp': latest.name,
            'price': latest['Close'],
            'rsi': latest['rsi_ma'],
            'trend': latest['ma_cloud_trend'],
            'ema_alignment': 'bullish' if ema_bullish else 'bearish' if ema_bearish else 'mixed',
            'indicators': {
                'ema5': latest['ema5'],
                'ema20': latest['ema1'],
                'ema50': latest['ema2'],
                'ema100': latest['ema3'],
                'ema200': latest['ema4'],
                'vwap': latest['vwap'],
                'ma_cloud_short': latest['ma_cloud_short'],
                'ma_cloud_long': latest['ma_cloud_long']
            }
        }

        return status

    def check_for_new_signal(self) -> Optional[Dict]:
        """
        Check if there's a new signal since last check
        Used for real-time monitoring

        Returns:
            Signal dictionary if new signal detected, None otherwise
        """
        latest_signal = self.get_latest_signal()

        if latest_signal is None:
            return None

        # Check if this is a new signal
        if self.last_signal is None:
            self.last_signal = latest_signal
            return latest_signal

        # Compare timestamps
        if latest_signal['timestamp'] > self.last_signal['timestamp']:
            self.last_signal = latest_signal
            return latest_signal

        return None

    def enable_monitoring(self):
        """Enable real-time monitoring"""
        self.monitoring_enabled = True

    def disable_monitoring(self):
        """Disable real-time monitoring"""
        self.monitoring_enabled = False

    def is_monitoring(self) -> bool:
        """Check if monitoring is enabled"""
        return self.monitoring_enabled

    def get_signal_statistics(self, lookback_hours: int = 24) -> Dict:
        """
        Get detailed signal statistics

        Args:
            lookback_hours: Hours to look back for signals

        Returns:
            Dictionary with signal counts and details
        """
        signals = self.get_all_signals(lookback_hours)

        long_signals = [s for s in signals if s['type'] == 'LONG']
        short_signals = [s for s in signals if s['type'] == 'SHORT']

        # Calculate average volume for each signal type
        avg_long_volume = sum(s['volume'] for s in long_signals) / len(long_signals) if long_signals else 0
        avg_short_volume = sum(s['volume'] for s in short_signals) / len(short_signals) if short_signals else 0

        # Calculate price change statistics
        long_price_changes = []
        short_price_changes = []

        for i in range(len(long_signals) - 1):
            price_change = ((long_signals[i]['price'] - long_signals[i+1]['price']) / long_signals[i+1]['price']) * 100
            long_price_changes.append(price_change)

        for i in range(len(short_signals) - 1):
            price_change = ((short_signals[i]['price'] - short_signals[i+1]['price']) / short_signals[i+1]['price']) * 100
            short_price_changes.append(price_change)

        avg_long_price_change = sum(long_price_changes) / len(long_price_changes) if long_price_changes else 0
        avg_short_price_change = sum(short_price_changes) / len(short_price_changes) if short_price_changes else 0

        return {
            'total_signals': len(signals),
            'long_count': len(long_signals),
            'short_count': len(short_signals),
            'long_signals': long_signals,
            'short_signals': short_signals,
            'avg_long_volume': avg_long_volume,
            'avg_short_volume': avg_short_volume,
            'avg_long_price_change': avg_long_price_change,
            'avg_short_price_change': avg_short_price_change,
            'lookback_hours': lookback_hours,
            'period_start': signals[-1]['timestamp'] if signals else None,
            'period_end': signals[0]['timestamp'] if signals else None
        }
