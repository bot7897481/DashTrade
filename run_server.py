#!/usr/bin/env python3
"""
DashTrade Server with Integrated Webhooks
Runs Streamlit with webhook routes on the same port
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def patch_streamlit_server():
    """Add webhook routes to Streamlit's Tornado server"""
    try:
        from streamlit.web.server.server import Server
        from webhook_routes import WEBHOOK_ROUTES

        # Store original _set_tornado_settings method
        original_set_tornado_settings = Server._set_tornado_settings

        def patched_set_tornado_settings(self):
            """Patched method that adds webhook routes"""
            original_set_tornado_settings(self)

            # Add webhook routes to the Tornado application
            for route in WEBHOOK_ROUTES:
                self._tornado_app.add_handlers(".*", [route])
                logger.info(f"Added webhook route: {route[0]}")

        # Apply patch
        Server._set_tornado_settings = patched_set_tornado_settings
        logger.info("Webhook routes patched into Streamlit server")
        return True

    except Exception as e:
        logger.error(f"Failed to patch Streamlit server: {e}")
        return False


def main():
    print("=" * 60)
    print("🤖 DASHTRADE SERVER WITH WEBHOOKS")
    print("=" * 60)

    # Patch Streamlit to add webhook routes
    if patch_streamlit_server():
        print("✅ Webhook routes integrated")
    else:
        print("⚠️  Webhook routes not available (will run Streamlit only)")

    # Import and run Streamlit
    from streamlit.web import cli as stcli

    port = os.environ.get('PORT', '5000')
    print(f"Starting on port {port}...")
    print("=" * 60)

    # Run Streamlit with the app
    sys.argv = [
        'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ]
    sys.exit(stcli.main())


if __name__ == '__main__':
    main()
