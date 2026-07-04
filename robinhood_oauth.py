"""
Robinhood OAuth 2.0 flow for the Agentic Trading MCP server.

Implements the standard MCP authorization flow so each user can connect
their own Robinhood account from their profile:

  1. Dynamic client registration (RFC 7591) — done once, cached in DB
  2. Authorization Code + PKCE (S256) — user logs in at robinhood.com
  3. Code exchange at the token endpoint — tokens stored per user
  4. Refresh token grant — used by robinhood_engine before trades

Discovered from https://agent.robinhood.com/.well-known/oauth-authorization-server:
  authorization_endpoint: https://robinhood.com/oauth
  token_endpoint:         https://api.robinhood.com/oauth2/token/
  registration_endpoint:  https://agent.robinhood.com/oauth/trading/register
  auth method: none (public client + PKCE), scope: internal
"""
import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

MCP_RESOURCE = "https://agent.robinhood.com/mcp/trading"
AUTHORIZATION_ENDPOINT = "https://robinhood.com/oauth"
TOKEN_ENDPOINT = "https://api.robinhood.com/oauth2/token/"
REGISTRATION_ENDPOINT = "https://agent.robinhood.com/oauth/trading/register"
SCOPE = "internal"

# Where Robinhood redirects the user after login/consent.
# Must match the redirect_uri used at client registration.
API_BASE_URL = os.environ.get(
    'API_BASE_URL', 'https://overflowing-spontaneity-production.up.railway.app'
)
REDIRECT_URI = f"{API_BASE_URL}/api/settings/robinhood/callback"

CLIENT_NAME = "DashTrade Trading Bot"


def register_client() -> Optional[Dict]:
    """
    Dynamically register DashTrade as an OAuth client with Robinhood.
    Returns {'client_id': ..., 'redirect_uri': ...} or None on failure.
    Called once; the result is cached in the database.
    """
    try:
        resp = requests.post(
            REGISTRATION_ENDPOINT,
            json={
                "client_name": CLIENT_NAME,
                "redirect_uris": [REDIRECT_URI],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": SCOPE,
            },
            timeout=15,
        )
        if resp.status_code not in (200, 201):
            logger.error(f"Robinhood client registration failed: "
                         f"HTTP {resp.status_code} {resp.text[:300]}")
            return None

        data = resp.json()
        client_id = data.get('client_id')
        if not client_id:
            logger.error("Robinhood client registration: no client_id in response")
            return None

        logger.info(f"Registered OAuth client with Robinhood: {client_id[:8]}…")
        return {'client_id': client_id, 'redirect_uri': REDIRECT_URI}
    except Exception as e:
        logger.error(f"Robinhood client registration error: {e}")
        return None


def generate_pkce() -> Tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b'=').decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return verifier, challenge


def generate_state() -> str:
    """Opaque, unguessable state parameter."""
    return secrets.token_urlsafe(32)


def build_authorize_url(client_id: str, state: str, code_challenge: str,
                        redirect_uri: Optional[str] = None) -> str:
    """Build the URL the user's browser is sent to for login/consent.

    redirect_uri MUST be the exact value the client_id was registered with.
    Pass the redirect_uri stored alongside the cached client so that a later
    change to API_BASE_URL can never desync the authorize request from the
    registration (Robinhood rejects a mismatch with a post-consent error page).
    """
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri or REDIRECT_URI,
        'scope': SCOPE,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    # Note: the RFC 8707 'resource' indicator was removed — Robinhood's
    # authorization-server metadata does not advertise resource_indicator
    # support, and including it coincided with a post-consent failure page.
    # Re-add via ROBINHOOD_SEND_RESOURCE=true if their implementation changes.
    if os.environ.get('ROBINHOOD_SEND_RESOURCE', '').lower() in ('1', 'true', 'yes'):
        params['resource'] = MCP_RESOURCE
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def exchange_code(client_id: str, code: str, code_verifier: str,
                  redirect_uri: Optional[str] = None) -> Optional[Dict]:
    """
    Exchange an authorization code for tokens.
    Returns {'access_token', 'refresh_token', 'expires_at'} or None.

    redirect_uri must match the value used in the authorize request (i.e. the
    one the client_id was registered with), or the token endpoint rejects it.
    """
    try:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri or REDIRECT_URI,
            'client_id': client_id,
            'code_verifier': code_verifier,
        }
        # Keep the resource indicator consistent with build_authorize_url: if it
        # was sent at authorize time it must also be sent here, and vice versa.
        if os.environ.get('ROBINHOOD_SEND_RESOURCE', '').lower() in ('1', 'true', 'yes'):
            data['resource'] = MCP_RESOURCE
        resp = requests.post(
            TOKEN_ENDPOINT,
            data=data,
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error(f"Robinhood code exchange failed: "
                         f"HTTP {resp.status_code} {resp.text[:300]}")
            return None

        data = resp.json()
        access_token = data.get('access_token')
        if not access_token:
            logger.error("Robinhood code exchange: no access_token in response")
            return None

        expires_at = None
        if data.get('expires_in'):
            expires_at = datetime.utcnow() + timedelta(seconds=int(data['expires_in']))

        return {
            'access_token': access_token,
            'refresh_token': data.get('refresh_token'),
            'expires_at': expires_at,
            'scope': data.get('scope', SCOPE),
        }
    except Exception as e:
        logger.error(f"Robinhood code exchange error: {e}")
        return None
