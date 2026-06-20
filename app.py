"""
app.py
------
WhatsApp Order Parser -> Google Sheets, a public Streamlit SaaS dashboard.

Flow:
  1. Visitor signs in with their OWN Google account (OAuth 2.0, see auth.py).
  2. They pick / create one of their own Google Sheets (Drive API).
  3. They paste raw WhatsApp text; an LLM extracts structured orders.
  4. They review/edit the parsed rows, then append them to the sheet.
  5. They build interactive pivot tables over the sheet data.

Run locally:   streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import auth
import google_services as gs
from ai_parser import parse_orders
from config import COLUMN_LABELS, ORDER_COLUMNS
from pivot import AGG_FUNCTIONS, build_pivot

st.set_page_config(
    page_title="WA Order → Google Sheets",
    page_icon="🧾",
    layout="wide",
)


# ===========================================================================
# Landing page (unauthenticated)
# ===========================================================================
def render_landing() -> None:
    """Clean 'Login with Google' interface shown before authentication."""
    st.title("🧾 WhatsApp Order Parser")
    st.subheader("Ubah pesan order WhatsApp yang berantakan menjadi data rapi di Google Sheets-mu.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            """
            **Cara kerja:**
            1. 🔐 Masuk dengan akun Google-mu sendiri.
            2. 📋 Tempel teks order dari WhatsApp.
            3. 🤖 AI merapikan & menstrukturkan datanya.
            4. 📊 Simpan ke Google Sheets & buat pivot table.

            Aplikasi ini **tidak menyimpan** data atau kredensialmu di server —
            semuanya berjalan di sesi kamu dan langsung ke Google Sheets milikmu.
            """
        )
    with col2:
        try:
            auth_url = auth.build_authorization_url()
            # st.link_button performs a normal browser navigation to Google's
            # consent screen; on return the ?code=... triggers the callback.
            st.link_button("🔓 Login with Google", auth_url, type="primary", use_container_width=True)
        except RuntimeError as exc:
            st.error(str(exc))
        st.caption("Kami meminta akses Google Sheets & daftar Drive (read-only).")


# ===========================================================================
# Sidebar (authenticated): profile, logout, spreadsheet picker / creator
# ===========================================================================
def render_sidebar(creds) -> str | None:
    """Render the sidebar and return the selected spreadsheet id (or None)."""
    user = st.session_state.get("user_info", {})

    with st.sidebar:
        st.markdown("### 👤 Profil")
        if user.get("picture"):
            st.image(user["picture"], width=64)
        st.write(f"**{user.get('name', 'Pengguna Google')}**")
        st.caption(user.get("email", ""))
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout()
            st.rerun()

        st.divider()
        st.markdown("### 📑 Spreadsheet")

        # --- Load the user's spreadsheets from Drive (cached per session) ---
        try:
            if "spreadsheets" not in st.session_state:
                with st.spinner("Memuat daftar spreadsheet…"):
                    st.session_state["spreadsheets"] = gs.list_spreadsheets(creds)
            sheets = st.session_state["spreadsheets"]
        except gs.GoogleServiceError as exc:
            st.error(str(exc))
            sheets = []

        if st.button("🔄 Refresh daftar", use_container_width=True):
            st.session_state.pop("spreadsheets", None)
            st.rerun()

        # --- Picker -----------------------------------------------------
        options = {s["name"]: s["id"] for s in sheets}
        selected_id = None
        if options:
            chosen_name = st.selectbox(
                "Pilih spreadsheet tujuan",
                options=list(options.keys()),
                index=0,
            )
            selected_id = options[chosen_name]
        else:
            st.info("Belum ada Google Sheet. Buat baru di bawah 👇")

        # --- Create new spreadsheet ------------------------------------
        with st.expander("➕ Buat Spreadsheet Baru"):
            new_title = st.text_input("Nama spreadsheet baru", placeholder="Order Toko Juni 2026")
            if st.button("Buat", use_container_width=True):
                if not new_title.strip():
                    st.warning("Isi nama spreadsheet dulu.")
                else:
                    try:
                        with st.spinner("Membuat spreadsheet…"):
                            created = gs.create_spreadsheet(creds, new_title.strip())
                        # Refresh the cached list and auto-select the new sheet.
                        st.session_state.pop("spreadsheets", None)
                        st.session_state["preselect_sheet_id"] = created["id"]
                        st.toast(f"Spreadsheet '{created['name']}' dibuat!", icon="✅")
                        st.rerun()
                    except gs.GoogleServiceError as exc:
                        st.error(str(exc))

        # Honour a just-created sheet selection across the rerun.
        preselect = st.session_state.pop("preselect_sheet_id", None)
        if preselect:
            selected_id = preselect

    return selected_id


# ===========================================================================
# Tab 1: Input Data
# ===========================================================================
def render_input_tab(creds, spreadsheet_id: str | None) -> None:
    st.header("📥 Input Data Order")

    raw_text = st.text_area(
        "Tempel teks order WhatsApp di sini",
        height=220,
        placeholder=(
            "Contoh:\n"
            "Bu mau pesan kaos polos warna hitam ukuran L 2 pcs a/n Budi 08123456789, "
            "kirim ke Jl. Melati No.5 Bandung, total 150rb ya"
        ),
    )

    if st.button("🤖 Proses Data dengan AI", type="primary"):
        if not raw_text.strip():
            st.warning("Tempel teks order dulu ya.")
        else:
            try:
                with st.spinner("AI sedang membaca & merapikan order…"):
                    parsed = parse_orders(raw_text)
                if parsed.empty:
                    st.warning("AI tidak menemukan order pada teks tersebut.")
                else:
                    # Stash in session so edits survive reruns until saved.
                    st.session_state["parsed_df"] = parsed
                    st.toast(f"{len(parsed)} order berhasil diparse!", icon="✨")
            except RuntimeError as exc:
                st.error(str(exc))

    # --- Editable preview of the parsed data ------------------------------
    if "parsed_df" in st.session_state:
        st.markdown("#### ✏️ Tinjau & edit sebelum disimpan")
        edited = st.data_editor(
            st.session_state["parsed_df"],
            num_rows="dynamic",      # user can add/delete rows manually
            use_container_width=True,
            column_config={
                col: st.column_config.Column(label=COLUMN_LABELS.get(col, col))
                for col in ORDER_COLUMNS
            },
            key="order_editor",
        )

        col_a, col_b = st.columns([1, 4])
        with col_a:
            save = st.button("💾 Simpan ke Google Sheets", type="primary")
        with col_b:
            if st.button("🗑️ Buang hasil parse"):
                st.session_state.pop("parsed_df", None)
                st.rerun()

        if save:
            if not spreadsheet_id:
                st.warning("Pilih atau buat spreadsheet tujuan di sidebar dulu.")
            elif edited.empty:
                st.warning("Tidak ada baris untuk disimpan.")
            else:
                try:
                    with st.spinner("Menyimpan ke Google Sheets…"):
                        written = gs.append_rows(creds, spreadsheet_id, edited)
                    st.toast(f"{written} baris tersimpan!", icon="✅")
                    st.success(f"Berhasil menambah {written} baris ke spreadsheet.")
                    # Clear preview + invalidate any cached analytics read.
                    st.session_state.pop("parsed_df", None)
                    st.session_state.pop("analysis_df", None)
                except gs.GoogleServiceError as exc:
                    st.error(str(exc))


# ===========================================================================
# Tab 2: Analisis & Pivot Table
# ===========================================================================
def render_pivot_tab(creds, spreadsheet_id: str | None) -> None:
    st.header("📊 Analisis & Pivot Table")

    if not spreadsheet_id:
        st.info("Pilih spreadsheet di sidebar untuk menganalisis datanya.")
        return

    # --- Load data (with manual refresh) ----------------------------------
    if st.button("🔄 Muat / segarkan data dari sheet"):
        st.session_state.pop("analysis_df", None)

    if "analysis_df" not in st.session_state:
        try:
            with st.spinner("Mengambil data dari Google Sheets…"):
                st.session_state["analysis_df"] = gs.read_sheet(creds, spreadsheet_id)
        except gs.GoogleServiceError as exc:
            st.error(str(exc))
            return

    df = st.session_state["analysis_df"]
    if df.empty:
        st.info("Sheet ini masih kosong. Tambahkan order lewat tab Input Data.")
        return

    with st.expander("👀 Lihat data mentah", expanded=False):
        st.dataframe(df, use_container_width=True)

    # --- Pivot configuration ---------------------------------------------
    st.markdown("#### ⚙️ Susun Pivot Table")
    cols = list(df.columns)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        rows = st.multiselect("Baris (Index)", cols, default=cols[:1])
    with c2:
        columns = st.multiselect("Kolom (opsional)", cols)
    with c3:
        values = st.selectbox("Nilai", cols, index=min(len(cols) - 1, 5))
    with c4:
        agg_label = st.selectbox("Agregasi", list(AGG_FUNCTIONS.keys()))

    try:
        pivot = build_pivot(
            df,
            rows=rows,
            columns=columns,
            values=values,
            aggfunc=AGG_FUNCTIONS[agg_label],
        )
        st.markdown("#### 📋 Hasil Pivot")
        st.dataframe(pivot, use_container_width=True)
    except ValueError as exc:
        st.warning(str(exc))
    except Exception as exc:  # noqa: BLE001 - bad column combos, non-numeric sums
        st.error(f"Tidak bisa membuat pivot dengan konfigurasi ini: {exc}")


# ===========================================================================
# Main
# ===========================================================================
def main() -> None:
    # If we just came back from Google's consent screen, finish the handshake.
    if auth.handle_oauth_callback():
        st.toast("Login berhasil!", icon="🎉")
        st.rerun()

    creds = auth.get_credentials()
    if creds is None:
        render_landing()
        return

    spreadsheet_id = render_sidebar(creds)

    tab1, tab2 = st.tabs(["📥 Input Data", "📊 Analisis & Pivot Table"])
    with tab1:
        render_input_tab(creds, spreadsheet_id)
    with tab2:
        render_pivot_tab(creds, spreadsheet_id)


if __name__ == "__main__":
    main()
