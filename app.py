import streamlit as st
import pandas as pd
import os
from gtts import gTTS
import tempfile
import datetime

# ===== TRANSLATOR SAFE =====
try:
    from deep_translator import GoogleTranslator
    TRANSLATE_OK = True
except:
    TRANSLATE_OK = False

st.set_page_config(page_title="Physics Dictionary – Thầy Trung", layout="wide")

USERS_FILE = "users.csv"
LOG_FILE = "history.csv"

if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["username","password","role","locked"]).to_csv(USERS_FILE,index=False)

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["user","word","time"]).to_csv(LOG_FILE,index=False)

def load_users():
    df = pd.read_csv(USERS_FILE, dtype=str)
    df["locked"] = df["locked"].fillna("False")
    return df

def save_users(df):
    df.to_csv(USERS_FILE,index=False)

def log(user, word):
    df = pd.read_csv(LOG_FILE)
    df.loc[len(df)] = [user, word, datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")]
    df.to_csv(LOG_FILE,index=False)

def speak_safe(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = tempfile.NamedTemporaryFile(delete=False,suffix=".mp3")
        tts.save(fp.name)
        return fp.name
    except:
        return None

if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
if not st.session_state.login:
    st.title("🔐 Physics Dictionary – Thầy Trung")

    tab1,tab2 = st.tabs(["Đăng nhập","Tạo tài khoản"])

    with tab1:
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu",type="password")
        if st.button("Đăng nhập"):
            df = load_users()
            if u in df.username.values:
                row = df[df.username==u].iloc[0]
                if row["locked"]=="True":
                    st.error("Tài khoản bị khoá")
                elif p == str(row["password"]):
                    st.session_state.login=True
                    st.session_state.user=u
                    st.session_state.role=row["role"]
                    st.rerun()
                else:
                    st.error("Sai mật khẩu")
            else:
                st.error("Không tồn tại")

    with tab2:
        nu = st.text_input("Tạo user")
        np = st.text_input("Tạo mật khẩu",type="password")
        if st.button("Đăng ký"):
            df = load_users()
            if nu in df.username.values:
                st.error("User đã tồn tại")
            else:
                df.loc[len(df)] = [nu,str(np),"HS","False"]
                save_users(df)
                st.success("Tạo thành công – sang tab đăng nhập")

    st.stop()

# ================= MAIN =================
st.sidebar.title("📘 Physics System")
menu = st.sidebar.radio("Chức năng",
        ["Tra từ","Phát âm","Thống kê"])

st.sidebar.write(f"👤 Người dùng: {st.session_state.user}")
if st.sidebar.button("Đăng xuất"):
    st.session_state.login=False
    st.rerun()

st.title("PHYSICS DICTIONARY – THẦY TRUNG")

# ================= TRA TỪ =================
if menu=="Tra từ":
    st.header("📖 Từ điển Anh – Việt – Việt – Anh")
    word = st.text_input("Nhập từ cần tra")
    mode = st.selectbox("Chế độ",["Anh → Việt","Việt → Anh"])

    if st.button("Tra cứu"):
        if word:
            if TRANSLATE_OK:
                try:
                    if mode=="Anh → Việt":
                        result = GoogleTranslator(source='en', target='vi').translate(word)
                        audio_lang="en"
                    else:
                        result = GoogleTranslator(source='vi', target='en').translate(word)
                        audio_lang="en"

                    st.success(result)

                    audio = speak_safe(result, audio_lang)
                    if audio:
                        st.audio(audio)

                except:
                    st.error("Lỗi mạng dịch")

            else:
                st.warning("⚠ Offline – chỉ hiển thị từ")
                st.success(word)

            log(st.session_state.user,word)

# ================= PHÁT ÂM =================
if menu=="Phát âm":
    st.header("🔊 Luyện phát âm")
    w = st.text_input("Nhập từ tiếng Anh")
    if st.button("Nghe"):
        audio = speak_safe(w)
        if audio:
            st.audio(audio)
        else:
            st.warning("Không phát âm được")

# ================= THỐNG KÊ =================
if menu=="Thống kê":
    st.header("📊 Lịch sử tra cứu")
    df = pd.read_csv(LOG_FILE)
    st.dataframe(df)
