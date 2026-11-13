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


# --- AYARLAR VE GİZLİ BİLGİLER ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxPWHCbD7cE9beiKjX5dmZTAzu-ZcErHpjLOhwbWy3lLIM77aXZcrLm8eqs8oB136oL/exec"
GMAIL_KULLANICI = "afotobest@gmail.com"
GMAIL_SIFRE = "byyewfosgesogdft"

# --- YARDIMCI TARİH DÖNÜŞTÜRÜCÜ FONKSİYON ---
def tarihi_duzenle(tarih_str):
    if not tarih_str:
        return ""
    s = str(tarih_str).strip()
    try:
        # Eğer zaten YYYY-MM-DD formatındaysa
        if len(s) >= 10 and s[4] == '-' and s[7] == '-':
            return s[:10]
        
        # 'Fri Nov 20 2026 00:00:00 GMT...' formatını parse etme
        temiz_parca = " ".join(s.split()[:4]) 
        dt = datetime.strptime(temiz_parca, "%a %b %d %Y")
        return dt.strftime("%Y-%m-%d")
    except:
        try:
            dt = pd.to_datetime(s)
            return dt.strftime("%Y-%m-%d")
        except:
            return s.split("T")[0].strip()

# --- GOOGLE E-TABLODAN VERİ ÇEKME ---
def verileri_tablodan_getir():
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
    kapali_df = pd.DataFrame(columns=["Tarih"])
    kampanya_df = pd.DataFrame(columns=["Tarih", "Indirim"])
    
    try:
        res = requests.get(GOOGLE_SCRIPT_URL, timeout=10)
        data = res.json()
        
        # 1. Fiyatlar
        if "fiyatlar" in data and data["fiyatlar"]:
            fiyat_df = pd.DataFrame(data["fiyatlar"])
            
        # 2. Kapalı Tarihler
        if "kapali_tarihler" in data and data["kapali_tarihler"]:
            temiz_kapali = []
            for t in data["kapali_tarihler"]:
                formatli_tarih = tarihi_duzenle(t)
                if formatli_tarih:
                    temiz_kapali.append({"Tarih": formatli_tarih})
            if temiz_kapali:
                kapali_df = pd.DataFrame(temiz_kapali)
                
        # 3. Kampanyalar
        if "kampanyalar" in data and data["kampanyalar"]:
            temiz_kampanya = []
            for k in data["kampanyalar"]:
                if isinstance(k, dict) and "tarih" in k:
                    formatli_tarih = tarihi_duzenle(k["tarih"])
                    if formatli_tarih:
                        temiz_kampanya.append({
                            "Tarih": formatli_tarih, 
                            "Indirim": int(k.get("oran", 0))
                        })
            if temiz_kampanya:
                kampanya_df = pd.DataFrame(temiz_kampanya)
                
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        
    return fiyat_df, kapali_df, kampanya_df

# Oturum başlatma
if "prices_df" not in st.session_state:
    f_df, k_df, kam_df = verileri_tablodan_getir()
    st.session_state.prices_df = f_df
    st.session_state.kapali_df = k_df
    st.session_state.kampanya_df = kam_df

def get_closed_dates_list():
    lst = []
    if "kapali_df" in st.session_state and not st.session_state.kapali_df.empty:
        for val in st.session_state.kapali_df["Tarih"]:
            if val:
                try:
                    dt = datetime.strptime(str(val).split("T")[0].strip(), "%Y-%m-%d").date()
                    if dt not in lst: lst.append(dt)
                except: pass
    return lst

def get_campaign_dict():
    dct = {}
    if "kampanya_df" in st.session_state and not st.session_state.kampanya_df.empty:
        for index, row in st.session_state.kampanya_df.iterrows():
            t_val = row["Tarih"]
            o_val = row["Indirim"]
            if t_val and o_val is not None:
                try:
                    dt = datetime.strptime(str(t_val).split("T")[0].strip(), "%Y-%m-%d").date()
                    dct[dt] = int(o_val)
                except: pass
    return dct

def takvim_verilerini_kaydet():
    # Streamlit tablosundaki mükerrer (aynı) tarihleri temizle
    if not st.session_state.kapali_df.empty:
        st.session_state.kapali_df['Tarih'] = st.session_state.kapali_df['Tarih'].astype(str).str.split("T").str[0].str.strip()
        st.session_state.kapali_df = st.session_state.kapali_df.drop_duplicates(subset=["Tarih"]).reset_index(drop=True)

    if not st.session_state.kampanya_df.empty:
        st.session_state.kampanya_df['Tarih'] = st.session_state.kampanya_df['Tarih'].astype(str).str.split("T").str[0].str.strip()
        st.session_state.kampanya_df = st.session_state.kampanya_df.drop_duplicates(subset=["Tarih"]).reset_index(drop=True)

    kapali_listesi = []
    if not st.session_state.kapali_df.empty:
        for val in st.session_state.kapali_df["Tarih"]:
            if val and val != "nan":
                t_str = str(val).split("T")[0].strip()
                if t_str and t_str not in kapali_listesi:
                    kapali_listesi.append(t_str)
                    
    kampanya_listesi = []
    eklenen_kampanya_tarihleri = set()
    if not st.session_state.kampanya_df.empty:
        for index, row in st.session_state.kampanya_df.iterrows():
            t_val = row["Tarih"]
            o_val = row["Indirim"]
            if t_val and str(t_val) != "nan":
                t_str = str(t_val).split("T")[0].strip()
                # Aynı kampanya tarihinden birden fazla varsa sadece ilkini al
                if t_str and t_str not in eklenen_kampanya_tarihleri:
                    eklenen_kampanya_tarihleri.add(t_str)
                    kampanya_listesi.append({
                        "tarih": t_str, 
                        "oran": o_val
                    })
    try:
        requests.post(GOOGLE_SCRIPT_URL, json={
            "islem": "takvim_guncelle",
            "kapali_tarihler": kapali_listesi,
            "kampanyalar": kampanya_listesi
        })
    except: pass

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

    kampanya_dict = get_campaign_dict()
    closed_lst = get_closed_dates_list()

    if kampanya_dict:
        kampanya_metni = "✨ **Fiyatlarımızın Yüksek Olduğu Günler:**\n"
        for d, oran in sorted(kampanya_dict.items()):
            if d >= date.today():
                kampanya_metni += f"- 📅 **{d.strftime('%d.%m.%Y')}** tarihde **%{oran} zamlı fiyat!**\n"
        st.info(kampanya_metni)

    rezervasyon_tarihi = st.date_input("Çekim Tarihi Seçiniz", value=date.today(), min_value=date.today())
    tarih_kapali_mi = rezervasyon_tarihi in closed_lst
    kampanya_orani = kampanya_dict.get(rezervasyon_tarihi, 0)

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
        toplam_tutar = ham_tutar * (1+kampanya_orani / 100)
        st.success(f"Bu tarihte **%{kampanya_orani} daha yüksek** fiyat!")

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
            except: pass
            mail_gonder(email, ad_soyad, telefon, email, t_str, detaylar, toplam_tutar)
            st.success("Rezervasyon alındı!")
            st.balloons()

# ================= YÖNETİCİ PANELİ =================
elif menu == "Yönetici Paneli (Fiyat & Takvim)":
    st.title("🔒 Yönetici Paneli")
    password = st.text_input("Yönetici Şifresi", type="password")
    
    if password == "12345":
        st.success("Giriş Başarılı!")
        
        if st.button("🔄 E-Tablodan Verileri Al / Yenile"):
            f_df, k_df, kam_df = verileri_tablodan_getir()
            st.session_state.prices_df = f_df
            st.session_state.kapali_df = k_df
            st.session_state.kampanya_df = kam_df
            st.success("Tüm veriler Google E-Tablodan başarıyla çekildi ve güncellendi!")
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
            tek_tarih = st.date_input("Kapatılacak Tarih", value=date.today(), min_value=date.today(), key="kap_tek_gun")
            if st.button("Seçilen Günü Kapat"):
                t_str = tek_tarih.strftime('%Y-%m-%d')
                if t_str not in st.session_state.kapali_df["Tarih"].values:
                    yeni_satir = pd.DataFrame([{"Tarih": t_str}])
                    st.session_state.kapali_df = pd.concat([st.session_state.kapali_df, yeni_satir], ignore_index=True)
                    takvim_verilerini_kaydet()
                    st.success("Kapatıldı ve E-Tabloya kaydedildi!")
                    st.rerun()
                else:
                    st.warning("Bu tarih zaten listede var.")

            st.markdown("### Şu An Kapalı Olan Tarihler (Tablo Yönetimi):")
            edited_kapali_df = st.data_editor(st.session_state.kapali_df, num_rows="dynamic", use_container_width=True, key="editor_kapali")
            
            # Fiyat Yönetimi ile birebir aynı çalışma mantığı
            if st.button("Kapalı Tarihleri Güncelle"):
                st.session_state.kapali_df = edited_kapali_df
                try:
                    takvim_verilerini_kaydet()
                    st.success("Kapalı tarihler güncellendi!")
                except Exception as ex:
                    st.error(f"Hata: {ex}")

        with tab3:
            st.subheader("Kampanya Ayarları")
            indirim = st.number_input("İndirim Oranı (%)", min_value=1, max_value=99, value=10, key="kamp_ind")
            k_tarih = st.date_input("Kampanya Tarihi", value=date.today(), min_value=date.today(), key="kamp_tarih_sec")
            
            if st.button("Kampanya Ekle ve Kaydet"):
                t_str = k_tarih.strftime('%Y-%m-%d')
                yeni_satir = pd.DataFrame([{"Tarih": t_str, "Indirim": int(indirim)}])
                st.session_state.kampanya_df = pd.concat([st.session_state.kampanya_df, yeni_satir], ignore_index=True)
                takvim_verilerini_kaydet()
                st.success("Kampanya kaydedildi ve E-Tabloya işlendi!")
                st.rerun()

            st.markdown("### Aktif Kampanyalı Tarihler ve İndirim Oranları (Tablo Yönetimi):")
            if "kampanya_df" not in st.session_state or st.session_state.kampanya_df.empty:
                st.session_state.kampanya_df = pd.DataFrame(columns=["Tarih", "Indirim"])
                
            edited_kampanya_df = st.data_editor(st.session_state.kampanya_df, num_rows="dynamic", use_container_width=True, key="editor_kampanya")
            
            # Fiyat Yönetimi ile birebir aynı çalışma mantığı
            if st.button("Kampanyaları Güncelle"):
                st.session_state.kampanya_df = edited_kampanya_df
                try:
                    takvim_verilerini_kaydet()
                    st.success("Kampanyalar güncellendi!")
                except Exception as ex:
                    st.error(f"Hata: {ex}")
                
    elif password != "":
        st.error("Hatalı Şifre!")