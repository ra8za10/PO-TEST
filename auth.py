"""
auth.py
-------
Google OAuth 2.0 (Authorization Code flow) implemented for a *public* Streamlit
app. Every visitor signs in with their **own** Google account, so we never ship
a shared service-account key. Tokens live only in `st.session_state`, which is
per-user and per-session in Streamlit, and are never written to disk.

High level flow
===============
1. Anonymous user lands on the app -> we render a "Login with Google" button
   that points at Google's consent screen (`build_authorization_url`).
2. Google redirects back to our `redirect_uri` with `?code=...&state=...`.
3. Streamlit re-runs; `handle_oauth_callback` reads `st.query_params`,
   validates the `state` (CSRF protection) and exchanges the code for tokens.
4. Credentials are stored in `session_state` and refreshed transparently when
   they expire (`get_credentials`).
"""

from __future__ import annotations

import os

import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from config import OAUTH2_API, SCOPES, get_secret

# Google often returns the granted scopes in a different order / adds "openid".
# Without this, oauthlib raises `Warning: Scope has changed` as a hard error.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
# Only relevant for local http:// development; harmless in production (https).
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "0")


# ---------------------------------------------------------------------------
# Flow construction
# ---------------------------------------------------------------------------
def _get_redirect_uri() -> str:
    """Where Google should send the user back after consent.

    This MUST exactly match one of the "Authorized redirect URIs" configured in
    the Google Cloud OAuth client. For local dev that's typically
    http://localhost:8501, for production your deployed Streamlit URL.
    """
    return get_secret("OAUTH_REDIRECT_URI", "http://localhost:8501")


def _build_flow(state: str | None = None) -> Flow:
    """Create a google-auth-oauthlib Flow from secrets.

    We use `from_client_config` (rather than a JSON file on disk) so the client
    id/secret can be supplied through st.secrets or environment variables.
    """
    client_id = get_secret("GOOGLE_CLIENT_ID")
    client_secret = get_secret("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET. "
            "Add them to .streamlit/secrets.toml or the environment."
        )

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [_get_redirect_uri()],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=_get_redirect_uri(),
        state=state,
    )


# ---------------------------------------------------------------------------
# Cross-redirect PKCE / state store
# ---------------------------------------------------------------------------
# CRITICAL: an OAuth round-trip navigates the whole browser away to Google and
# back. The app therefore returns in a *fresh* Streamlit session with an EMPTY
# st.session_state — so it cannot carry the PKCE `code_verifier` (or the CSRF
# `state`) across the redirect. Instead we keep a small process-global map keyed
# by the `state` value, which Google echoes back to us on the callback. This
# survives across sessions within the same server process (Streamlit Community
# Cloud runs one process per app, so this holds).
_PENDING_VERIFIERS: dict[str, str] = {}
_PENDING_MAX = 64


def _remember_state(state: str, code_verifier: str | None) -> None:
    """Stash the PKCE verifier for an in-flight login, bounding memory use."""
    if len(_PENDING_VERIFIERS) >= _PENDING_MAX:
        # Drop the oldest pending login to keep the map from growing unbounded.
        _PENDING_VERIFIERS.pop(next(iter(_PENDING_VERIFIERS)), None)
    _PENDING_VERIFIERS[state] = code_verifier or ""


# ---------------------------------------------------------------------------
# Step 1: send the user to Google's consent screen
# ---------------------------------------------------------------------------
def build_authorization_url() -> str:
    """Return the Google consent URL and remember its PKCE verifier server-side."""
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",      # request a refresh_token...
        prompt="consent",           # ...and force consent so we always get one
        include_granted_scopes="true",
    )
    # google-auth-oauthlib enables PKCE by default, so `authorization_url()` just
    # sent a `code_challenge` derived from flow.code_verifier. We MUST present the
    # matching verifier at token-exchange time. Stash it in the process-global
    # store keyed by `state` (NOT session_state — that is gone after the
    # redirect). Otherwise Google rejects fetch_token with "Missing code
    # verifier". The store lookup on callback also doubles as the CSRF check.
    _remember_state(state, flow.code_verifier)
    return auth_url


# ---------------------------------------------------------------------------
# Step 2: handle the redirect back from Google
# ---------------------------------------------------------------------------
def handle_oauth_callback() -> bool:
    """If we're returning from Google, exchange the code for tokens.

    Returns True when a fresh sign-in just completed, otherwise False.
    """
    params = st.query_params
    if "code" not in params:
        return False

    returned_state = params.get("state")
    # Recover the PKCE verifier for this login from the process store, keyed by
    # the `state` Google echoed back. Its presence is ALSO our CSRF check: we
    # only proceed for a `state` value that this server actually issued. (Returns
    # from a normal session_state since that is empty in this fresh session.)
    code_verifier = _PENDING_VERIFIERS.pop(returned_state, None) if returned_state else None
    if code_verifier is None:
        st.error(
            "Sesi login tidak valid atau kedaluwarsa (server mungkin baru "
            "di-restart). Silakan klik 'Login with Google' lagi."
        )
        st.query_params.clear()
        return False

    try:
        flow = _build_flow(state=returned_state)
        # Present the matching PKCE verifier so the token endpoint accepts the
        # code (empty string -> None means "no PKCE", handled gracefully).
        flow.code_verifier = code_verifier or None
        # Reconstruct the full callback URL Streamlit was hit with. oauthlib
        # parses the `code` (and `scope`) out of it to request the token.
        authorization_response = _get_redirect_uri() + "?" + _querystring(params)
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as exc:  # noqa: BLE001 - surface any token exchange error
        st.error(f"Gagal menukar kode OAuth menjadi token: {exc}")
        st.query_params.clear()
        return False

    # Persist credentials (as a dict, JSON-serialisable) in the session only.
    st.session_state["credentials"] = _credentials_to_dict(flow.credentials)
    st.session_state["user_info"] = _fetch_user_info(flow.credentials)

    # Clean the ?code=...&state=... out of the URL so a refresh doesn't re-run
    # the exchange (the code is single-use and would fail the second time).
    st.query_params.clear()
    return True


def _querystring(params) -> str:
    """Rebuild a query string from Streamlit's query params mapping."""
    from urllib.parse import urlencode

    flat = {k: (v[0] if isinstance(v, list) else v) for k, v in params.items()}
    return urlencode(flat)


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------
def _credentials_to_dict(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }


def get_credentials() -> Credentials | None:
    """Return valid Credentials from the session, refreshing if expired.

    Returns None if the user is not authenticated. Any unrecoverable refresh
    error logs the user out so the UI falls back to the login screen.
    """
    data = st.session_state.get("credentials")
    if not data:
        return None

    creds = Credentials(**data)
    if creds.valid:
        return creds

    # Token expired but we have a refresh token -> silently refresh.
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            st.session_state["credentials"] = _credentials_to_dict(creds)
            return creds
        except Exception:  # noqa: BLE001 - refresh failed, force re-login
            logout()
            return None
    return None


def _fetch_user_info(creds: Credentials) -> dict:
    """Best-effort fetch of the signed-in user's name/email/picture."""
    try:
        from googleapiclient.discovery import build

        service = build(*OAUTH2_API, credentials=creds, cache_discovery=False)
        return service.userinfo().get().execute()
    except Exception:  # noqa: BLE001 - profile is non-critical
        return {}


def is_authenticated() -> bool:
    return get_credentials() is not None


def logout() -> None:
    """Drop all auth-related state. The user returns to the landing page."""
    for key in ("credentials", "user_info"):
        st.session_state.pop(key, None)
