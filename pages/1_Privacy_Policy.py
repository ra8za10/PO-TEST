"""
pages/1_Privacy_Policy.py
-------------------------
Public privacy policy. Deliberately does NOT require authentication: Google's
OAuth verification reviewers must be able to open this URL while signed out.

Live URL (Streamlit multipage): https://<your-app>.streamlit.app/Privacy_Policy
"""

import streamlit as st

from config import AI_PROVIDER, APP_NAME, CONTACT_EMAIL, LEGAL_ENTITY, LEGAL_LAST_UPDATED

st.set_page_config(page_title=f"Privacy Policy — {APP_NAME}", page_icon="🔒", layout="centered")

st.title("🔒 Kebijakan Privasi / Privacy Policy")
st.caption(f"Terakhir diperbarui: {LEGAL_LAST_UPDATED}")

st.markdown(
    f"""
{LEGAL_ENTITY} ("kami") mengoperasikan **{APP_NAME}** ("Layanan"), sebuah aplikasi
web yang mengubah teks pesanan WhatsApp yang tidak terstruktur menjadi baris data
rapi di Google Spreadsheet milik Anda sendiri. Kebijakan ini menjelaskan data apa
yang kami akses, mengapa, dan apa yang **tidak** kami lakukan.

---

## 1. Ringkasan singkat

- Kami **tidak memiliki database**. Kami tidak menyimpan pesanan, isi spreadsheet,
  atau teks WhatsApp Anda di server kami.
- Data pesanan Anda ditulis **langsung ke Google Spreadsheet milik Anda**.
- Token Google Anda hanya disimpan **di memori sesi** selama Anda memakai aplikasi,
  dan hilang saat Anda logout atau menutup tab.
- Teks yang Anda tempel dikirim ke penyedia AI ({AI_PROVIDER}) **hanya** untuk
  diekstrak menjadi data terstruktur.

---

## 2. Data yang kami akses

**a. Informasi akun Google.** Saat Anda login, kami menerima nama, alamat email,
dan foto profil Anda. Ini hanya dipakai untuk menampilkan identitas Anda di
aplikasi. Kami tidak menyimpannya setelah sesi berakhir.

**b. Google Spreadsheets (scope `spreadsheets`).** Digunakan untuk membaca sheet
yang Anda pilih (untuk analisis/pivot) dan menambahkan baris pesanan baru ke sheet
tersebut. Kami hanya mengakses spreadsheet yang **Anda pilih sendiri**.

**c. Google Drive metadata (scope `drive.readonly`).** Digunakan **hanya** untuk
menampilkan daftar nama spreadsheet Anda di dropdown pemilih. Kami tidak membaca,
mengunduh, atau mengubah file Drive Anda yang lain.

**d. Teks yang Anda tempel.** Teks pesanan WhatsApp yang Anda masukkan diproses
untuk diekstrak menjadi kolom-kolom terstruktur.

---

## 3. Bagaimana data diproses

Teks yang Anda tempel dikirim melalui koneksi terenkripsi ke **{AI_PROVIDER}**,
penyedia model AI kami, semata-mata untuk mengubahnya menjadi JSON terstruktur.
Jangan menempelkan informasi yang sangat sensitif (nomor kartu kredit, kata sandi,
data identitas rahasia) ke dalam kolom input. Penggunaan data oleh penyedia AI
tunduk pada kebijakan privasi mereka masing-masing.

Hasil ekstraksi ditampilkan untuk Anda tinjau, lalu **hanya** ditulis ke Google
Spreadsheet Anda ketika Anda menekan tombol simpan.

---

## 4. Penyimpanan dan retensi

Layanan ini bersifat *stateless*. Kami tidak menjalankan basis data pengguna.
Kredensial OAuth (access token dan refresh token) disimpan di memori sesi server
selama sesi Anda aktif dan **tidak** ditulis ke disk. Menekan **Logout**, menutup
tab, atau sesi yang kedaluwarsa akan menghapusnya.

---

## 5. Berbagi data

Kami **tidak menjual, menyewakan, atau memperdagangkan** data Anda. Data hanya
mengalir ke: (a) Google, atas nama Anda, untuk membaca/menulis spreadsheet Anda;
dan (b) penyedia AI ({AI_PROVIDER}) untuk pemrosesan teks seperti dijelaskan di
atas. Kami dapat mengungkapkan data bila diwajibkan secara hukum.

---

## 6. Kepatuhan terhadap Kebijakan Data Pengguna Google API

> Penggunaan dan pemindahan informasi yang diterima dari Google API oleh
> {APP_NAME} akan mematuhi
> [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
> termasuk persyaratan **Limited Use**.

Secara khusus, kami **tidak** menggunakan data Google Workspace Anda untuk
melatih model AI, untuk iklan, atau untuk tujuan apa pun selain menyediakan
fitur yang Anda minta secara langsung.

---

## 7. Mencabut akses

Anda dapat mencabut akses aplikasi ini kapan saja melalui
[Google Account Permissions](https://myaccount.google.com/permissions).
Pencabutan berlaku segera; kami tidak menyimpan salinan data Anda.

---

## 8. Keamanan

Semua komunikasi berjalan melalui HTTPS. Autentikasi memakai OAuth 2.0 standar
(dengan PKCE), sehingga kami **tidak pernah** melihat kata sandi Google Anda.
Meskipun demikian, tidak ada sistem yang sepenuhnya bebas risiko.

---

## 9. Anak-anak

Layanan ini tidak ditujukan untuk pengguna di bawah 13 tahun.

---

## 10. Perubahan

Kebijakan ini dapat diperbarui sewaktu-waktu. Tanggal "terakhir diperbarui" di
atas akan mencerminkan revisi terbaru.

---

## 11. Kontak

Pertanyaan tentang privasi: **{CONTACT_EMAIL}**
"""
)

st.divider()
# Plain relative links (not st.page_link): linking back to the main script from
# inside a page raises KeyError: 'url_pathname' on some Streamlit versions, and
# this page must never crash — Google's OAuth reviewers have to be able to read it.
st.markdown("🏠 [Kembali ke aplikasi](/) &nbsp;·&nbsp; 📜 [Syarat & Ketentuan](/Terms_of_Service)")
