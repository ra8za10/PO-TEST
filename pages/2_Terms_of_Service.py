"""
pages/2_Terms_of_Service.py
---------------------------
Public terms of service. Like the privacy policy, this page is intentionally
reachable without logging in so Google's OAuth reviewers can read it.

Live URL (Streamlit multipage): https://<your-app>.streamlit.app/Terms_of_Service
"""

import streamlit as st

from config import (
    AI_PROVIDER,
    APP_NAME,
    CONTACT_EMAIL,
    GOVERNING_LAW,
    LEGAL_ENTITY,
    LEGAL_LAST_UPDATED,
)

st.set_page_config(page_title=f"Terms of Service — {APP_NAME}", page_icon="📜", layout="centered")

st.title("📜 Syarat & Ketentuan / Terms of Service")
st.caption(f"Terakhir diperbarui: {LEGAL_LAST_UPDATED}")

st.markdown(
    f"""
Dengan mengakses atau menggunakan **{APP_NAME}** ("Layanan"), yang dioperasikan
oleh {LEGAL_ENTITY} ("kami"), Anda menyetujui syarat berikut. Jika Anda tidak
setuju, mohon jangan menggunakan Layanan ini.

---

## 1. Deskripsi layanan

{APP_NAME} membantu Anda mengubah teks pesanan WhatsApp yang tidak terstruktur
menjadi baris data terstruktur, menyimpannya ke Google Spreadsheet **milik Anda
sendiri**, dan membuat tabel pivot untuk analisis. Kami tidak menyediakan
penyimpanan data; spreadsheet Anda tetap milik dan tanggung jawab Anda.

---

## 2. Akun Google dan otorisasi

Layanan memerlukan login dengan akun Google Anda melalui OAuth 2.0. Anda
memberikan izin kepada Layanan untuk mengakses Google Sheets dan membaca daftar
file Spreadsheet Anda, sebagaimana dijelaskan pada
[Kebijakan Privasi](/Privacy_Policy). Anda dapat mencabut izin ini kapan saja di
[Google Account Permissions](https://myaccount.google.com/permissions).

Anda bertanggung jawab menjaga keamanan akun Google Anda.

---

## 3. Penggunaan yang dapat diterima

Anda setuju untuk **tidak**:

- menggunakan Layanan untuk tujuan melanggar hukum atau melanggar hak pihak lain;
- mengunggah data pribadi orang lain tanpa dasar hukum yang sah;
- mencoba meretas, membebani, melakukan *reverse engineering*, atau mengganggu
  Layanan maupun infrastruktur pihak ketiga yang digunakannya;
- menggunakan Layanan untuk mengirim spam atau menyalahgunakan API Google.

Anda bertanggung jawab penuh atas isi teks yang Anda tempelkan, termasuk data
pelanggan (nama, nomor WhatsApp, alamat) dan kepatuhannya terhadap peraturan
perlindungan data yang berlaku bagi bisnis Anda.

---

## 4. Akurasi AI — penting

Ekstraksi data dilakukan oleh model kecerdasan buatan pihak ketiga
({AI_PROVIDER}). Hasilnya **dapat mengandung kesalahan**: salah membaca jumlah,
harga, alamat, atau melewatkan bagian pesanan.

**Anda wajib meninjau setiap baris pada tabel pratinjau sebelum menyimpannya.**
Layanan menyediakan editor pratinjau justru untuk keperluan ini. Kami tidak
bertanggung jawab atas kerugian yang timbul dari data yang salah, termasuk
kesalahan pengiriman, kesalahan penagihan, atau kehilangan pendapatan.

---

## 5. Layanan pihak ketiga

Layanan bergantung pada Google API dan penyedia model AI. Ketersediaan,
perubahan, atau kegagalan layanan pihak ketiga tersebut berada di luar kendali
kami. Penggunaan Anda atas Google Sheets dan Drive juga tunduk pada syarat
layanan Google.

---

## 6. Ketersediaan

Layanan disediakan **"sebagaimana adanya" (as is)** dan **"sebagaimana
tersedia"**. Kami dapat mengubah, menangguhkan, atau menghentikan seluruh atau
sebagian Layanan kapan saja tanpa pemberitahuan. Kami tidak menjamin Layanan
akan bebas gangguan, bebas kesalahan, atau aman dari kehilangan data.

---

## 7. Penafian jaminan

Sejauh diizinkan hukum yang berlaku, kami menafikan semua jaminan, baik tersurat
maupun tersirat, termasuk jaminan kelayakan untuk diperjualbelikan, kesesuaian
untuk tujuan tertentu, dan non-pelanggaran.

---

## 8. Batasan tanggung jawab

Sejauh diizinkan hukum, {LEGAL_ENTITY} tidak bertanggung jawab atas kerugian
tidak langsung, insidental, khusus, konsekuensial, atau kehilangan keuntungan,
data, atau niat baik yang timbul dari penggunaan Layanan — termasuk kerugian
akibat kesalahan ekstraksi AI atau kehilangan data pada spreadsheet Anda.

---

## 9. Data Anda

Anda tetap menjadi pemilik seluruh data yang Anda masukkan dan seluruh isi
Google Spreadsheet Anda. Kami tidak mengklaim kepemilikan apa pun atasnya, dan
kami tidak menyimpan salinannya.

---

## 10. Penghentian

Anda dapat berhenti menggunakan Layanan kapan saja dengan logout dan mencabut
akses di setelan akun Google Anda. Kami dapat menghentikan akses Anda apabila
Anda melanggar syarat ini.

---

## 11. Perubahan syarat

Kami dapat memperbarui syarat ini sewaktu-waktu. Penggunaan Layanan setelah
perubahan berarti Anda menerima syarat yang telah diperbarui.

---

## 12. Hukum yang berlaku

Syarat ini diatur oleh hukum {GOVERNING_LAW}, tanpa memperhatikan
pertentangan ketentuan hukum.

---

## 13. Kontak

Pertanyaan tentang syarat ini: **{CONTACT_EMAIL}**
"""
)

st.divider()
# Plain relative links — see the note in the privacy policy page.
st.markdown("🏠 [Kembali ke aplikasi](/) &nbsp;·&nbsp; 🔒 [Kebijakan Privasi](/Privacy_Policy)")
