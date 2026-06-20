# 🧾 WhatsApp Order Parser → Google Sheets

A public Streamlit SaaS app that lets anyone paste messy WhatsApp order
messages, uses an LLM (OpenRouter Structured Outputs) to extract clean structured
data, appends it to **their own** Google Sheets via per-user OAuth, and builds
interactive pivot tables on a dashboard.

## ✨ Features

- **Per-user Google OAuth 2.0** — no shared service account; each visitor signs
  in with their own account. Tokens live only in the Streamlit session.
- **AI parsing** of unstructured WhatsApp text into a strict JSON schema using
  OpenRouter (OpenAI-compatible) Structured Outputs (guaranteed schema-valid
  output). Swap models via the `OPENROUTER_MODEL` secret.
- **Editable preview** (`st.data_editor`) before saving — supports multiple
  orders per message and manual corrections.
- **Drive integration** — pick an existing spreadsheet or create a new one.
- **Append to Google Sheets** with correct column ordering and types.
- **Interactive pivot table** — choose rows, columns, value & aggregation.

## 🗂️ Project structure

| File | Responsibility |
|------|----------------|
| `app.py` | Streamlit UI: landing, sidebar, tabs, orchestration |
| `auth.py` | Google OAuth 2.0 flow, token refresh, session handling |
| `google_services.py` | Drive (list) + Sheets (create/append/read) wrappers |
| `ai_parser.py` | LLM parsing engine + Pydantic schema |
| `pivot.py` | Pivot-table construction helpers |
| `config.py` | Scopes, schema, secrets loader |

## 🚀 Setup

1. **Install deps**
   ```bash
   pip install -r requirements.txt
   ```
2. **Google Cloud Console** — create an OAuth *Web application* client, enable
   the **Google Sheets API** and **Google Drive API**, and add your redirect
   URI (e.g. `http://localhost:8501`) to the client's authorized redirect URIs.
3. **Secrets** — copy the example and fill it in:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
4. **Run**
   ```bash
   streamlit run app.py
   ```

## 🔐 Security notes

- The real `.streamlit/secrets.toml` is git-ignored — never commit credentials.
- OAuth `state` is validated on callback (CSRF protection) and the `?code=`
  is stripped from the URL after a successful token exchange.
- The app stores nothing server-side; all data goes straight to the user's
  own Google Sheets.
