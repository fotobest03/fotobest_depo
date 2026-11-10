import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Teklif ve Fiyat Yönetimi", page_icon="📸", layout="centered")

# --- SESSION STATE (Bellek Yönetimi) ---
if "prices_df" not in st.session_state:
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

# --- UYGULAMA MENÜSÜ ---
menu = st.sidebar.radio("Sayfa Seçin", ["Müşteri Teklif Formu", "Yönetici Paneli (Fiyat & Takvim)"])

# ==========================================
# 1. MÜŞTERİ TEKLİF FORMU
# ==========================================
if menu == "Müşteri Teklif Formu":
    st.title("📸 Çekim & Paket Teklif Formu")
    
    # Kapak Görseli
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
        
        # Geçmiş tarihler engellendi (min_value=date.today())
        rezervasyon_tarihi = st.date_input("Çekim Tarihi Seçiniz", value=date.today(), min_value=date.today())

        # Seçilen tarihin kapalı olup olmadığını kontrol et
        tarih_kapali_mi = rezervasyon_tarihi in st.session_state.closed_dates
        if tarih_kapali_mi:
            st.error(f"⚠️ Seçtiğiniz tarih ({rezervasyon_tarihi.strftime('%d.%m.%Y')}) yönetici tarafından kapatılmıştır/doludur. Lütfen başka bir tarih seçiniz.")

        st.subheader("🎁 Paket ve Çekim Seçenekleri")
        
        album_opts = df_prices[df_prices['Kategori'] == 'Aile Albümü']
        tablo_opts = df_prices[df_prices['Kategori'] == 'Tablo Seçimi']
        poz_opts = df_prices[df_prices['Kategori'] == 'Poz Sayısı']
        mekan_opts = df_prices[df_prices['Kategori'] == 'Çekim Mekanı']
        klip_opts = df_prices[df_prices['Kategori'] == 'Dış Çekim Klibi']

        secilen_album = st.selectbox("Aile Albümü", album_opts['Secenek'].tolist())
        secilen_tablo = st.selectbox("Tablo Seçimi", tablo_opts['Secenek'].tolist())
        secilen_poz = st.selectbox("Albüm İçi Poz Sayısı", poz_opts['Secenek'].tolist())
        secilen_mekan = st.selectbox("Çekim Mekanı", mekan_opts['Secenek'].tolist())
        secilen_klip = st.radio("Dış Çekim Klibi İstiyorum", klip_opts['Secenek'].tolist())

        # Fiyat Hesaplama
        try:
            f_album = float(album_opts[album_opts['Secenek'] == secilen_album]['Fiyat'].values[0])
            f_tablo = float(tablo_opts[tablo_opts['Secenek'] == secilen_tablo]['Fiyat'].values[0])
            f_poz = float(poz_opts[poz_opts['Secenek'] == secilen_poz]['Fiyat'].values[0])
            f_mekan = float(mekan_opts[mekan_opts['Secenek'] == secilen_mekan]['Fiyat'].values[0])
            f_klip = float(klip_opts[klip_opts['Secenek'] == secilen_klip]['Fiyat'].values[0])
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
                st.success(f"Talebiniz başarıyla alındı! Seçilen Çekim Tarihi: {rezervasyon_tarihi.strftime('%d.%m.%Y')}")

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
                st.success("Fiyatlar başarıyla güncellendi!")

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
            
            else: # Tarih Aralığı Kapat
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