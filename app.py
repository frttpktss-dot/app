import streamlit as st
import openai
import time

# -------------------------------
# Uygulama Başlığı ve Tema Ayarı
# -------------------------------
st.set_page_config(page_title="RoutineSwap", layout="centered")

# Koyu tema için CSS
dark_css = """
<style>
body {
    background-color: #0E1117;
    color: #FAFAFA;
}
.stButton>button {
    color: white;
    border-radius: 8px;
    height: 60px;
    font-size: 18px;
    font-weight: bold;
    width: 100%;
}
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)

# -------------------------------
# Sidebar: API Key Girişi
# -------------------------------
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if api_key:
    openai.api_key = api_key

st.title("🌙 RoutineSwap")

# -------------------------------
# Ana Ekran Butonları
# -------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    breath = st.button("Bir Nefes Al", key="breath", 
                       help="Sakinleşmek için tıkla",
                       use_container_width=True)
    st.markdown(
        "<style>div[data-testid='stButton'] button[kind='secondary']{background-color:#8A9A7B;}</style>",
        unsafe_allow_html=True
    )

with col2:
    stop = st.button("Dur", key="stop",
                     help="Durmak için tıkla",
                     use_container_width=True)
    st.markdown(
        "<style>div[data-testid='stButton'] button[kind='secondary']{background-color:#D4A5A5;}</style>",
        unsafe_allow_html=True
    )

with col3:
    escape = st.button("Beni Buradan Çıkar", key="escape",
                       help="Kurtulmak için tıkla",
                       use_container_width=True)
    st.markdown(
        "<style>div[data-testid='stButton'] button[kind='secondary']{background-color:#1A8A9A;}</style>",
        unsafe_allow_html=True
    )

# -------------------------------
# KAI Mantığı: Buton Tıklama
# -------------------------------
def kai_response(trigger):
    if not api_key:
        return "⚠️ Lütfen önce API anahtarını gir."
    prompt = f"""
    Sen KAI adında bir AI koçsun. Kullanıcıya 'Fırat' diye hitap et.
    {trigger} butonuna bastı. Ona sigara, stres yemeği veya sosyal medya krizini atlatması için 1-2 cümlelik destek ver.
    Ardından 3 dakikalık bir mikro-görev öner.
    Cümlenin sonunu tam olarak şu ifadeyle bitir: "Hazırsan 'Başla' butonuna bas, geri sayımı başlatıyorum".
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Sen destekleyici bir koçsun."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"API hatası: {e}"

message = None
if breath:
    message = kai_response("Bir Nefes Al")
elif stop:
    message = kai_response("Dur")
elif escape:
    message = kai_response("Beni Buradan Çıkar")

if message:
    st.markdown(f"### 🤖 KAI'nin Mesajı:\n{message}")

# -------------------------------
# Sayaç: 3 Dakika (180 saniye)
# -------------------------------
if st.button("Başla"):
    countdown_placeholder = st.empty()
    for i in range(180, 0, -1):
        mins, secs = divmod(i, 60)
        countdown_placeholder.markdown(f"## ⏳ Kalan Süre: {mins:02d}:{secs:02d}")
        time.sleep(1)
    countdown_placeholder.markdown("## ✅ Süre Doldu! Harika iş çıkardın Fırat 🎉")
