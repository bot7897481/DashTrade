"""
Trading Bot Management Page
Configure automated trading strategies with TradingView webhooks
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Set page config
st.set_page_config(page_title="Trading Bot", page_icon="🤖", layout="wide")

# Import after st.set_page_config
from bot_database import (
    BotAPIKeysDB, BotConfigDB, BotTradesDB, WebhookTokenDB, RiskEventDB,
    SystemStrategyDB, UserStrategySubscriptionDB, UserOutgoingWebhookDB
)
from bot_engine import TradingEngine

# Check authentication
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.error("Please log in to access the Trading Bot")
    st.stop()

# Get user info from session state (stored in 'user' dict)
user_id = st.session_state['user']['id']
username = st.session_state['user']['username']

# ============================================================================
# MAIN PAGE
# ============================================================================

st.title("🤖 Automated Trading Bot")
st.markdown(f"**User:** {username}")
st.markdown("---")

# Create tabs
tab1, tab2, tab2b, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⚙️ Setup", "📋 My Bots", "📡 System Strategies", "📊 Live Positions",
    "📜 Trade History", "📈 Performance", "⚠️ Risk Events", "🔗 Webhooks"
])

# ============================================================================
# TAB 1: SETUP (API Keys & Webhook)
# ============================================================================

with tab1:
    st.header("⚙️ Bot Setup")

    # Check if user has API keys
    has_keys = BotAPIKeysDB.has_api_keys(user_id)

    if has_keys:
        keys = BotAPIKeysDB.get_api_keys(user_id)
        st.success(f"✅ Alpaca API connected ({keys['mode'].upper()} mode)")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Update API Keys"):
                st.session_state.update_keys = True

        with col2:
            if st.button("🗑️ Remove API Keys", type="secondary"):
                if st.checkbox("Confirm deletion"):
                    if BotAPIKeysDB.delete_api_keys(user_id):
                        st.success("API keys removed")
                        st.rerun()

    if not has_keys or st.session_state.get('update_keys', False):
        st.subheader("Connect Alpaca Account")

        with st.form("api_keys_form"):
            st.markdown("""
            Get your API keys from [Alpaca Markets](https://alpaca.markets):
            1. Sign up for a free account
            2. Go to Paper Trading dashboard
            3. Generate API keys
            """)

            api_key = st.text_input("Alpaca API Key", type="password")
            secret_key = st.text_input("Alpaca Secret Key", type="password")

            mode = st.radio(
                "Trading Mode",
                options=['paper', 'live'],
                index=0,
                help="Start with paper trading to test your strategies"
            )

            if mode == 'live':
                st.warning("⚠️ Live trading uses real money! Make sure you understand the risks.")

            submit = st.form_submit_button("💾 Save API Keys")

            if submit:
                if not api_key or not secret_key:
                    st.error("Please enter both API key and secret")
                else:
                    with st.spinner("Saving and validating API keys..."):
                        success, error_msg = BotAPIKeysDB.save_api_keys(user_id, api_key, secret_key, mode)
                        if success:
                            st.success("✅ API keys saved successfully!")
                            st.session_state.update_keys = False
                            st.rerun()
                        else:
                            st.error(f"Failed to save API keys: {error_msg}")

    # Webhook URL section
    if has_keys:
        st.markdown("---")
        st.subheader("📡 TradingView Webhook URL")

        # Get or generate webhook token
        token = WebhookTokenDB.get_user_token(user_id)

        if not token:
            st.info("Generate a webhook URL to receive TradingView alerts")
            if st.button("🔗 Generate Webhook URL"):
                token = WebhookTokenDB.generate_token(user_id)
                st.rerun()

        if token:
            # Webhook URL - use dedicated webhook service (hardcoded for reliability)
            webhook_url = f"https://webhook.novalgo.org/webhook?token={token}"

            st.code(webhook_url, language=None)

            # Token management buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Regenerate Token", help="Generate a new token (old URL will stop working)"):
                    # Delete old token and generate new one
                    WebhookTokenDB.delete_user_token(user_id)
                    new_token = WebhookTokenDB.generate_token(user_id)
                    if new_token:
                        st.success("✅ New token generated! Update your TradingView alerts with the new URL.")
                        st.rerun()
                    else:
                        st.error("Failed to generate new token")

            with col2:
                if st.button("🗑️ Remove Webhook", type="secondary", help="Delete your webhook token"):
                    if st.session_state.get('confirm_delete_token', False):
                        WebhookTokenDB.delete_user_token(user_id)
                        st.session_state.confirm_delete_token = False
                        st.success("Webhook token removed")
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_token = True
                        st.warning("Click again to confirm deletion")

            st.info("""
            **How to use this webhook:**
            1. Copy the URL above
            2. In TradingView, create an alert
            3. Set Webhook URL to the URL above
            4. Use this message format:
            ```
            {
              "action": "{{strategy.order.action}}",
              "symbol": "{{ticker}}",
              "timeframe": "15 Min"
            }
            ```
            """)

# ============================================================================
# TAB 2: MY BOTS
# ============================================================================

with tab2:
    st.header("📋 My Trading Bots")

    if not has_keys:
        st.warning("⚠️ Please configure your Alpaca API keys in the Setup tab first")
    else:
        # Add new bot section
        with st.expander("➕ Add New Bot", expanded=False):
            with st.form("add_bot_form"):
                col1, col2 = st.columns(2)

                with col1:
                    symbol = st.text_input("Symbol (e.g., AAPL, TSLA)", value="").upper()
                    timeframe = st.selectbox(
                        "Timeframe",
                        options=["5 Min", "15 Min", "30 Min", "45 Min", "1 Hour", "4 Hour", "1 Day"],
                        index=1
                    )
                    position_size = st.number_input(
                        "Position Size ($)",
                        min_value=100.0,
                        max_value=100000.0,
                        value=5000.0,
                        step=100.0
                    )
                    
                    signal_source = st.selectbox(
                        "Signal Source",
                        options=["Webhook", "Internal (Yahoo)", "Internal (Alpaca)"],
                        index=0,
                        help="Webhook: Wait for external TradingView signals. Internal (Yahoo): DashTrade calculates signals using Yahoo data (15m delay). Internal (Alpaca): DashTrade calculates signals using Alpaca Real-Time data."
                    )

                with col2:
                    strategy_name = st.text_input("Strategy Name (optional)", value="")
                    risk_limit = st.number_input(
                        "Risk Limit (%)",
                        min_value=1.0,
                        max_value=100.0,
                        value=10.0,
                        step=0.5,
                        help="Close position if loss exceeds this percentage"
                    )
                    daily_loss_limit = st.number_input(
                        "Daily Loss Limit ($) (optional)",
                        min_value=0.0,
                        value=0.0,
                        step=100.0
                    )
                    
                    strategy_type = st.selectbox(
                        "Internal Strategy",
                        options=["none", "NovAlgo Fast Signals [Custom]"],
                        index=0,
                        help="Only used if Signal Source starts with 'Internal'"
                    )

                submit_bot = st.form_submit_button("✅ Create Bot")

                if submit_bot:
                    if not symbol:
                        st.error("Please enter a symbol")
                    elif "Internal" in signal_source and strategy_type == "none":
                        st.error("Please select an Internal Strategy (e.g., NovAlgo Fast Signals) when using an Internal Signal Source.")
                    else:
                        # Check if bot already exists with SAME signal source
                        # (Allow multiple bots for same symbol+timeframe with different signal sources)
                        signal_source_key = signal_source.lower()
                        existing = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol, timeframe, signal_source_key)
                        if existing:
                            st.error(f"Bot already exists for {symbol} {timeframe} with signal source '{signal_source}'. Choose a different signal source or edit the existing bot.")
                        else:
                            bot_id = BotConfigDB.create_bot(
                                user_id=user_id,
                                symbol=symbol,
                                timeframe=timeframe,
                                position_size=position_size,
                                strategy_name=strategy_name if strategy_name else None,
                                risk_limit_percent=risk_limit,
                                daily_loss_limit=daily_loss_limit if daily_loss_limit > 0 else None,
                                signal_source=signal_source_key,
                                strategy_type=strategy_type if "Internal" in signal_source else "none"
                            )

                            if bot_id:
                                st.success(f"✅ Bot created for {symbol} {timeframe} ({signal_source})")
                                st.rerun()
                            else:
                                st.error("Failed to create bot")

        # Display existing bots
        st.markdown("---")
        bots = BotConfigDB.get_user_bots(user_id)

        if not bots:
            st.info("No bots configured yet. Create your first bot above!")
        else:
            st.markdown(f"**Total Bots:** {len(bots)} | **Active:** {sum(1 for b in bots if b['is_active'])}")

            # Convert to DataFrame for display
            df = pd.DataFrame(bots)

            # Select columns to display
            display_cols = [
                'symbol', 'timeframe', 'position_size', 'is_active',
                'order_status', 'risk_limit_percent', 'current_position_side',
                'total_pnl', 'total_trades'
            ]

            df_display = df[display_cols].copy()
            df_display['position_size'] = df_display['position_size'].apply(lambda x: f"${float(x):,.0f}")
            df_display['total_pnl'] = df_display['total_pnl'].apply(lambda x: f"${float(x):,.2f}" if x else "$0.00")
            df_display['risk_limit_percent'] = df_display['risk_limit_percent'].apply(lambda x: f"{float(x):.1f}%")

            # Renamed columns for display
            df_display.columns = [
                'Symbol', 'Timeframe', 'Position Size', 'Active',
                'Status', 'Risk Limit', 'Position', 'Total P&L', 'Trades'
            ]
            
            # Add Source column to display df
            df_display['Source'] = df['signal_source'].apply(lambda x: "🔗 " + x.title())
            df_display['Strategy'] = df['strategy_type'].apply(lambda x: x if x != 'none' else "N/A")
            
            st.dataframe(df_display[['Symbol', 'Timeframe', 'Source', 'Strategy', 'Position Size', 'Active', 'Status', 'Risk Limit', 'Position', 'Total P&L', 'Trades']], use_container_width=True, hide_index=True)

            # Bot management
            st.markdown("### Manage Bots")

            cols = st.columns(4)

            for idx, bot in enumerate(bots):
                with cols[idx % 4]:
                    with st.container(border=True):
                        st.markdown(f"**{bot['symbol']} - {bot['timeframe']}**")
                        st.caption(f"Status: {bot['order_status']}")

                        toggle_label = "🔴 Disable" if bot['is_active'] else "🟢 Enable"
                        if st.button(toggle_label, key=f"toggle_{bot['id']}"):
                            new_status = not bot['is_active']
                            if BotConfigDB.toggle_bot(bot['id'], user_id, new_status):
                                st.success(f"Bot {'enabled' if new_status else 'disabled'}")
                                st.rerun()

                        if st.button("🗑️ Delete", key=f"delete_{bot['id']}", type="secondary"):
                            if BotConfigDB.delete_bot(bot['id'], user_id):
                                st.success("Bot deleted")
                                st.rerun()

# ============================================================================
# TAB 2B: SYSTEM STRATEGIES (Subscribe to company signals)
# ============================================================================

with tab2b:
    st.header("📡 System Strategies")
    st.caption("Subscribe to NovAlgo's TradingView strategies - signals are executed automatically")

    if not has_keys:
        st.warning("⚠️ Please configure your Alpaca API keys in the Setup tab first")
    else:
        # Get available system strategies
        try:
            system_strategies = SystemStrategyDB.get_all_strategies(active_only=True)
        except Exception:
            system_strategies = []
            st.warning("⚠️ System strategies not available. Database migration may be needed.")

        if not system_strategies:
            st.info("No system strategies available yet. Check back later!")
        else:
            # Get user's bots for subscription
            user_bots = BotConfigDB.get_user_bots(user_id)

            if not user_bots:
                st.warning("⚠️ You need to create a bot first in the 'My Bots' tab before subscribing to strategies")
            else:
                st.markdown("### Available Strategies")

                for strategy in system_strategies:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 2])

                        with col1:
                            st.markdown(f"### 📈 {strategy['name']}")
                            st.markdown(f"**Symbol:** {strategy['symbol']} | **Timeframe:** {strategy['timeframe']}")
                            if strategy.get('description'):
                                st.write(strategy['description'])

                            # Show stats
                            st.caption(f"📊 Total signals sent: {strategy.get('total_signals', 0)}")

                        with col2:
                            st.markdown("**Subscribe with your bot:**")

                            # Select which bot to subscribe
                            matching_bots = [b for b in user_bots if b['symbol'] == strategy['symbol']]

                            if not matching_bots:
                                st.info(f"Create a bot for {strategy['symbol']} to subscribe")
                                if st.button(f"➕ Quick Create Bot for {strategy['symbol']}", key=f"quick_create_{strategy['id']}"):
                                    bot_id = BotConfigDB.create_bot(
                                        user_id=user_id,
                                        symbol=strategy['symbol'],
                                        timeframe=strategy['timeframe'],
                                        position_size=1000.0,
                                        strategy_name=f"System: {strategy['name']}",
                                        signal_source='system'
                                    )
                                    if bot_id:
                                        st.success(f"✅ Bot created! Refresh to subscribe.")
                                        st.rerun()
                            else:
                                for bot in matching_bots:
                                    is_subscribed = UserStrategySubscriptionDB.is_subscribed(
                                        user_id, strategy['id'], bot['id']
                                    )

                                    bot_label = f"{bot['symbol']} - {bot['timeframe']} (${float(bot['position_size']):,.0f})"

                                    if is_subscribed:
                                        st.success(f"✅ Subscribed: {bot_label}")
                                        if st.button("Unsubscribe", key=f"unsub_{strategy['id']}_{bot['id']}"):
                                            UserStrategySubscriptionDB.unsubscribe(user_id, strategy['id'], bot['id'])
                                            st.rerun()
                                    else:
                                        st.write(f"Bot: {bot_label}")

                        # Risk Warning & Subscribe form (only if not subscribed)
                        if matching_bots:
                            not_subscribed_bots = [
                                b for b in matching_bots
                                if not UserStrategySubscriptionDB.is_subscribed(user_id, strategy['id'], b['id'])
                            ]

                            if not_subscribed_bots:
                                with st.expander("⚠️ Subscribe - Read Risk Disclaimer First"):
                                    st.error(f"""
                                    **RISK DISCLAIMER**

                                    {strategy.get('risk_warning', 'Trading involves substantial risk. Past performance is not indicative of future results.')}

                                    By subscribing, you acknowledge:
                                    - This strategy is provided by NovAlgo's TradingView alerts
                                    - Signals are generated automatically and may result in losses
                                    - NovAlgo is NOT responsible for any trading losses
                                    - You are trading with your own funds at your own risk
                                    - Past performance does not guarantee future results
                                    """)

                                    selected_bot = st.selectbox(
                                        "Select bot to subscribe:",
                                        options=[f"{b['id']}|{b['symbol']} - {b['timeframe']}" for b in not_subscribed_bots],
                                        key=f"select_bot_{strategy['id']}"
                                    )

                                    accept_disclaimer = st.checkbox(
                                        "I have read and accept the risk disclaimer",
                                        key=f"accept_{strategy['id']}"
                                    )

                                    if st.button("✅ Subscribe to Strategy", key=f"subscribe_{strategy['id']}", type="primary"):
                                        if not accept_disclaimer:
                                            st.error("❌ You must accept the risk disclaimer to subscribe")
                                        else:
                                            bot_id = int(selected_bot.split('|')[0])
                                            success, msg = UserStrategySubscriptionDB.subscribe(
                                                user_id=user_id,
                                                strategy_id=strategy['id'],
                                                bot_config_id=bot_id,
                                                disclaimer_accepted=True
                                            )
                                            if success:
                                                st.success(f"✅ {msg}")
                                                st.balloons()
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {msg}")

                # Show user's current subscriptions
                st.markdown("---")
                st.markdown("### Your Subscriptions")

                try:
                    subscriptions = UserStrategySubscriptionDB.get_user_subscriptions(user_id)
                except Exception:
                    subscriptions = []

                if not subscriptions:
                    st.info("You haven't subscribed to any system strategies yet")
                else:
                    for sub in subscriptions:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.markdown(f"**{sub['strategy_name']}**")
                                st.caption(f"{sub['symbol']} | {sub['timeframe']}")
                            with col2:
                                st.write(f"Position Size: ${float(sub['position_size']):,.0f}")
                                st.caption(f"Subscribed: {sub['created_at']}")
                            with col3:
                                if st.button("🔴 Unsubscribe", key=f"unsub_list_{sub['id']}"):
                                    UserStrategySubscriptionDB.unsubscribe(user_id, sub['strategy_id'], sub['bot_config_id'])
                                    st.rerun()

# ============================================================================
# TAB 3: LIVE POSITIONS
# ============================================================================

with tab3:
    st.header("📊 Live Positions")

    if not has_keys:
        st.warning("⚠️ Please configure your Alpaca API keys first")
    else:
        if st.button("🔄 Refresh Positions"):
            st.rerun()

        try:
            engine = TradingEngine(user_id)

            # Get account info
            account = engine.get_account_info()

            if account:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Equity", f"${account['equity']:,.2f}")
                col2.metric("Cash", f"${account['cash']:,.2f}")
                col3.metric("Buying Power", f"${account['buying_power']:,.2f}")
                col4.metric("Portfolio Value", f"${account['portfolio_value']:,.2f}")

            # Get positions
            positions = engine.get_all_positions()

            if not positions:
                st.info("No open positions")
            else:
                df_pos = pd.DataFrame(positions)

                # Format for display
                df_pos['qty'] = df_pos['qty'].apply(lambda x: f"{x:.2f}")
                df_pos['market_value'] = df_pos['market_value'].apply(lambda x: f"${x:,.2f}")
                df_pos['unrealized_pl'] = df_pos['unrealized_pl'].apply(lambda x: f"${x:,.2f}")
                df_pos['unrealized_plpc'] = df_pos['unrealized_plpc'].apply(lambda x: f"{x:.2f}%")
                df_pos['entry_price'] = df_pos['entry_price'].apply(lambda x: f"${x:.2f}")
                df_pos['current_price'] = df_pos['current_price'].apply(lambda x: f"${x:.2f}")

                st.dataframe(df_pos, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error loading positions: {e}")

# ============================================================================
# TAB 4: TRADE HISTORY
# ============================================================================

with tab4:
    st.header("📜 Trade History")

    limit = st.slider("Number of trades to show", 10, 500, 100)

    trades = BotTradesDB.get_user_trades(user_id, limit=limit)

    if not trades:
        st.info("No trades yet")
    else:
        df_trades = pd.DataFrame(trades)

        # Format for display
        display_cols = [
            'created_at', 'symbol', 'timeframe', 'action', 'status',
            'notional', 'filled_qty', 'filled_avg_price', 'order_id'
        ]

        df_display = df_trades[display_cols].copy()
        df_display['notional'] = df_display['notional'].apply(lambda x: f"${float(x):,.2f}" if x else "")
        df_display['filled_avg_price'] = df_display['filled_avg_price'].apply(lambda x: f"${float(x):.2f}" if x else "")

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Export option
        if st.button("📥 Export to CSV"):
            csv = df_trades.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"trades_{username}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ============================================================================
# TAB 5: PERFORMANCE
# ============================================================================

with tab5:
    st.header("📈 Performance Analytics")

    bots = BotConfigDB.get_user_bots(user_id)

    if not bots:
        st.info("No bots configured")
    else:
        # Performance summary
        total_pnl = sum(float(bot['total_pnl']) for bot in bots)
        total_trades = sum(bot['total_trades'] for bot in bots)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total P&L", f"${total_pnl:,.2f}")
        col2.metric("Total Trades", total_trades)
        col3.metric("Active Bots", sum(1 for b in bots if b['is_active']))

        # Per-symbol breakdown
        st.markdown("### Per-Symbol Performance")

        perf_data = []
        for bot in bots:
            perf_data.append({
                'Symbol': bot['symbol'],
                'Timeframe': bot['timeframe'],
                'P&L': float(bot['total_pnl']),
                'Trades': bot['total_trades'],
                'Position Size': float(bot['position_size']),
                'Status': bot['order_status']
            })

        df_perf = pd.DataFrame(perf_data)
        df_perf = df_perf.sort_values('P&L', ascending=False)

        st.dataframe(df_perf, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 6: RISK EVENTS
# ============================================================================

with tab6:
    st.header("⚠️ Risk Management Events")

    risk_events = RiskEventDB.get_user_risk_events(user_id, limit=50)

    if not risk_events:
        st.success("✅ No risk events triggered")
    else:
        st.warning(f"⚠️ {len(risk_events)} risk events recorded")

        df_risk = pd.DataFrame(risk_events)

        display_cols = [
            'created_at', 'event_type', 'symbol', 'timeframe',
            'threshold_value', 'current_value', 'action_taken'
        ]

        df_display = df_risk[display_cols].copy()
        df_display['threshold_value'] = df_display['threshold_value'].apply(lambda x: f"{float(x):.2f}%")
        df_display['current_value'] = df_display['current_value'].apply(lambda x: f"{float(x):.2f}%")

        st.dataframe(df_display, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 7: OUTGOING WEBHOOKS
# ============================================================================

with tab7:
    st.header("🔗 Outgoing Webhooks")
    st.caption("Forward signals to your own systems (Discord, Slack, custom APIs)")

    st.markdown("""
    Configure webhooks to receive notifications when:
    - **Signals**: Trading signals are received (buy/sell)
    - **Trades**: Orders are executed on Alpaca
    """)

    # Add new webhook
    with st.expander("➕ Add New Webhook", expanded=False):
        with st.form("add_webhook_form"):
            webhook_name = st.text_input("Webhook Name", placeholder="e.g., My Discord Bot")
            webhook_url = st.text_input("Webhook URL", placeholder="https://discord.com/api/webhooks/...")

            col1, col2 = st.columns(2)
            with col1:
                include_signals = st.checkbox("Include Signals", value=True)
            with col2:
                include_trades = st.checkbox("Include Trades", value=True)

            st.caption("Example payload sent to your webhook:")
            st.code("""{
  "event": "signal",
  "symbol": "AAPL",
  "action": "buy",
  "timeframe": "15 Min",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "system_strategy" or "user_webhook"
}""", language="json")

            submit_webhook = st.form_submit_button("💾 Save Webhook")

            if submit_webhook:
                if not webhook_url:
                    st.error("❌ Please enter a webhook URL")
                elif not webhook_url.startswith('http'):
                    st.error("❌ Webhook URL must start with http:// or https://")
                else:
                    success, msg = UserOutgoingWebhookDB.save_webhook(
                        user_id=user_id,
                        webhook_url=webhook_url,
                        webhook_name=webhook_name or "Unnamed Webhook",
                        include_signals=include_signals,
                        include_trades=include_trades
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # Display existing webhooks
    st.markdown("---")
    st.markdown("### Your Webhooks")

    try:
        webhooks = UserOutgoingWebhookDB.get_user_webhooks(user_id, active_only=False)
    except Exception:
        webhooks = []
        st.warning("⚠️ Webhooks not available. Database migration may be needed.")

    if not webhooks:
        st.info("No webhooks configured yet. Add one above to receive notifications!")
    else:
        for wh in webhooks:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    status_icon = "🟢" if wh['is_active'] else "🔴"
                    st.markdown(f"**{status_icon} {wh.get('webhook_name', 'Unnamed')}**")
                    st.caption(f"URL: {wh['webhook_url'][:50]}...")

                    # Show what's included
                    includes = []
                    if wh.get('include_signals'):
                        includes.append("📊 Signals")
                    if wh.get('include_trades'):
                        includes.append("💰 Trades")
                    st.write(" | ".join(includes) if includes else "Nothing selected")

                with col2:
                    st.metric("Successful Calls", wh.get('success_count', 0))
                    st.metric("Failed Calls", wh.get('failure_count', 0))
                    if wh.get('last_called_at'):
                        st.caption(f"Last called: {wh['last_called_at']}")

                with col3:
                    # Toggle active status
                    if wh['is_active']:
                        if st.button("🔴 Disable", key=f"disable_wh_{wh['id']}"):
                            UserOutgoingWebhookDB.toggle_webhook(user_id, wh['id'], False)
                            st.rerun()
                    else:
                        if st.button("🟢 Enable", key=f"enable_wh_{wh['id']}"):
                            UserOutgoingWebhookDB.toggle_webhook(user_id, wh['id'], True)
                            st.rerun()

                    if st.button("🗑️ Delete", key=f"delete_wh_{wh['id']}", type="secondary"):
                        UserOutgoingWebhookDB.delete_webhook(user_id, wh['id'])
                        st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("⚠️ Trading involves risk. Only trade with money you can afford to lose. Start with paper trading to test your strategies.")
