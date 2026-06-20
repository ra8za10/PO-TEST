"""
ai_parser.py
------------
The AI parsing engine. It turns messy, free-form WhatsApp order messages into a
strict, validated list of order records.

We use the **OpenAI Structured Outputs** feature (`responses.parse` / the
chat-completions `parse` helper) with a Pydantic schema. Structured Outputs
guarantees the model returns JSON that conforms to the schema, so we never have
to hand-roll brittle `json.loads` + try/except parsing of free text.

(If you prefer Gemini, the equivalent is `google-genai` with
`config=types.GenerateContentConfig(response_mime_type="application/json",
response_schema=OrderBatch)`. The rest of the app is provider-agnostic because
this module only ever returns a pandas DataFrame.)
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field

from config import ORDER_COLUMNS, get_secret

# A small, fast, structured-output-capable model is plenty for extraction.
DEFAULT_MODEL = get_secret("OPENAI_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Schema (single source of truth for the LLM contract)
# ---------------------------------------------------------------------------
class Order(BaseModel):
    """One parsed order. Field descriptions double as instructions to the LLM."""

    tanggal_pesanan: str = Field(
        description="Order date in YYYY-MM-DD format. If no date is mentioned, "
        "use today's date which is provided in the prompt."
    )
    nama_pelanggan: str = Field(description="Customer's name.")
    kontak_wa: Optional[str] = Field(
        default=None, description="Customer's WhatsApp/phone number, or null if absent."
    )
    nama_produk: str = Field(description="The product being ordered.")
    ukuran_atau_varian: Optional[str] = Field(
        default=None, description="Size or variant, or null if not specified."
    )
    jumlah: int = Field(description="Quantity ordered as an integer. Default to 1 if unclear.")
    alamat_pengiriman: str = Field(description="Full shipping address.")
    total_harga: Optional[float] = Field(
        default=None,
        description="Total price as a number, only if explicitly stated/calculated. "
        "Null otherwise — do not guess.",
    )


class OrderBatch(BaseModel):
    """A WhatsApp message may contain several orders, so we always return a list."""

    orders: List[Order]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
def _system_prompt() -> str:
    today = date.today().isoformat()
    return (
        "You are a meticulous data-entry assistant for an Indonesian small "
        "business. You receive raw, messy WhatsApp order messages that may use "
        "slang, emojis, typos, mixed Indonesian/English, inconsistent line "
        "breaks, and multiple orders in one message.\n\n"
        "Extract every distinct order into the structured schema. Rules:\n"
        f"- Today's date is {today}. Use it for `tanggal_pesanan` whenever the "
        "message does not clearly state a date.\n"
        "- Normalise phone numbers to digits (keep a leading 0 or +62 as written).\n"
        "- `jumlah` must be a positive integer; if quantity is missing assume 1.\n"
        "- Only fill `total_harga` when a concrete amount is written; never invent "
        "or compute a price from unit prices unless the total is stated.\n"
        "- Use null for any optional field you genuinely cannot find.\n"
        "- If the text contains no order at all, return an empty `orders` list."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def parse_orders(raw_text: str) -> pd.DataFrame:
    """Parse raw WhatsApp text into a DataFrame with ORDER_COLUMNS.

    Raises RuntimeError with a friendly message on configuration/API errors so
    the Streamlit layer can show it via st.error.
    """
    if not raw_text or not raw_text.strip():
        return pd.DataFrame(columns=ORDER_COLUMNS)

    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY belum diset. Tambahkan ke .streamlit/secrets.toml."
        )

    client = OpenAI(api_key=api_key, timeout=60)

    try:
        # `.parse` (Structured Outputs) returns an already-validated Pydantic
        # object in `.output_parsed`, eliminating manual JSON handling.
        completion = client.responses.parse(
            model=DEFAULT_MODEL,
            input=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": raw_text},
            ],
            text_format=OrderBatch,
        )
        batch: OrderBatch = completion.output_parsed
    except Exception as exc:  # noqa: BLE001 - timeouts, rate limits, auth, etc.
        raise RuntimeError(f"Pemrosesan AI gagal: {exc}") from exc

    if not batch or not batch.orders:
        return pd.DataFrame(columns=ORDER_COLUMNS)

    # Pydantic -> records -> DataFrame, with guaranteed column order.
    records = [order.model_dump() for order in batch.orders]
    return pd.DataFrame(records, columns=ORDER_COLUMNS)
