"""
config.py
---------
Central place for constants, OAuth scopes, the canonical data schema and
small configuration helpers. Keeping these in one module makes the rest of
the codebase easy to reason about and avoids "magic strings" scattered around.
"""

from __future__ import annotations

import os

import streamlit as st

# ---------------------------------------------------------------------------
# OAuth scopes
# ---------------------------------------------------------------------------
# We request the minimum scopes required by the product:
#   * spreadsheets        -> read/write the user's Google Sheets
#   * drive.readonly      -> list the user's existing spreadsheets in a picker
#   * openid/email/profile-> identify the signed-in user (name + avatar)
#
# NOTE: Google frequently *adds* the "openid" scope to the granted set even if
# you don't ask for it, which makes oauthlib raise a "Scope has changed"
# warning/error. We relax that check in `auth.py` via OAUTHLIB_RELAX_TOKEN_SCOPE.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Google API discovery endpoints
SHEETS_API = ("sheets", "v4")
DRIVE_API = ("drive", "v3")
OAUTH2_API = ("oauth2", "v2")

# MIME type that identifies a native Google Sheet inside Drive.
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"

# ---------------------------------------------------------------------------
# Canonical order schema
# ---------------------------------------------------------------------------
# The column order here is the single source of truth used for:
#   * building the header row of a freshly created spreadsheet,
#   * ordering the DataFrame shown in st.data_editor,
#   * serialising rows before appending them to Google Sheets.
ORDER_COLUMNS = [
    "tanggal_pesanan",
    "nama_pelanggan",
    "kontak_wa",
    "nama_produk",
    "ukuran_atau_varian",
    "jumlah",
    "alamat_pengiriman",
    "total_harga",
]

# Human friendly labels for the UI (the sheet still stores raw column keys).
COLUMN_LABELS = {
    "tanggal_pesanan": "Tanggal Pesanan",
    "nama_pelanggan": "Nama Pelanggan",
    "kontak_wa": "Kontak WA",
    "nama_produk": "Nama Produk",
    "ukuran_atau_varian": "Ukuran / Varian",
    "jumlah": "Jumlah",
    "alamat_pengiriman": "Alamat Pengiriman",
    "total_harga": "Total Harga",
}


def get_secret(key: str, default: str | None = None) -> str | None:
    """Fetch a secret from st.secrets first, then environment variables.

    This lets the app run both on Streamlit Community Cloud (st.secrets) and in
    a plain container/VM where secrets are injected as environment variables.
    """
    # st.secrets raises if no secrets file exists at all, so guard with try.
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:  # pragma: no cover - secrets file simply absent
        pass
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# Legal / contact details used by the Privacy Policy and Terms pages
# ---------------------------------------------------------------------------
# EDIT THESE (or override any of them in secrets.toml). Google's OAuth
# verification team checks that these pages exist, are reachable WITHOUT
# logging in, and identify a real operator with a working contact address.
APP_NAME = get_secret("APP_NAME", "WA Order Parser")
# Your name or registered business name — the party these terms are between.
LEGAL_ENTITY = get_secret("LEGAL_ENTITY", "WA Order Parser")
# TODO: replace with a real, monitored address before going public.
CONTACT_EMAIL = get_secret("CONTACT_EMAIL", "you@example.com")
LEGAL_LAST_UPDATED = get_secret("LEGAL_LAST_UPDATED", "26 Juli 2026")
GOVERNING_LAW = get_secret("GOVERNING_LAW", "Republik Indonesia")
# Name of the AI provider that receives pasted text — must be disclosed.
AI_PROVIDER = get_secret("AI_PROVIDER_NAME", "OpenRouter")
