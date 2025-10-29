"""
Interactive TradingView-Style Charts
Advanced charting with zoom, pan, drawing tools, and signal markers
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf


class InteractiveChart:
    """TradingView-style interactive chart creator"""

    def __init__(self, df, symbol, signals=None):
        """
        Initialize interactive chart

        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            signals: Dictionary with long_signals and short_signals lists
        """
        self.df = df
        self.symbol = symbol
        self.signals = signals or {'long_signals': [], 'short_signals': []}

    def create_advanced_chart(self, show_volume=True, show_emas=True,
                             show_vwap=True, show_signals=True,
                             show_ma_cloud=True, chart_height=800):
        """
        Create TradingView-style advanced chart

        Args:
            show_volume: Show volume subplot
            show_emas: Show EMA lines
            show_vwap: Show VWAP line
            show_signals: Show signal markers
            show_ma_cloud: Show MA cloud
            chart_height: Chart height in pixels

        Returns:
            Plotly figure object
        """
        # Determine subplot configuration
        if show_volume:
            rows = 2
            row_heights = [0.7, 0.3]
            subplot_titles = (f'{self.symbol} - Advanced Chart', 'Volume')
        else:
            rows = 1
            row_heights = [1.0]
            subplot_titles = (f'{self.symbol} - Advanced Chart',)

        # Create figure
        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=subplot_titles
        )

        # Candlesticks
        fig.add_trace(
            go.Candlestick(
                x=self.df.index,
                open=self.df['open'],
                high=self.df['high'],
                low=self.df['low'],
                close=self.df['close'],
                name='OHLC',
                increasing=dict(line=dict(color='#26a69a', width=1), fillcolor='#26a69a'),
                decreasing=dict(line=dict(color='#ef5350', width=1), fillcolor='#ef5350'),
                whiskerwidth=0.5,
            ),
            row=1, col=1
        )

        # MA Cloud
        if show_ma_cloud and 'ma_cloud_short' in self.df.columns:
            fig.add_trace(
                go.Scatter(
                    x=self.df.index,
                    y=self.df['ma_cloud_short'],
                    name='Cloud Short',
                    line=dict(color='rgba(0, 200, 83, 0.5)', width=1),
                    hovertemplate='Short MA: $%{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=self.df.index,
                    y=self.df['ma_cloud_long'],
                    name='Cloud Long',
                    line=dict(color='rgba(255, 23, 68, 0.5)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(128, 128, 128, 0.2)',
                    hovertemplate='Long MA: $%{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

        # EMAs
        if show_emas:
            ema_config = {
                'ema5': {'name': 'EMA 9', 'color': '#FFD700', 'width': 1.5},
                'ema1': {'name': 'EMA 20', 'color': '#FF4500', 'width': 1.5},
                'ema2': {'name': 'EMA 50', 'color': '#FFA500', 'width': 1.5},
                'ema3': {'name': 'EMA 100', 'color': '#00FA9A', 'width': 1.5},
                'ema4': {'name': 'EMA 200', 'color': '#FFFFFF', 'width': 2}
            }

            for ema_col, config in ema_config.items():
                if ema_col in self.df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=self.df.index,
                            y=self.df[ema_col],
                            name=config['name'],
                            line=dict(color=config['color'], width=config['width']),
                            hovertemplate=f"{config['name']}: $%{{y:.2f}}<extra></extra>"
                        ),
                        row=1, col=1
                    )

        # VWAP
        if show_vwap and 'vwap' in self.df.columns:
            fig.add_trace(
                go.Scatter(
                    x=self.df.index,
                    y=self.df['vwap'],
                    name='VWAP',
                    line=dict(color='#2962FF', width=2, dash='dash'),
                    hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )

            # VWAP bands
            if 'vwap_upper1' in self.df.columns:
                for i, (upper, lower, color) in enumerate([
                    ('vwap_upper1', 'vwap_lower1', 'rgba(76, 175, 80, 0.1)'),
                    ('vwap_upper2', 'vwap_lower2', 'rgba(255, 235, 59, 0.1)'),
                    ('vwap_upper3', 'vwap_lower3', 'rgba(244, 67, 54, 0.1)')
                ], 1):
                    if upper in self.df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=self.df.index,
                                y=self.df[upper],
                                name=f'VWAP +{i}σ',
                                line=dict(color='rgba(0,0,0,0)', width=0),
                                showlegend=False,
                                hoverinfo='skip'
                            ),
                            row=1, col=1
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=self.df.index,
                                y=self.df[lower],
                                name=f'VWAP -{i}σ',
                                line=dict(color='rgba(0,0,0,0)', width=0),
                                fill='tonexty',
                                fillcolor=color,
                                showlegend=False,
                                hoverinfo='skip'
                            ),
                            row=1, col=1
                        )

        # Signal markers
        if show_signals:
            # LONG signals
            for signal in self.signals.get('long_signals', []):
                timestamp = signal['timestamp']
                price = signal['price']

                fig.add_trace(
                    go.Scatter(
                        x=[timestamp],
                        y=[price * 0.995],
                        mode='markers+text',
                        name='LONG',
                        marker=dict(
                            symbol='triangle-up',
                            size=15,
                            color='#00c853',
                            line=dict(color='white', width=2)
                        ),
                        text=['L'],
                        textposition='bottom center',
                        textfont=dict(color='white', size=10, family='Arial Black'),
                        showlegend=False,
                        hovertemplate=(
                            f"<b>LONG SIGNAL</b><br>"
                            f"Time: {timestamp}<br>"
                            f"Price: ${price:.2f}<br>"
                            f"Volume: {signal.get('volume', 0):,.0f}<br>"
                            f"RSI: {signal.get('rsi', 0):.2f}<br>"
                            f"<extra></extra>"
                        )
                    ),
                    row=1, col=1
                )

            # SHORT signals
            for signal in self.signals.get('short_signals', []):
                timestamp = signal['timestamp']
                price = signal['price']

                fig.add_trace(
                    go.Scatter(
                        x=[timestamp],
                        y=[price * 1.005],
                        mode='markers+text',
                        name='SHORT',
                        marker=dict(
                            symbol='triangle-down',
                            size=15,
                            color='#ff1744',
                            line=dict(color='white', width=2)
                        ),
                        text=['S'],
                        textposition='top center',
                        textfont=dict(color='white', size=10, family='Arial Black'),
                        showlegend=False,
                        hovertemplate=(
                            f"<b>SHORT SIGNAL</b><br>"
                            f"Time: {timestamp}<br>"
                            f"Price: ${price:.2f}<br>"
                            f"Volume: {signal.get('volume', 0):,.0f}<br>"
                            f"RSI: {signal.get('rsi', 0):.2f}<br>"
                            f"<extra></extra>"
                        )
                    ),
                    row=1, col=1
                )

        # Volume
        if show_volume:
            colors = ['#ef5350' if self.df['close'].iloc[i] < self.df['open'].iloc[i] else '#26a69a'
                     for i in range(len(self.df))]

            fig.add_trace(
                go.Bar(
                    x=self.df.index,
                    y=self.df['volume'],
                    name='Volume',
                    marker_color=colors,
                    showlegend=False,
                    hovertemplate='Volume: %{y:,.0f}<extra></extra>'
                ),
                row=2, col=1
            )

        # Update layout - TradingView style
        fig.update_layout(
            title=dict(
                text=f"<b>{self.symbol}</b> | Interactive Chart",
                font=dict(size=20, color='#d1d4dc')
            ),
            height=chart_height,
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.5)',
                font=dict(color='#d1d4dc')
            ),
            plot_bgcolor='#131722',
            paper_bgcolor='#131722',
            font=dict(color='#d1d4dc', family='Trebuchet MS'),
            dragmode='zoom',  # Enable zoom by default
            modebar=dict(
                bgcolor='rgba(0,0,0,0.5)',
                color='#d1d4dc',
                activecolor='#2962FF'
            )
        )

        # Update axes
        fig.update_xaxes(
            title_text="Date",
            gridcolor='#1e222d',
            showgrid=True,
            row=rows, col=1
        )

        fig.update_yaxes(
            title_text="Price ($)",
            gridcolor='#1e222d',
            showgrid=True,
            side='right',
            row=1, col=1
        )

        if show_volume:
            fig.update_yaxes(
                title_text="Volume",
                gridcolor='#1e222d',
                showgrid=True,
                side='right',
                row=2, col=1
            )

        # Add range selector buttons
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=4, label="4h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All")
                ]),
                bgcolor='rgba(0,0,0,0.5)',
                activecolor='#2962FF',
                font=dict(color='#d1d4dc')
            ),
            row=1, col=1
        )

        return fig
