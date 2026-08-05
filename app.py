import streamlit as st
from openai import OpenAI
import time
import random

# Uygulama Başlığı ve Sayfa Ayarı
st.set_page_config(page_title="RoutineSwap", layout="centered")

# Koyu Tema ve Mobil Dostu CSS Tasarımı
dark_css = """
<style>
body {
    background-color: #0E1117;
    color: #FAFAFA;
}
.stButton>button {
    color: white;
    border-radius: 12px;
    height: 60px;
    font-size: 16px;
    font-weight: bold;
    width: 100%;
    border: 1px solid #30363D;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
}
.tictactoe-btn button {
    height: 70px !important;
    font-size: 28px !important;
}
.memory-btn button {
    height: 65px !important;
    font-size: 24px !important;
}
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)

# API Key Secrets kontrolü
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI API anahtarı Secrets kısmında bulunamadı. Lütfen Streamlit Cloud Secrets ayarlarınızı kontrol edin.")
    st.stop()

client = OpenAI(api_key=api_key)

st.title("🌙 RoutineSwap")

# ---------------------------------------------------------
# SESSION STATE TANIMLARI
# ---------------------------------------------------------
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = None
if "kai_response" not in st.session_state:
    st.session_state.kai_response = None
if "selected_game" not in st.session_state:
    st.session_state.selected_game = None

# 1. X-O-X State
if "xo_board" not in st.session_state:
    st.session_state.xo_board = [""] * 9
if "xo_winner" not in st.session_state:
    st.session_state.xo_winner = None

# 2. Sayı Tahmin State
if "target_number" not in st.session_state:
    st.session_state.target_number = random.randint(1, 100)
if "guess_attempts" not in st.session_state:
    st.session_state.guess_attempts = 0
if "guess_feedback" not in st.session_state:
    st.session_state.guess_feedback = ""

# 3. Hafıza Oyunu State
EMOJIS = ["🍕", "🎮", "🚀", "🐱", "🍕", "🎮", "🚀", "🐱"]
if "memory_cards" not in st.session_state:
    cards = EMOJIS.copy()
    random.shuffle(cards)
    st.session_state.memory_cards = cards
if "memory_flipped" not in st.session_state:
    st.session_state.memory_flipped = [False] * 8
if "memory_selected" not in st.session_state:
    st.session_state.memory_selected = []
if "memory_matched" not in st.session_state:
    st.session_state.memory_matched = []

# ---------------------------------------------------------
# OYUN MANTIKLARI VE SIFIRLAMA
# ---------------------------------------------------------
def reset_xo():
    st.session_state.xo_board = [""] * 9
    st.session_state.xo_winner = None

def reset_guess():
    st.session_state.target_number = random.randint(1, 100)
    st.session_state.guess_attempts = 0
    st.session_state.guess_feedback = ""

def reset_memory():
    cards = EMOJIS.copy()
    random.shuffle(cards)
    st.session_state.memory_cards = cards
    st.session_state.memory_flipped = [False] * 8
    st.session_state.memory_selected = []
    st.session_state.memory_matched = []

# X-O-X Yardımcı Fonksiyonlar
def check_xo_winner(board):
    lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if "" not in board:
        return "Berabere"
    return None

def xo_bot_move():
    empty = [i for i, spot in enumerate(st.session_state.xo_board) if spot == ""]
    if empty and st.session_state.xo_winner is None:
        move = random.choice(empty)
        st.session_state.xo_board[move] = "O"
        st.session_state.xo_winner = check_xo_winner(st.session_state.xo_board)

def make_xo_move(index):
    if st.session_state.xo_board[index] == "" and st.session_state.xo_winner is None:
        st.session_state.xo_board[index] = "X"
        st.session_state.xo_winner = check_xo_winner(st.session_state.xo_board)
        if st.session_state.xo_winner is None:
            xo_bot_move()

# Promtlar
prompts = {
    "Sigara Bırakma": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının sigara/elektronik sigara krizini atlatması için en yakın dostu, mentörü ve sakinleştirici limanısın. Asla resmi konuşma, samimi ve sıcak bir Türkçe kullan. Kriz anındaki gerginliği 1-2 kısa cümleyle dostça göğüsledikten sonra, hemen o anki duygu durumuna özel, elini/zihnini oyalayacak 3 dakikalık net bir mikro-görev ver. Görevi verdikten sonra cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" şeklinde bitir.',
    "Stres Yemeği": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının duygusal yeme krizlerini ve anlık tatlı/atıştırmalık krizlerini yöneten samimi bir dostsun. Asla yargılayıcı konuşma. O anki mutsuzluk, stres veya can sıkıntısı hissini anladığını belirt. Kendisini mutfağa veya buzdolabına yönlendirmek yerine, o an durmasını sağlayacak 3 dakikalık pürüzsüz bir zihinsel değişim görevi ver. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.',
    "Sosyal Medya": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının telefonda amaçsızca kaydırma (doomscrolling) yapmasını ve dijital bağımlılık krizlerini engellemek için tasarlanmış gerçekçi bir dostsun. Ekran başında harcanan zamanın farkına varmasını sağla ama bunu dostça yap. Telefonu hemen masaya ters bırakmasını veya 3 dakika boyunca ekrandan tamamen uzaklaşıp odadaki fiziksel nesnelere odaklanmasını iste. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.'
}

# ---------------------------------------------------------
# ARAYÜZ VE MOD SEÇİMİ
# ---------------------------------------------------------
st.write("### Değiştirmek istediğin rutini seç:")
col1, col2, col3 = st.columns(3)

def select_routine(mode_name):
    st.session_state.selected_mode = mode_name
    st.session_state.kai_response = None
    # Rastgele bir oyun seç (XOX, Sayı Tahmin veya Hafıza Oyunu)
    st.session_state.selected_game = random.choice(["xox", "guess", "memory"])
    reset_xo()
    reset_guess()
    reset_memory()

with col1:
    if st.button("Bir Nefes Al\n(Sigara)", key="btn_sigara"):
        select_routine("Sigara Bırakma")

with col2:
    if st.button("Dur\n(Stres Yemeği)", key="btn_stres"):
        select_routine("Stres Yemeği")

with col3:
    if st.button("Beni Buradan Çıkar\n(Sosyal Medya)", key="btn_sosyal"):
        select_routine("Sosyal Medya")

# ---------------------------------------------------------
# KAI YANITI VE OYUN ALANI
# ---------------------------------------------------------
if st.session_state.selected_mode:
    st.divider()
    st.subheader(f"🤖 KAI — {st.session_state.selected_mode} Modu")

    if st.session_state.kai_response is None:
        with st.spinner("KAI hazırlanıyor..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
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

        # ---------------------------------------------------------
        # MINI OYUN EKRANLARI
        # ---------------------------------------------------------
        
        # 1. OYUN: X-O-X
        if st.session_state.selected_game == "xox":
            st.warning("🎮 **Zihnini Dağıt:** KAI seni X-O-X maçına davet ediyor! (Sen: X | KAI: O)")
            b = st.session_state.xo_board
            for row in range(3):
                g_cols = st.columns(3)
                for col_idx in range(3):
                    idx = row * 3 + col_idx
                    val = b[idx] if b[idx] != "" else " "
                    with g_cols[col_idx]:
                        st.markdown('<div class="tictactoe-btn">', unsafe_allow_html=True)
                        if st.button(val, key=f"xo_{idx}"):
                            make_xo_move(idx)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.xo_winner:
                if st.session_state.xo_winner == "Berabere":
                    st.write("🤝 Berabere bitti!")
                elif st.session_state.xo_winner == "X":
                    st.success("🎉 Sen kazandın!")
                else:
                    st.error("🤖 KAI kazandı!")
                if st.button("Yeniden Oyna", key="btn_reset_xox"):
                    reset_xo()
                    st.rerun()

        # 2. OYUN: SAYI TAHMİN
        elif st.session_state.selected_game == "guess":
            st.warning("🎮 **Zihnini Dağıt:** KAI 1 ile 100 arasında bir sayı tuttu. Bakalım kaç hamlede bulacaksın?")
            
            user_guess = st.number_input("Tahminin:", min_value=1, max_value=100, step=1, key="num_guess_input")
            if st.button("Tahmin Et", key="btn_submit_guess"):
                st.session_state.guess_attempts += 1
                if user_guess < st.session_state.target_number:
                    st.session_state.guess_feedback = "📈 Daha BÜYÜK bir sayı söyle!"
                elif user_guess > st.session_state.target_number:
                    st.session_state.guess_feedback = "📉 Daha KÜÇÜK bir sayı söyle!"
                else:
                    st.session_state.guess_feedback = f"🎉 TEBRİKLER! {st.session_state.guess_attempts} hamlede buldun!"
            
            if st.session_state.guess_feedback:
                if "TEBRİKLER" in st.session_state.guess_feedback:
                    st.success(st.session_state.guess_feedback)
                    if st.button("Yeni Sayı Tut", key="btn_reset_guess"):
                        reset_guess()
                        st.rerun()
                else:
                    st.info(st.session_state.guess_feedback)

        # 3. OYUN: HAFIZA / EŞLEŞTİRME OYUNU
        elif st.session_state.selected_game == "memory":
            st.warning("🎮 **Zihnini Dağıt:** Aynı emojileri bulup kartları eşleştir!")
            
            # 2 satır, 4 sütun
            cards = st.session_state.memory_cards
            flipped = st.session_state.memory_flipped
            matched = st.session_state.memory_matched

            for row in range(2):
                m_cols = st.columns(4)
                for col_idx in range(4):
                    idx = row * 4 + col_idx
                    # Kart kapalıysa ❓ göster, açıksa veya eşleştiyse emojiyi göster
                    card_text = cards[idx] if (flipped[idx] or idx in matched) else "❓"
                    
                    with m_cols[col_idx]:
                        st.markdown('<div class="memory-btn">', unsafe_allow_html=True)
                        if st.button(card_text, key=f"mem_{idx}"):
                            if not flipped[idx] and idx not in matched and len(st.session_state.memory_selected) < 2:
                                st.session_state.memory_flipped[idx] = True
                                st.session_state.memory_selected.append(idx)
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

            # 2 kart seçildiğinde kontrol
            if len(st.session_state.memory_selected) == 2:
                idx1, idx2 = st.session_state.memory_selected
                if cards[idx1] == cards[idx2]:
                    st.session_state.memory_matched.extend([idx1, idx2])
                    st.session_state.memory_selected = []
                    st.success("Eşleşme bulundu!")
                    st.rerun()
                else:
                    time.sleep(0.8)
                    st.session_state.memory_flipped[idx1] = False
                    st.session_state.memory_flipped[idx2] = False
                    st.session_state.memory_selected = []
                    st.rerun()

            if len(st.session_state.memory_matched) == 8:
                st.balloons()
                st.success("🎉 Harika! Bütün eşleşmeleri buldun!")
                if st.button("Yeniden Karıştır", key="btn_reset_mem"):
                    reset_memory()
                    st.rerun()

        st.write("")
        # ---------------------------------------------------------
        # GERİ SAYIM SAYACI
        # ---------------------------------------------------------
        if st.button("🚀 Geri Sayımı Başlat (3 Dakika)", key="btn_timer"):
            st.write("---")
            timer_placeholder = st.empty()
            for seconds in range(180, -1, -1):
                mins, secs = divmod(seconds, 60)
                timer_placeholder.metric("Kalan Süre", f"{mins:02d}:{secs:02d}")
                time.sleep(1)
            st.balloons()
            st.success("Harika iş çıkardın! Kriz anını başarıyla atlattın.")
