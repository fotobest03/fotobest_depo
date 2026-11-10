import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR VE GİZLİ BİLGİLER ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwkniKw0mYQUiVpDjupS6eNg9ZlOSGzk8vTbDsJFKPkCbEl3tHKts6cbDNqxIsk2EQ/exec"
GMAIL_KULLANICI = "afotobest@gmail.com"
GMAIL_SIFRE = "byyewfosgesogdft"

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Teklif ve Fiyat Yönetimi", page_icon="📸", layout="centered")

# --- GOOGLE SHEETS'TEN FİYATLARI ÇEKME ---
if "prices_df" not in st.session_state:
    try:
        response = requests.get(GOOGLE_SCRIPT_URL)
        data = response.json()
        if data and isinstance(data, list):
            st.session_state.prices_df = pd.DataFrame(data)
        else:
            raise Exception("Boş veri")
    except:
        # İnternetten çekemezse varsayılan yedek fiyatlar
        st.session_state.prices_df = pd.DataFrame([
            {"Kategori": "Aile Albümü", "Secenek": "2'li Albüm", "Fiyat": 1500},
            {"Kategori": "Tablo Seçimi", "Secenek": "30 x 40 Çerçeveli", "Fiyat": 2000},
            {"Kategori": "Poz Sayısı", "Secenek": "40", "Fiyat": 1000},
            {"Kategori": "Çekim Mekanı", "Secenek": "Ayazin", "Fiyat": 2500},
            {"Kategori": "Dış Çekim Klibi", "Secenek": "Evet", "Fiyat": 3000},
            {"Kategori": "Dış Çekim Klibi", "Secenek": "Hayır", "Fiyat": 0}
        ])

if "closed_dates" not in st.session_state:
    st.session_state.closed_dates = []

# --- E-POSTA GÖNDERME FONKSİYONU ---
def mail_gonder(alici_eposta, ad_soyad, telefon, email, tarih_str, detaylar, toplam_tutar):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_KULLANICI
        msg['To'] = GMAIL_KULLANICI 
        msg['Subject'] = f"📷 Yeni Rezervasyon Talebi: {ad_soyad}"

        govde = f"""
        Yeni bir rezervasyon talebi alındı!
        
        Müşteri Bilgileri:
        - Ad Soyad: {ad_soyad}
        - Telefon: {telefon}
        - E-Posta: {email}
        - Çekim Tarihi: {tarih_str}
        
        Seçilen Paket Detayları:
        {detaylar}
        
        Toplam Tutar: {toplam_tutar:,.2f} TL
        """
        msg.attach(MIMEText(govde, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_KULLANICI, GMAIL_SIFRE)
        server.sendmail(GMAIL_KULLANICI, [GMAIL_KULLANICI, alici_eposta], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")
        return False

# --- UYGULAMA MENÜSÜ ---
menu = st.sidebar.radio("Sayfa Seçin", ["Müşteri Teklif Formu", "Yönetici Paneli (Fiyat & Takvim)"])

# ==========================================
# 1. MÜŞTERİ TEKLİF FORMU
# ==========================================
if menu == "Müşteri Teklif Formu":
    st.title("📸 Çekim & Paket Teklif Formu")
    
    try:
        st.image("kapak_foto.jpg", use_container_width=True)
    except:
        pass 
    
    st.write("Lütfen rezervasyon tarihinizi ve almak istediğiniz hizmet detaylarını seçiniz.")

    df_prices = st.session_state.prices_df

    with st.form("musteri_formu"):
        st.subheader("👤 Kişisel Bilgiler")
        ad_soyad = st.text_input("Ad Soyad *")
        telefon = st.text_input("Telefon *")
        email = st.text_input("E-Posta Adresi *")

        st.subheader("📅 Rezervasyon Tarihi")
        rezervasyon_tarihi = st.date_input("Çekim Tarihi Seçiniz", value=date.today(), min_value=date.today())

        tarih_kapali_mi = rezervasyon_tarihi in st.session_state.closed_dates
        if tarih_kapali_mi:
            st.error(f"⚠️ Seçtiğiniz tarih ({rezervasyon_tarihi.strftime('%d.%m.%Y')}) yönetici tarafından kapatılmıştır/doludur.")

        st.subheader("🎁 Paket ve Çekim Seçenekleri")
        
        album_opts = df_prices[df_prices['Kategori'] == 'Aile Albümü']
        tablo_opts = df_prices[df_prices['Kategori'] == 'Tablo Seçimi']
        poz_opts = df_prices[df_prices['Kategori'] == 'Poz Sayısı']
        mekan_opts = df_prices[df_prices['Kategori'] == 'Çekim Mekanı']
        klip_opts = df_prices[df_prices['Kategori'] == 'Dış Çekim Klibi']

        secilen_album = st.selectbox("Aile Albümü", album_opts['Secenek'].tolist()) if not album_opts.empty else ""
        secilen_tablo = st.selectbox("Tablo Seçimi", tablo_opts['Secenek'].tolist()) if not tablo_opts.empty else ""
        secilen_poz = st.selectbox("Albüm İçi Poz Sayısı", poz_opts['Secenek'].tolist()) if not poz_opts.empty else ""
        secilen_mekan = st.selectbox("Çekim Mekanı", mekan_opts['Secenek'].tolist()) if not mekan_opts.empty else ""
        secilen_klip = st.radio("Dış Çekim Klibi İstiyorum", klip_opts['Secenek'].tolist()) if not klip_opts.empty else ""

        # Fiyat Hesaplama
        try:
            f_album = float(album_opts[album_opts['Secenek'] == secilen_album]['Fiyat'].values[0]) if secilen_album else 0.0
            f_tablo = float(tablo_opts[tablo_opts['Secenek'] == secilen_tablo]['Fiyat'].values[0]) if secilen_tablo else 0.0
            f_poz = float(poz_opts[poz_opts['Secenek'] == secilen_poz]['Fiyat'].values[0]) if secilen_poz else 0.0
            f_mekan = float(mekan_opts[mekan_opts['Secenek'] == secilen_mekan]['Fiyat'].values[0]) if secilen_mekan else 0.0
            f_klip = float(klip_opts[klip_opts['Secenek'] == secilen_klip]['Fiyat'].values[0]) if secilen_klip else 0.0
        except:
            f_album = f_tablo = f_poz = f_mekan = f_klip = 0.0

        toplam_tutar = f_album + f_tablo + f_poz + f_mekan + f_klip

        st.markdown(f"### **Toplam Tutar: {toplam_tutar:,.2f} TL**")
        
        submitted = st.form_submit_button("Teklifi Gönder ve Kaydet")

        if submitted:
            if tarih_kapali_mi:
                st.error("❌ Seçtiğiniz tarih kapalı olduğu için rezervasyon oluşturulamaz!")
            elif not ad_soyad or not telefon or not email:
                st.warning("Lütfen zorunlu kişisel bilgileri doldurun.")
            else:
                tarih_str = rezervasyon_tarihi.strftime('%d.%m.%Y')
                detaylar_str = f"Albüm: {secilen_album} | Tablo: {secilen_tablo} | Poz: {secilen_poz} | Mekan: {secilen_mekan} | Klip: {secilen_klip}"
                
                veri = {
                    "tarih": tarih_str,
                    "ad_soyad": ad_soyad,
                    "telefon": telefon,
                    "email": email,
                    "detaylar": detaylar_str,
                    "tutar": f"{toplam_tutar:,.2f} TL"
                }
                
                try:
                    requests.post(GOOGLE_SCRIPT_URL, json=veri)
                except:
                    pass

                mail_gonder(email, ad_soyad, telefon, email, tarih_str, detaylar_str, toplam_tutar)

                st.success(f"Talebiniz başarıyla alındı! Seçilen Çekim Tarihi: {tarih_str}")
                st.balloons()

# ==========================================
# 2. YÖNETİCİ FİYAT & TAKVİM YÖNETİM PANELİ
# ==========================================
elif menu == "Yönetici Paneli (Fiyat & Takvim)":
    st.title("🔒 Yönetici Paneli")
    
    password = st.text_input("Yönetici Şifresi", type="password")
    
    if password == "12345":
        st.success("Giriş Başarılı!")
        
        tab1, tab2 = st.tabs(["💰 Fiyat Yönetimi", "📅 Kapalı / Dolu Tarih Yönetimi"])
        
        with tab1:
            st.subheader("Ürün ve Fiyat Tablosu")
            edited_df = st.data_editor(st.session_state.prices_df, num_rows="dynamic", use_container_width=True)
            
            if st.button("Fiyatları Güncelle"):
                st.session_state.prices_df = edited_df
                
                # Google E-Tabloya Gönderme
                fiyat_listesi = edited_df.to_dict(orient="records")
                guncelleme_verisi = {
                    "islem": "fiyat_guncelle",
                    "fiyatlar": fiyat_listesi
                }
                try:
                    res = requests.post(GOOGLE_SCRIPT_URL, json=guncelleme_verisi)
                    if res.status_code == 200:
                        st.success("Fiyatlar hem bellekte hem de Google E-Tabloda başarıyla güncellendi!")
                    else:
                        st.warning("Fiyatlar güncellendi ancak E-Tabloya yazılırken bir hata oluştu.")
                except Exception as ex:
                    st.error(f"Bağlantı hatası: {ex}")

        with tab2:
            st.subheader("Çekime Kapalı / Dolu Tarih Ayarları")
            kapatma_turu = st.radio("Kapatma Yöntemi Seçin", ["Tek Gün Kapat", "Tarih Aralığı Kapat"])
            
            if kapatma_turu == "Tek Gün Kapat":
                tek_tarih = st.date_input("Kapatılacak Tarih", value=date.today(), min_value=date.today())
                if st.button("Seçilen Günü Kapat"):
                    if tek_tarih not in st.session_state.closed_dates:
                        st.session_state.closed_dates.append(tek_tarih)
                        st.success(f"{tek_tarih.strftime('%d.%m.%Y')} tarihi kapalı tarihlere eklendi.")
                    else:
                        st.warning("Bu tarih zaten kapalı listesinde bulunuyor.")
            
            else: 
                col1, col2 = st.columns(2)
                with col1:
                    baslangic_tarihi = st.date_input("Başlangıç Tarihi", value=date.today(), min_value=date.today())
                with col2:
                    bitis_tarihi = st.date_input("Bitiş Tarihi", value=date.today(), min_value=date.today())
                
                if st.button("Tarih Aralığını Kapat"):
                    if baslangic_tarihi > bitis_tarihi:
                        st.error("Başlangıç tarihi bitiş tarihinden sonra olamaz!")
                    else:
                        eklenen_sayisi = 0
                        curr = baslangic_tarihi
                        while curr <= bitis_tarihi:
                            if curr not in st.session_state.closed_dates:
                                st.session_state.closed_dates.append(curr)
                                eklenen_sayisi += 1
                            curr += timedelta(days=1)
                        st.success(f"{baslangic_tarihi.strftime('%d.%m.%Y')} ile {bitis_tarihi.strftime('%d.%m.%Y')} arasındaki {eklenen_sayisi} yeni tarih kapalı listesine eklendi.")

            st.write("---")
            st.markdown("### 🚫 Şu An Kapalı Olan Tüm Tarihler:")
            if st.session_state.closed_dates:
                for d in sorted(st.session_state.closed_dates):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"📌 {d.strftime('%d.%m.%Y')}")
                    with c2:
                        if st.button("Aç / Kaldır", key=str(d)):
                            st.session_state.closed_dates.remove(d)
                            st.rerun()
            else:
                st.info("Şu an kapalı/rezerve edilmiş özel bir tarih bulunmuyor.")

    elif password != "":
        st.error("Hatalı Şifre!")