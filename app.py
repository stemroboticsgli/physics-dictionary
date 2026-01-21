import streamlit as st
import pandas as pd
import os
import re
from gtts import gTTS
import tempfile
import datetime
from openai import OpenAI

# ===== AI CLIENT =====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Physics AI Tutor – Thầy Trung", layout="wide")

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


# ===== EXTRACT ENGLISH =====
def extract_english_term(text):
    patterns = [
        r"Noun.*?\s*[:\-]\s*(.+)",
        r"\*\*English\*\*\s*[:\-]\s*(.+)",
        r"English\s*[:\-]\s*(.+)"
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            term = m.group(1).split("\n")[0]
            term = re.sub(r"[^\w\s\-]", "", term)
            return term.strip()

    return None


# ===== AI PHỔ THÔNG =====
def general_gpt_translate(word, mode):
    if mode=="Anh → Việt":
        prompt = f"""
You are an English teacher.

Analyze the word "{word}".

Return exactly:
- Noun (main term)
- Verb form
- Adjective form
- Adverb form
- Explanation
- Example
"""
    else:
        prompt = f"""
You are an English teacher.

Translate and analyze the Vietnamese word "{word}".

Return exactly:
- Noun (main term)
- Verb form
- Adjective form
- Adverb form
- Explanation
- Example
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a professional English teacher."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


# ===== AI VẬT LÍ =====
def physics_gpt_translate(word, mode):
    if mode=="Anh → Việt":
        prompt = f"""
Bạn là giáo viên Vật lí THPT.
Hãy dịch thuật ngữ "{word}" sang tiếng Việt theo đúng ngữ cảnh Vật lí.

Trình bày:
- Noun (main term)
- Verb form
- Adjective form
- Adverb form
- Explanation (physics context)
- Formula (if any)
- Example sentence in physics
"""
    else:
        prompt = f"""
You are a physics teacher.
Translate the Vietnamese physics term "{word}" into proper English physics terminology.

Return:
- Noun (main term)
- Verb form
- Adjective form
- Adverb form
- Explanation (physics context)
- Formula (if any)
- Example sentence in physics
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a professional physics teacher."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


if "login" not in st.session_state:
    st.session_state.login = False


# ================= LOGIN =================
if not st.session_state.login:
    st.title("🔐 Physics AI Tutor – Thầy Trung")

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
menu = st.sidebar.radio("Chức năng",["Tra từ","Phát âm","Thống kê"])

st.sidebar.write(f"👤 Người dùng: {st.session_state.user}")
if st.sidebar.button("Đăng xuất"):
    st.session_state.login=False
    st.rerun()

st.title("PHYSICS AI TUTOR – THẦY TRUNG")


# ================= TRA TỪ =================
if menu=="Tra từ":
    st.header("📖 Từ điển Anh – Việt – Việt – Anh")

    word = st.text_input("Nhập từ cần tra")
    mode = st.selectbox("Chế độ ngôn ngữ",["Anh → Việt","Việt → Anh"])
    translate_type = st.radio("Kiểu dịch",["Phổ thông","Chuyên ngành Vật lí"])

    if st.button("Tra cứu"):
        if word:
            try:
                if translate_type=="Phổ thông":
                    with st.spinner("AI đang phân tích từ vựng..."):
                        result = general_gpt_translate(word,mode)
                        st.markdown(result)

                        eng = extract_english_term(result)
                        speak_word = eng if eng else word

                else:
                    with st.spinner("AI đang phân tích vật lí..."):
                        result = physics_gpt_translate(word,mode)
                        st.markdown(result)

                        eng = extract_english_term(result)
                        speak_word = eng if eng else word

                st.divider()
                st.subheader("🔊 Phát âm")
                audio = speak_safe(speak_word, "en")
                if audio:
                    st.audio(audio)

                log(st.session_state.user,word)

            except Exception as e:
                st.error("Lỗi AI: "+str(e))


# ================= PHÁT ÂM =================
if menu=="Phát âm":
    st.header("🔊 Luyện phát âm")
    w = st.text_input("Nhập từ tiếng Anh")
    if st.button("Nghe"):
        audio = speak_safe(w)
        if audio:
            st.audio(audio)


# ================= THỐNG KÊ =================
if menu=="Thống kê":
    st.header("📊 Lịch sử tra cứu")
    df = pd.read_csv(LOG_FILE)
    st.dataframe(df)
