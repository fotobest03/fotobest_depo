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
        st.session_state.prices_df = pd.DataFrame([
            {"Kategori": "Ana Albüm", "Secenek": "30 x 60 Mat Albüm", "Fiyat": 3500},
            {"Kategori": "Ana Albüm", "Secenek": "30 x 76 Mat Albüm", "Fiyat": 4500},
            {"Kategori": "Aile Albümü", "Secenek": "2'li Albüm", "Fiyat": 1500},
            {"Kategori": "Tablo Seçimi", "Secenek": "30 x 40 Çerçeveli", "Fiyat": 2000},
            {"Kategori": "Poz Sayısı", "Secenek": "40", "Fiyat": 1000},
            {"Kategori": "Çekim Mekanı", "Secenek": "Ayazin", "Fiyat": 2500},
            {"Kategori": "Dış Çekim Klibi", "Secenek": "Evet", "Fiyat": 3000},
            {"Kategori": "Dış Çekim Klibi", "Secenek": "Hayır", "Fiyat": 0}
        ])

if "closed_dates" not in st.session_state:
    st.session_state.closed_dates = []

if "campaign_dates" not in st.session_state:
    st.session_state.campaign_dates = {}

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
        
        Ödenecek Tutar: {toplam_tutar:,.2f} TL
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

    st.subheader("👤 Kişisel Bilgiler")
    ad_soyad = st.text_input("Ad Soyad *")
    telefon = st.text_input("Telefon *")
    email = st.text_input("E-Posta Adresi *")

    st.subheader("📅 Rezervasyon Tarihi")

    # --- KAMPANYALI TARİHLERİ MÜŞTERİYE GÖSTERME ALANI ---
    if st.session_state.campaign_dates:
        kampanya_metni = "✨ **İndirimli Kampanyalı Günlerimiz:**\n"
        for d, oran in sorted(st.session_state.campaign_dates.items()):
            if d >= date.today(): # Geçmiş tarihleri göstermeyelim
                kampanya_metni += f"- 📅 **{d.strftime('%d.%m.%Y')}** tarihine özel **%{oran} İndirim!**\n"
        st.info(kampanya_metni)

    rezervasyon_tarihi = st.date_input("Çekim Tarihi Seçiniz", value=date.today(), min_value=date.today())

    # Kontroller
    tarih_kapali_mi = rezervasyon_tarihi in st.session_state.closed_dates
    kampanya_orani = st.session_state.campaign_dates.get(rezervasyon_tarihi, 0)

    if tarih_kapali_mi:
        st.error(f"⚠️ Seçtiğiniz tarih ({rezervasyon_tarihi.strftime('%d.%m.%Y')}) yönetici tarafından kapatılmıştır/doludur.")

    st.subheader("🎁 Paket ve Çekim Seçenekleri")
    
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

    # Fiyat Hesaplama
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
    toplam_tutar = ham_tutar  # Varsayılan tutar

    # Kampanya İndirimi Uygulama
    if kampanya_orani > 0:
        indirimli_tutar = ham_tutar * (1 - kampanya_orani / 100)
        st.success(f"🎉 Kampanyalı Tarih! Bu tarihe özel **%{kampanya_orani} indirim** tanımlanmıştır.")
        st.markdown(f"~~Normal Tutar: {ham_tutar:,.2f} TL~~")
        toplam_tutar = indirimli_tutar
        kampanya_detay_str = f" (%{kampanya_orani} Kampanya İndirimli)"
    else:
        kampanya_detay_str = " (Normal Fiyat)"

    st.markdown(f"### **Toplam Tutar: {toplam_tutar:,.2f} TL**")

    submitted = st.button("Teklifi Gönder ve Kaydet")

    if submitted:
        if tarih_kapali_mi:
            st.error("❌ Seçtiğiniz tarih kapalı olduğu için rezervasyon oluşturulamaz!")
        elif not ad_soyad or not telefon or not email:
            st.warning("Lütfen zorunlu kişisel bilgileri doldurun.")
        else:
            tarih_str = rezervasyon_tarihi.strftime('%d.%m.%Y')
            detaylar_str = f"Ana Albüm: {secilen_ana_album} | Aile Albümü: {secilen_album} | Tablo: {secilen_tablo} | Poz: {secilen_poz} | Mekan: {secilen_mekan} | Klip: {secilen_klip}{kampanya_detay_str}"
            
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
        
        tab1, tab2, tab3 = st.tabs(["💰 Fiyat Yönetimi", "📅 Kapalı Tarihler", "🎉 Kampanyalı Tarihler"])
        
        with tab1:
            st.subheader("Ürün ve Fiyat Tablosu")
            edited_df = st.data_editor(st.session_state.prices_df, num_rows="dynamic", use_container_width=True)
            
            if st.button("Fiyatları Güncelle"):
                st.session_state.prices_df = edited_df
                
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
                    baslangic_tarihi = st.date_input("Başlangıç Tarihi", value=date.today(), min_value=date.today(), key="kapat_bas")
                with col2:
                    bitis_tarihi = st.date_input("Bitiş Tarihi", value=date.today(), min_value=date.today(), key="kapat_bit")
                
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

        with tab3:
            st.subheader("🎉 Kampanyalı Tarih ve İndirim Oranı Belirleme")
            kampanya_turu = st.radio("Kampanya Ekleme Yöntemi", ["Tek Gün Kampanya", "Tarih Aralığı Kampanya"])
            indirim_orani = st.number_input("İndirim Oranı (%)", min_value=1, max_value=99, value=10, step=1)
            
            if kampanya_turu == "Tek Gün Kampanya":
                k_tek_tarih = st.date_input("Kampanyalı Tarih Seçin", value=date.today(), min_value=date.today(), key="kamp_tek")
                if st.button("Kampanya Ekle (Tek Gün)"):
                    st.session_state.campaign_dates[k_tek_tarih] = indirim_orani
                    st.success(f"{k_tek_tarih.strftime('%d.%m.%Y')} tarihi için %{indirim_orani} indirim tanımlandı!")
            else:
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    k_bas = st.date_input("Başlangıç Tarihi", value=date.today(), min_value=date.today(), key="kamp_bas")
                with col_k2:
                    k_bit = st.date_input("Bitiş Tarihi", value=date.today(), min_value=date.today(), key="kamp_bit")
                
                if st.button("Kampanya Ekle (Tarih Aralığı)"):
                    if k_bas > k_bit:
                        st.error("Başlangıç tarihi bitiş tarihinden sonra olamaz!")
                    else:
                        sayac = 0
                        curr = k_bas
                        while curr <= k_bit:
                            st.session_state.campaign_dates[curr] = indirim_orani
                            sayac += 1
                            curr += timedelta(days=1)
                        st.success(f"{k_bas.strftime('%d.%m.%Y')} - {k_bit.strftime('%d.%m.%Y')} arasındaki {sayac} gün için %{indirim_orani} indirim tanımlandı!")

            st.write("---")
            st.markdown("### 🏷️ Aktif Kampanyalı Tarihler ve İndirim Oranları:")
            if st.session_state.campaign_dates:
                for d, oran in sorted(st.session_state.campaign_dates.items()):
                    kc1, kc2 = st.columns([3, 1])
                    with kc1:
                        st.write(f"🎉 **{d.strftime('%d.%m.%Y')}** ➔ **%{oran} İndirim**")
                    with kc2:
                        if st.button("Kaldır", key=f"kampanya_sil_{d}"):
                            del st.session_state.campaign_dates[d]
                            st.rerun()
            else:
                st.info("Şu an tanımlı aktif bir kampanyalı tarih bulunmuyor.")

    elif password != "":
        st.error("Hatalı Şifre!")