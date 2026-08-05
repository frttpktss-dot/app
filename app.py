import streamlit as st
from openai import OpenAI
import time

# Uygulama Başlığı ve Sayfa Ayarı
st.set_page_config(page_title="RoutineSwap", layout="centered")

# Koyu Tema Tasarımı (CSS)
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

# Yan Menü: OpenAI API Key Girişi
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

st.title("🌙 RoutineSwap")

if not api_key:
    st.warning("Lütfen devam etmek için sol yan menüden OpenAI API anahtarınızı girin.")
    st.stop()

# OpenAI İstemcisini Başlat
client = OpenAI(api_key=api_key)

# Session State Hazırlığı
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = None
if "kai_response" not in st.session_state:
    st.session_state.kai_response = None

# Modlar ve Sistem Promptları
prompts = {
    "Sigara Bırakma": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının sigara/elektronik sigara krizini atlatması için en yakın dostu, mentörü ve sakinleştirici limanısın. Asla resmi konuşma, samimi ve sıcak bir Türkçe kullan. Kullanıcıya Fırat adıyla hitap et. Kriz anındaki gerginliği 1-2 kısa cümleyle dostça göğüsledikten sonra, hemen o anki duygu durumuna özel, elini/zihnini oyalayacak 3 dakikalık net bir mikro-görev ver. Görevi verdikten sonra cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" şeklinde bitir.',
    "Stres Yemeği": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının duygusal yeme krizlerini ve anlık tatlı/atıştırmalık krizlerini yöneten samimi bir dostsun. Asla yargılayıcı konuşma. Kullanıcıya Fırat adıyla hitap et. O anki mutsuzluk, stres veya can sıkıntısı hissini anladığını belirt. Kendisini mutfağa veya buzdolabına yönlendirmek yerine, o an durmasını sağlayacak 3 dakikalık pürüzsüz bir zihinsel değişim görevi ver. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.',
    "Sosyal Medya": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının telefonda amaçsızca kaydırma (doomscrolling) yapmasını ve dijital bağımlılık krizlerini engellemek için tasarlanmış gerçekçi bir dostsun. Kullanıcıya Fırat adıyla hitap et. Ekran başında harcanan zamanın farkına varmasını sağla ama bunu dostça yap. Telefonu hemen masaya ters bırakmasını veya 3 dakika boyunca ekrandan tamamen uzaklaşıp odadaki fiziksel nesnelere odaklanmasını iste. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.'
}

# Mod Seçim Butonları
st.write("### Değiştirmek istediğin rutini seç:")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Bir Nefes Al\n(Sigara)", key="btn_sigara"):
        st.session_state.selected_mode = "Sigara Bırakma"
        st.session_state.kai_response = None

with col2:
    if st.button("Dur\n(Stres Yemeği)", key="btn_stres"):
        st.session_state.selected_mode = "Stres Yemeği"
        st.session_state.kai_response = None

with col3:
    if st.button("Beni Buradan Çıkar\n(Sosyal Medya)", key="btn_sosyal"):
        st.session_state.selected_mode = "Sosyal Medya"
        st.session_state.kai_response = None

# Yapay Zeka Yanıtı ve İletişim
if st.session_state.selected_mode:
    st.divider()
    st.subheader(f"🤖 KAI — {st.session_state.selected_mode} Modu")

    if st.session_state.kai_response is None:
        with st.spinner("KAI hazırlanıyor..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": prompts[st.session_state.selected_mode]},
                        {"role": "user", "content": "Kriz anındayım, yardım et."}
                    ]
                )
                st.session_state.kai_response = response.choices[0].message.content
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

    if st.session_state.kai_response:
        st.info(st.session_state.kai_response)

        # Geri Sayım Sayacı
        if st.button("🚀 Başla", key="btn_timer"):
            st.write("---")
            timer_placeholder = st.empty()
            for seconds in range(180, -1, -1):
                mins, secs = divmod(seconds, 60)
                timer_placeholder.metric("Kalan Süre", f"{mins:02d}:{secs:02d}")
                time.sleep(1)
            st.balloons()
            st.success("Harika iş çıkardın Fırat! Kriz anını atlattın.")
