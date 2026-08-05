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
    height: 55px;
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
    font-size: 22px !important;
}
/* Popover içi buton genişlikleri */
div[data-testid="stPopoverBody"] button {
    height: 45px !important;
    font-size: 16px !important;
    margin-bottom: 4px;
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
if "content_type" not in st.session_state:
    st.session_state.content_type = None  # "task" veya "game"
if "selected_game" not in st.session_state:
    st.session_state.selected_game = None

# 1. X-O-X State
if "xo_board" not in st.session_state:
    st.session_state.xo_board = [""] * 9
if "xo_winner" not in st.session_state:
    st.session_state.xo_winner = None
if "xo_score_user" not in st.session_state:
    st.session_state.xo_score_user = 0
if "xo_score_kai" not in st.session_state:
    st.session_state.xo_score_kai = 0

# 2. Sayı Tahmin State
if "target_number" not in st.session_state:
    st.session_state.target_number = random.randint(1, 100)
if "guess_attempts" not in st.session_state:
    st.session_state.guess_attempts = 0
if "guess_feedback" not in st.session_state:
    st.session_state.guess_feedback = ""

# 3. Hafıza Oyunu State
EMOJIS = ["🍕", "🎮", "🚀", "🐱", "🏀", "🎧", "🍕", "🎮", "🚀", "🐱", "🏀", "🎧"]
if "memory_cards" not in st.session_state:
    cards = EMOJIS.copy()
    random.shuffle(cards)
    st.session_state.memory_cards = cards
if "memory_flipped" not in st.session_state:
    st.session_state.memory_flipped = [False] * 12
if "memory_selected" not in st.session_state:
    st.session_state.memory_selected = []
if "memory_matched" not in st.session_state:
    st.session_state.memory_matched = []

# 4. Sudoku Mini (4x4) State
def get_initial_sudoku():
    board = [
        [1, 0, 0, 4],
        [0, 0, 2, 0],
        [0, 3, 0, 0],
        [2, 0, 0, 1]
    ]
    locked = [
        [True, False, False, True],
        [False, False, True, False],
        [False, True, False, False],
        [True, False, False, True]
    ]
    solution = [
        [1, 2, 3, 4],
        [3, 4, 2, 1],
        [4, 3, 1, 2],
        [2, 1, 4, 3]
    ]
    return board, locked, solution

if "sudoku_board" not in st.session_state:
    b, l, s = get_initial_sudoku()
    st.session_state.sudoku_board = b
    st.session_state.sudoku_locked = l
    st.session_state.sudoku_solution = s

# 5. Yılan (Snake) State
if "snake" not in st.session_state:
    st.session_state.snake = [(2, 2), (2, 1)]
    st.session_state.food = (0, 3)
    st.session_state.snake_dir = "RIGHT"
    st.session_state.snake_score = 0
    st.session_state.snake_game_over = False

# ---------------------------------------------------------
# OYUN SIFIRLAMA FONKSİYONLARI
# ---------------------------------------------------------
def reset_xo_round():
    st.session_state.xo_board = [""] * 9
    st.session_state.xo_winner = None

def reset_xo_full():
    reset_xo_round()
    st.session_state.xo_score_user = 0
    st.session_state.xo_score_kai = 0

def reset_guess():
    st.session_state.target_number = random.randint(1, 100)
    st.session_state.guess_attempts = 0
    st.session_state.guess_feedback = ""

def reset_memory():
    cards = EMOJIS.copy()
    random.shuffle(cards)
    st.session_state.memory_cards = cards
    st.session_state.memory_flipped = [False] * 12
    st.session_state.memory_selected = []
    st.session_state.memory_matched = []

def reset_sudoku():
    b, l, s = get_initial_sudoku()
    st.session_state.sudoku_board = b
    st.session_state.sudoku_locked = l
    st.session_state.sudoku_solution = s

def reset_snake():
    st.session_state.snake = [(2, 2), (2, 1)]
    st.session_state.food = (random.randint(0, 4), random.randint(0, 4))
    st.session_state.snake_dir = "RIGHT"
    st.session_state.snake_score = 0
    st.session_state.snake_game_over = False

# --- X-O-X Bot Mantığı ---
def check_xo_winner(board):
    lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if "" not in board:
        return "Berabere"
    return None

def xo_smart_bot_move():
    board = st.session_state.xo_board
    empty = [i for i, spot in enumerate(board) if spot == ""]
    if not empty or st.session_state.xo_winner:
        return

    for spot in empty:
        temp = board.copy()
        temp[spot] = "O"
        if check_xo_winner(temp) == "O":
            board[spot] = "O"
            st.session_state.xo_winner = check_xo_winner(board)
            return

    for spot in empty:
        temp = board.copy()
        temp[spot] = "X"
        if check_xo_winner(temp) == "X":
            board[spot] = "O"
            st.session_state.xo_winner = check_xo_winner(board)
            return

    if 4 in empty:
        board[4] = "O"
    else:
        move = random.choice(empty)
        board[move] = "O"
    
    st.session_state.xo_winner = check_xo_winner(board)

def make_xo_move(index):
    if st.session_state.xo_board[index] == "" and st.session_state.xo_winner is None:
        st.session_state.xo_board[index] = "X"
        st.session_state.xo_winner = check_xo_winner(st.session_state.xo_board)
        
        if st.session_state.xo_winner is None:
            xo_smart_bot_move()
            
        if st.session_state.xo_winner:
            if st.session_state.xo_winner == "X":
                st.session_state.xo_score_user += 1
            elif st.session_state.xo_winner == "O":
                st.session_state.xo_score_kai += 1

# PROMPT AYARLARI
task_prompts = {
    "Sigara Bırakma": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının sigara/elektronik sigara krizini atlatması için samimi bir dostsun. Kriz anındaki gerginliği 1-2 kısa cümleyle dostça göğüsledikten sonra, hemen o anki duygu durumuna özel, elini/zihnini oyalayacak 3 dakikalık net bir mikro-görev ver. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.',
    "Stres Yemeği": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının duygusal yeme krizlerini yöneten samimi bir dostsun. O anki mutsuzluk veya stres hissini anladığını belirt. Kendisini mutfağa yönlendirmek yerine, 3 dakikalık zihinsel değişim görevi ver. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.',
    "Sosyal Medya": 'Sen "RoutineSwap" uygulamasının içindeki yapay zeka koçu KAI\'sin. Kullanıcının telefonda doomscrolling yapmasını engelleyen gerçekçi bir dostsun. Telefonu masaya ters bırakmasını veya 3 dakika boyunca ekrandan uzaklaşmasını iste. Cümleni "Hazırsan \'Başla\' butonuna bas, geri sayımı başlatıyorum" diyerek bitir.'
}

game_prompts = {
    "Sigara Bırakma": 'Sen RoutineSwap KAI\'sin. Sigara krizi gelen kullanıcıya tek cümlelik heyecanlı bir meydan okuma yaz: "Ellerini ve zihnini sigaradan uzaklaştırma vakti! Bakalım bu mini oyunda beni yenebilecek misin?"',
    "Stres Yemeği": 'Sen RoutineSwap KAI\'sin. Tatlı krizi gelen kullanıcıya tek cümlelik meydan okuma yaz: "Mutfak kapısını kapat, odağımızı değiştiriyoruz! Bakalım bu oyunda ne kadar hızlısın?"',
    "Sosyal Medya": 'Sen RoutineSwap KAI\'sin. Sosyal medyada takılan kullanıcıya tek cümlelik meydan okuma yaz: "Ekranı kaydırmayı bırak, zihnini çalıştırma vakti! Oyun başlıyor!"'
}

# ---------------------------------------------------------
# ARAYÜZ VE MOD SEÇİMİ
# ---------------------------------------------------------
st.write("### Değiştirmek istediğin rutini seç:")
col1, col2, col3 = st.columns(3)

def select_routine(mode_name):
    st.session_state.selected_mode = mode_name
    st.session_state.kai_response = None
    st.session_state.content_type = random.choice(["task", "game"])
    
    available_games = ["xox", "guess", "memory", "sudoku", "snake"]
    if st.session_state.selected_game in available_games:
        available_games.remove(st.session_state.selected_game)
        
    st.session_state.selected_game = random.choice(available_games)
    
    reset_xo_full()
    reset_guess()
    reset_memory()
    reset_sudoku()
    reset_snake()

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
# KAI YANITI VE İÇERİK EKRANI
# ---------------------------------------------------------
if st.session_state.selected_mode:
    st.divider()
    st.subheader(f"🤖 KAI — {st.session_state.selected_mode} Modu")

    if st.session_state.kai_response is None:
        with st.spinner("KAI hazırlanıyor..."):
            try:
                system_prompt = task_prompts[st.session_state.selected_mode] if st.session_state.content_type == "task" else game_prompts[st.session_state.selected_mode]
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Kriz anındayım, yardım et."}
                    ]
                )
                st.session_state.kai_response = response.choices[0].message.content
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

    if st.session_state.kai_response:
        st.info(st.session_state.kai_response)

        # GÖREV MODU
        if st.session_state.content_type == "task":
            st.write("")
            if st.button("🚀 Geri Sayımı Başlat (3 Dakika)", key="btn_timer_task"):
                st.write("---")
                timer_placeholder = st.empty()
                for seconds in range(180, -1, -1):
                    mins, secs = divmod(seconds, 60)
                    timer_placeholder.metric("Kalan Süre", f"{mins:02d}:{secs:02d}")
                    time.sleep(1)
                st.balloons()
                st.success("Harika iş çıkardın! Kriz dalgasını başarıyla atlattın.")

        # OYUN MODU
        elif st.session_state.content_type == "game":
            
            # 1. X-O-X
            if st.session_state.selected_game == "xox":
                st.warning("🎮 **Zihnini Dağıt:** KAI ile X-O-X Seri Maçı! (3 Skora Ulaşan Kazanır)")
                st.write(f"🏆 **Skor -> Sen: {st.session_state.xo_score_user} | KAI: {st.session_state.xo_score_kai}**")
                
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
                        st.info("🤝 Raund berabere bitti!")
                    elif st.session_state.xo_winner == "X":
                        st.success("🎉 Raundu sen kazandın!")
                    else:
                        st.error("🤖 Raundu KAI kazandı!")

                    if st.session_state.xo_score_user >= 3:
                        st.balloons()
                        st.success("👑 TEBRİKLER! SERİYİ KAZANDIN!")
                        if st.button("Yeni Seri Başlat", key="btn_reset_full_xo"):
                            reset_xo_full()
                            st.rerun()
                    elif st.session_state.xo_score_kai >= 3:
                        st.error("💀 SERİYİ KAI KAZANDI!")
                        if st.button("Rövanş İste", key="btn_reset_full_xo2"):
                            reset_xo_full()
                            st.rerun()
                    else:
                        if st.button("Sonraki Raund", key="btn_next_xo_round"):
                            reset_xo_round()
                            st.rerun()

            # 2. SAYI TAHMİN
            elif st.session_state.selected_game == "guess":
                st.warning("🎮 **Zihnini Dağıt:** KAI 1 ile 100 arasında bir sayı tuttu!")
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

            # 3. HAFIZA OYUNU
            elif st.session_state.selected_game == "memory":
                st.warning("🎮 **Zihnini Dağıt:** 6 Eşleşmeyi Bul!")
                cards = st.session_state.memory_cards
                flipped = st.session_state.memory_flipped
                matched = st.session_state.memory_matched

                for row in range(3):
                    m_cols = st.columns(4)
                    for col_idx in range(4):
                        idx = row * 4 + col_idx
                        card_text = cards[idx] if (flipped[idx] or idx in matched) else "❓"
                        
                        with m_cols[col_idx]:
                            st.markdown('<div class="memory-btn">', unsafe_allow_html=True)
                            if st.button(card_text, key=f"mem_{idx}"):
                                if not flipped[idx] and idx not in matched and len(st.session_state.memory_selected) < 2:
                                    st.session_state.memory_flipped[idx] = True
                                    st.session_state.memory_selected.append(idx)
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                if len(st.session_state.memory_selected) == 2:
                    idx1, idx2 = st.session_state.memory_selected
                    if cards[idx1] == cards[idx2]:
                        st.session_state.memory_matched.extend([idx1, idx2])
                        st.session_state.memory_selected = []
                        st.success("Eşleşme bulundu!")
                        st.rerun()
                    else:
                        time.sleep(0.6)
                        st.session_state.memory_flipped[idx1] = False
                        st.session_state.memory_flipped[idx2] = False
                        st.session_state.memory_selected = []
                        st.rerun()

                if len(st.session_state.memory_matched) == 12:
                    st.balloons()
                    st.success("🎉 Harika! Bütün 6 eşleşmeyi buldun!")
                    if st.button("Yeniden Karıştır", key="btn_reset_mem"):
                        reset_memory()
                        st.rerun()

            # 4. TAMAMEN DÜZELTİLMİŞ POP-OVER MANTIKLI SUDOKU (4x4)
            elif st.session_state.selected_game == "sudoku":
                st.warning("🧩 **Zihnini Dağıt:** Mini 4x4 Sudoku!")
                st.caption("📌 Kilitli olmayan karelere tıklayıp sayıyı seçebilir veya 'Temizle' yapabilirsin.")
                
                board = st.session_state.sudoku_board
                locked = st.session_state.sudoku_locked
                
                for r in range(4):
                    s_cols = st.columns(4)
                    for c in range(4):
                        val = board[r][c]
                        is_loc = locked[r][c]
                        
                        with s_cols[c]:
                            if is_loc:
                                # Kilitli sabit hücreler
                                st.button(f"🔒 {val}", key=f"sdk_{r}_{c}", disabled=True)
                            else:
                                # Kullanıcının doldurabildiği hücreler (Popover Arayüzü)
                                label = f"✏️ {val}" if val != 0 else "➖"
                                with st.popover(label, use_container_width=True):
                                    st.write(f"**Hücre [{r+1}, {c+1}] Seçimi:**")
                                    p_col1, p_col2 = st.columns(2)
                                    with p_col1:
                                        if st.button("1", key=f"pop_{r}_{c}_1"):
                                            st.session_state.sudoku_board[r][c] = 1
                                            st.rerun()
                                        if st.button("3", key=f"pop_{r}_{c}_3"):
                                            st.session_state.sudoku_board[r][c] = 3
                                            st.rerun()
                                    with p_col2:
                                        if st.button("2", key=f"pop_{r}_{c}_2"):
                                            st.session_state.sudoku_board[r][c] = 2
                                            st.rerun()
                                        if st.button("4", key=f"pop_{r}_{c}_4"):
                                            st.session_state.sudoku_board[r][c] = 4
                                            st.rerun()
                                    
                                    if st.button("❌ Temizle (Boş Bırak)", key=f"pop_{r}_{c}_clear"):
                                        st.session_state.sudoku_board[r][c] = 0
                                        st.rerun()

                st.write("")
                col_chk, col_rst = st.columns(2)
                with col_chk:
                    if st.button("✅ Kontrol Et", key="btn_check_sudoku"):
                        # Boş hücre kontrolü
                        has_empty = any(0 in row for row in st.session_state.sudoku_board)
                        if has_empty:
                            st.warning("⚠️ Henüz tüm hücreleri doldurmadın!")
                        elif st.session_state.sudoku_board == st.session_state.sudoku_solution:
                            st.balloons()
                            st.success("🎉 MÜKEMMEL! Sudoku'yu doğru çözdün!")
                        else:
                            st.error("❌ Hatalı rakamlar var, tekrar gözden geçir!")
                
                with col_rst:
                    if st.button("🔄 Tahtayı Temizle", key="btn_reset_sudoku_board"):
                        reset_sudoku()
                        st.rerun()

            # 5. YILAN (SNAKE)
            elif st.session_state.selected_game == "snake":
                st.warning("🐍 **Zihnini Dağıt:** Yılan Oyununda Yemleri Topla!")
                
                grid_display = [["⬜" for _ in range(5)] for _ in range(5)]
                for sr, sc in st.session_state.snake:
                    grid_display[sr][sc] = "🟩"
                fr, fc = st.session_state.food
                grid_display[fr][fc] = "🍎"
                
                for r in range(5):
                    st.text(" ".join(grid_display[r]))
                
                st.write(f"Skor: **{st.session_state.snake_score}**")

                c_up, c_down, c_left, c_right = st.columns(4)
                move = None
                with c_up:
                    if st.button("⬆️ Yukarı", key="snk_u"): move = "UP"
                with c_down:
                    if st.button("⬇️ Aşağı", key="snk_d"): move = "DOWN"
                with c_left:
                    if st.button("⬅️ Sol", key="snk_l"): move = "LEFT"
                with c_right:
                    if st.button("➡️ Sağ", key="snk_r"): move = "RIGHT"

                if move and not st.session_state.snake_game_over:
                    head_r, head_c = st.session_state.snake[0]
                    if move == "UP": head_r -= 1
                    elif move == "DOWN": head_r += 1
                    elif move == "LEFT": head_c -= 1
                    elif move == "RIGHT": head_c += 1

                    new_head = (head_r, head_c)
                    
                    if head_r < 0 or head_r >= 5 or head_c < 0 or head_c >= 5 or new_head in st.session_state.snake:
                        st.session_state.snake_game_over = True
                    else:
                        st.session_state.snake.insert(0, new_head)
                        if new_head == st.session_state.food:
                            st.session_state.snake_score += 1
                            st.session_state.food = (random.randint(0, 4), random.randint(0, 4))
                        else:
                            st.session_state.snake.pop()
                    st.rerun()

                if st.session_state.snake_game_over:
                    st.error("💥 Oyunu Kaybettin!")
                    if st.button("Yeniden Başlat", key="btn_reset_snake"):
                        reset_snake()
                        st.rerun()
