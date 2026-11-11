import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- SAYFA YAPILANDIRMASI VE GÖRÜNÜM AYARI ---
st.set_page_config(page_title="Teklif ve Fiyat Yönetimi", page_icon="📸", layout="centered")

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- AYARLAR VE GİZLİ BİLGİLER ---
GOOGLE_SCRIPT_URL = " https://script.google.com/macros/s/AKfycbySQfRxbf427CEk8G9zwlMTVnMcry2NDRhyx_OUxADKaLYy_BrSfEXQvxuTahAWcgvG/exec"
GMAIL_KULLANICI = "afotobest@gmail.com"
GMAIL_SIFRE = "byyewfosgesogdft"

# --- VERİLERİ TABLODAN ÇEKEN FONKSİYON ---
def verileri_cek():
    fiyat_df = pd.DataFrame([
        {"Kategori": "Ana Albüm", "Secenek": "30 x 60 Mat Albüm", "Fiyat": 3500},
        {"Kategori": "Ana Albüm", "Secenek": "30 x 76 Mat Albüm", "Fiyat": 4500},
        {"Kategori": "Aile Albümü", "Secenek": "2'li Albüm", "Fiyat": 1500},
        {"Kategori": "Tablo Seçimi", "Secenek": "30 x 40 Çerçeveli", "Fiyat": 2000},
        {"Kategori": "Poz Sayısı", "Secenek": "40", "Fiyat": 1000},
        {"Kategori": "Çekim Mekanı", "Secenek": "Ayazin", "Fiyat": 2500},
        {"Kategori": "Dış Çekim Klibi", "Secenek": "Evet", "Fiyat": 3000},
        {"Kategori": "Dış Çekim Klibi", "Secenek": "Hayır", "Fiyat": 0}
    ])
    kapali_liste = []
    kampanya_sozluk = {}

    try:
        res = requests.get(GOOGLE_SCRIPT_URL, timeout=10)
        data = res.json()
        
        if "fiyatlar" in data and data["fiyatlar"]:
            fiyat_df = pd.DataFrame(data["fiyatlar"])
            
        if "kapali_tarihler" in data and data["kapali_tarihler"]:
            for t in data["kapali_tarihler"]:
                dt = datetime.strptime(str(t).split("T")[0].strip(), "%Y-%m-%d").date()
                if dt not in kapali_liste:
                    kapali_liste.append(dt)
                    
        if "kampanyalar" in data and data["kampanyalar"]:
            for k in data["kampanyalar"]:
                dt = datetime.strptime(str(k["tarih"]).split("T")[0].strip(), "%Y-%m-%d").date()
                kampanya_sozluk[dt] = int(k["oran"])
    except Exception as e:
        print(f"Hata: {e}")

    return fiyat_df, kapali_liste, kampanya_sozluk

# Oturum başlatma
if "prices_df" not in st.session_state:
    f, k_list, k_dict = verileri_cek()
    st.session_state.prices_df = f
    st.session_state.closed_dates = k_list
    st.session_state.campaign_dates = k_dict

# --- E-POSTA GÖNDERME ---
def mail_gonder(alici_eposta, ad_soyad, telefon, email, tarih_str, detaylar, toplam_tutar):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_KULLANICI
        msg['To'] = GMAIL_KULLANICI 
        msg['Subject'] = f"📷 Yeni Rezervasyon Talebi: {ad_soyad}"
        govde = f"Yeni Rezervasyon:\nAd Soyad: {ad_soyad}\nTelefon: {telefon}\nTarih: {tarih_str}\nDetaylar: {detaylar}\nTutar: {toplam_tutar:,.2f} TL"
        msg.attach(MIMEText(govde, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_KULLANICI, GMAIL_SIFRE)
        server.sendmail(GMAIL_KULLANICI, [GMAIL_KULLANICI, alici_eposta], msg.as_string())
        server.quit()
        return True
    except:
        return False

# --- KAYDETME FONKSİYONLARI ---
def google_kapali_guncelle():
    tarih_listesi = [d.strftime('%Y-%m-%d') for d in st.session_state.closed_dates]
    try:
        requests.post(GOOGLE_SCRIPT_URL, json={"islem": "kapali_tarih_guncelle", "tarihler": tarih_listesi})
    except:
        pass

def google_kampanya_guncelle():
    kampanya_listesi = [{"tarih": d.strftime('%Y-%m-%d'), "oran": oran} for d, oran in st.session_state.campaign_dates.items()]
    try:
        requests.post(GOOGLE_SCRIPT_URL, json={"islem": "kampanya_guncelle", "kampanyalar": kampanya_listesi})
    except:
        pass

# --- MENÜ ---
menu = st.sidebar.radio("Sayfa Seçin", ["Müşteri Teklif Formu", "Yönetici Paneli (Fiyat & Takvim)"])

# ================= MÜŞTERİ FORMU =================
if menu == "Müşteri Teklif Formu":
    st.title("📸 Çekim & Paket Teklif Formu")
    
    try:
        st.image("kapak_foto.jpg", use_container_width=True)
    except:
        pass 
    
    ad_soyad = st.text_input("Ad Soyad *")
    telefon = st.text_input("Telefon *")
    email = st.text_input("E-Posta Adresi *")

    if st.session_state.campaign_dates:
        kampanya_metni = "✨ **İndirimli Kampanyalı Günlerimiz:**\n"
        for d, oran in sorted(st.session_state.campaign_dates.items()):
            if d >= date.today():
                kampanya_metni += f"- 📅 **{d.strftime('%d.%m.%Y')}** tarihine özel **%{oran} İndirim!**\n"
        st.info(kampanya_metni)

    rezervasyon_tarihi = st.date_input("Çekim Tarihi Seçiniz", value=date.today(), min_value=date.today())
    tarih_kapali_mi = rezervasyon_tarihi in st.session_state.closed_dates
    kampanya_orani = st.session_state.campaign_dates.get(rezervasyon_tarihi, 0)

    if tarih_kapali_mi:
        st.error(f"⚠️ Seçtiğiniz tarih ({rezervasyon_tarihi.strftime('%d.%m.%Y')}) doludur.")

    df_prices = st.session_state.prices_df
    ana_album_opts = df_prices[df_prices['Kategori'] == 'Ana Albüm']
    album_opts = df_prices[df_prices['Kategori'] == 'Aile Albümü']
    tablo_opts = df_prices[df_prices['Kategori'] == 'Tablo Seçimi']
    poz_opts = df_prices[df_prices['Kategori'] == 'Poz Sayısı']
    mekan_opts = df_prices[df_prices['Kategori'] == 'Çekim Mekanı']
    klip_opts = df_prices[df_prices['Kategori'] == 'Dış Çekim Klibi']

    secilen_ana_album = st.selectbox("Ana Albüm", ana_album_opts['Secenek'].tolist()) if not ana_album_opts.empty else ""
    secilen_album = st.selectbox("Aile Albümü", album_opts['Secenek'].tolist()) if not album_opts.empty else ""
    secilen_tablo = st.selectbox("Tablo Seçimi", tablo_opts['Secenek'].tolist()) if not tablo_opts.empty else ""
    secilen_poz = st.selectbox("Albüm İçi Poz Sayısı", poz_opts['Secenek'].tolist()) if not poz_opts.empty else ""
    secilen_mekan = st.selectbox("Çekim Mekanı", mekan_opts['Secenek'].tolist()) if not mekan_opts.empty else ""
    secilen_klip = st.radio("Dış Çekim Klibi İstiyorum", klip_opts['Secenek'].tolist()) if not klip_opts.empty else ""

    try:
        f_ana_album = float(ana_album_opts[ana_album_opts['Secenek'] == secilen_ana_album]['Fiyat'].values[0]) if secilen_ana_album else 0.0
        f_album = float(album_opts[album_opts['Secenek'] == secilen_album]['Fiyat'].values[0]) if secilen_album else 0.0
        f_tablo = float(tablo_opts[tablo_opts['Secenek'] == secilen_tablo]['Fiyat'].values[0]) if secilen_tablo else 0.0
        f_poz = float(poz_opts[poz_opts['Secenek'] == secilen_poz]['Fiyat'].values[0]) if secilen_poz else 0.0
        f_mekan = float(mekan_opts[mekan_opts['Secenek'] == secilen_mekan]['Fiyat'].values[0]) if secilen_mekan else 0.0
        f_klip = float(klip_opts[klip_opts['Secenek'] == secilen_klip]['Fiyat'].values[0]) if secilen_klip else 0.0
    except:
        f_ana_album = f_album = f_tablo = f_poz = f_mekan = f_klip = 0.0

    ham_tutar = f_ana_album + f_album + f_tablo + f_poz + f_mekan + f_klip
    toplam_tutar = ham_tutar

    if kampanya_orani > 0:
        toplam_tutar = ham_tutar * (1 - kampanya_orani / 100)
        st.success(f"🎉 Bu tarihe özel **%{kampanya_orani} indirim** uygulandı!")

    st.markdown(f"### **Toplam Tutar: {toplam_tutar:,.2f} TL**")

    if st.button("Teklifi Gönder ve Kaydet"):
        if tarih_kapali_mi:
            st.error("❌ Kapalı tarih!")
        elif not ad_soyad or not telefon or not email:
            st.warning("Bilgileri doldurun.")
        else:
            t_str = rezervasyon_tarihi.strftime('%d.%m.%Y')
            detaylar = f"{secilen_ana_album} | {secilen_album} | {secilen_tablo}"
            veri = {"tarih": t_str, "ad_soyad": ad_soyad, "telefon": telefon, "email": email, "detaylar": detaylar, "tutar": f"{toplam_tutar:,.2f} TL"}
            try:
                requests.post(GOOGLE_SCRIPT_URL, json=veri)
            except:
                pass
            mail_gonder(email, ad_soyad, telefon, email, t_str, detaylar, toplam_tutar)
            st.success("Rezervasyon alındı!")
            st.balloons()

# ================= YÖNETİCİ PANELİ =================
elif menu == "Yönetici Paneli (Fiyat & Takvim)":
    st.title("🔒 Yönetici Paneli")
    password = st.text_input("Yönetici Şifresi", type="password")
    
    if password == "12345":
        st.success("Giriş Başarılı!")
        
        # Girişte ve her yenilemede verileri tazeleyelim
        f, k_list, k_dict = verileri_cek()
        st.session_state.prices_df = f
        st.session_state.closed_dates = k_list
        st.session_state.campaign_dates = k_dict

        if st.button("🔄 Verileri Şimdi Yenile"):
            st.rerun()

        tab1, tab2, tab3 = st.tabs(["💰 Fiyat Yönetimi", "📅 Kapalı Tarihler", "🎉 Kampanyalı Tarihler"])
        
        with tab1:
            edited_df = st.data_editor(st.session_state.prices_df, num_rows="dynamic", use_container_width=True)
            if st.button("Fiyatları Güncelle"):
                st.session_state.prices_df = edited_df
                try:
                    requests.post(GOOGLE_SCRIPT_URL, json={"islem": "fiyat_guncelle", "fiyatlar": edited_df.to_dict(orient="records")})
                    st.success("Fiyatlar güncellendi!")
                except Exception as ex:
                    st.error(f"Hata: {ex}")

        with tab2:
            st.subheader("Kapalı Tarih Ayarları")
            tek_tarih = st.date_input("Kapatılacak Tarih", value=date.today(), min_value=date.today())
            if st.button("Seçilen Günü Kapat"):
                if tek_tarih not in st.session_state.closed_dates:
                    st.session_state.closed_dates.append(tek_tarih)
                    google_kapali_guncelle()
                    st.success("Kapatıldı ve kaydedildi!")
                    st.rerun()
                else:
                    st.warning("Bu tarih zaten listede var.")

            st.markdown("### 🚫 Şu An Kapalı Olan Tarihler (Tablo Yönetimi):")
            if st.session_state.closed_dates:
                # Kapalı tarihleri DataFrame tablosuna dönüştürüyoruz
                df_kapali = pd.DataFrame({"Kapalı Tarihler": [d.strftime('%Y-%m-%d') for d in sorted(st.session_state.closed_dates)]})
                
                edited_kapali_df = st.data_editor(df_kapali, num_rows="dynamic", use_container_width=True, key="editor_kapali")
                
                if st.button("Kapalı Tarihleri Tablodan Güncelle / Sil"):
                    yeni_tarihler = []
                    for val in edited_kapali_df["Kapalı Tarihler"]:
                        if val:
                            try:
                                dt = datetime.strptime(str(val).split("T")[0].strip(), "%Y-%m-%d").date()
                                if dt not in yeni_tarihler:
                                    yeni_tarihler.append(dt)
                            except:
                                pass
                    st.session_state.closed_dates = yeni_tarihler
                    google_kapali_guncelle()
                    st.success("Kapalı tarihler tablodan güncellendi!")
                    st.rerun()
            else:
                st.info("Şu an kapalı tarih bulunmuyor.")

        with tab3:
            st.subheader("Kampanya Ayarları")
            indirim = st.number_input("İndirim Oranı (%)", min_value=1, max_value=99, value=10)
            k_tarih = st.date_input("Kampanya Tarihi", value=date.today(), min_value=date.today(), key="kamp_t")
            if st.button("Kampanya Ekle ve Kaydet"):
                st.session_state.campaign_dates[k_tarih] = int(indirim)
                google_kampanya_guncelle()
                st.success("Kampanya kaydedildi!")
                st.rerun()

            st.markdown("### 🏷️ Aktif Kampanyalar (Tablo Yönetimi):")
            if st.session_state.campaign_dates:
                # Kampanyaları DataFrame tablosuna dönüştürüyoruz
                kampanya_liste = [{"Tarih": d.strftime('%Y-%m-%d'), "İndirim (%)": oran} for d, oran in sorted(st.session_state.campaign_dates.items())]
                df_kampanya = pd.DataFrame(kampanya_liste)
                
                edited_kampanya_df = st.data_editor(df_kampanya, num_rows="dynamic", use_container_width=True, key="editor_kampanya")
                
                if st.button("Kampanyaları Tablodan Güncelle / Sil"):
                    yeni_kampanyalar = {}
                    for index, row in edited_kampanya_df.iterrows():
                        t_val = row["Tarih"]
                        o_val = row["İndirim (%)"]
                        if t_val:
                            try:
                                dt = datetime.strptime(str(t_val).split("T")[0].strip(), "%Y-%m-%d").date()
                                yeni_kampanyalar[dt] = int(o_val)
                            except:
                                pass
                    st.session_state.campaign_dates = yeni_kampanyalar
                    google_kampanya_guncelle()
                    st.success("Kampanyalar tablodan güncellendi!")
                    st.rerun()
            else:
                st.info("Aktif kampanya bulunmuyor.")
    elif password != "":
        st.error("Hatalı Şifre!")