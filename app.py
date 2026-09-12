import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import pandas as pd
import requests
import io
import re
import json
import os
import uuid
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="BC Tech Ai Assistant", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# Custom Modern Chat Bubbles Styles with Full Capsule Rounded Chat Input Box
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden !important;}
    header {visibility: visible !important;}
    
    .stApp > header {background-color: transparent;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    
    .block-container {padding-top: 1.5rem; max-width: 780px;}
    
    /* Full Capsule Round Shape for Chat Input Container and Box */
    [data-testid="stChatInput"] {
        border-radius: 50px !important;
        background-color: transparent !important;
    }
    
    [data-testid="stChatInput"] > div {
        border-radius: 50px !important;
        border: 1px solid #dfe1e5 !important;
        background-color: #f8f9fa !important;
        box-shadow: 0 2px 8px rgba(32,33,36,0.12) !important;
        padding-left: 10px !important;
        padding-right: 6px !important;
    }
    
    [data-testid="stChatInput"] > div:focus-within {
        box-shadow: 0 4px 12px rgba(32,33,36,0.22) !important;
        border-color: #4285F4 !important;
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="input"] {
        border-radius: 50px !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Target User messages to align to Right cleanly */
    [data-testid="stChatMessage"]:has(div.st-emotion-cache-1c7y2kd),
    [data-testid="stChatMessage"]:has(img[alt="user"]) {
        flex-direction: row-reverse;
        text-align: right;
    }
    
    [data-testid="stChatMessage"] {
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 16px;
    }
    
    /* Sidebar Recent Buttons */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton>button {
        width: 100% !important;
        float: none !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: #ffffff !important;
        border: 1px solid #dadce0 !important;
        color: #1a73e8 !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 6px;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton>button:hover {
        background-color: #e8f0fe !important;
        border-color: #4285f4 !important;
        color: #1967d2 !important;
    }
    
    #new_chat_btn_wrap button {
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        float: none !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# --- PERSISTENT STORAGE DB MANAGER ---
DB_FILE = "bctech_chat_storage.json"
PAPERS_META_FILE = "bctech_papers_store.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_papers_db():
    if os.path.exists(PAPERS_META_FILE):
        try:
            with open(PAPERS_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_papers_db(papers_db):
    try:
        with open(PAPERS_META_FILE, "w", encoding="utf-8") as f:
            json.dump(papers_db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if "papers_data" not in st.session_state:
    st.session_state.papers_data = load_papers_db()

query_params = st.query_params
if "chat_id" not in query_params or not query_params["chat_id"]:
    current_chat_id = str(uuid.uuid4())
    st.query_params["chat_id"] = current_chat_id
else:
    current_chat_id = query_params["chat_id"]

db_data = load_db()
if current_chat_id not in db_data:
    db_data[current_chat_id] = {
        "messages": [],
        "recent_chats": [],
        "current_language": "HINDI",
        "last_mentioned_name": None
    }
    save_db(db_data)

if "messages" not in st.session_state:
    st.session_state.messages = db_data[current_chat_id]["messages"]
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = db_data[current_chat_id]["recent_chats"]
if "current_language" not in st.session_state:
    st.session_state.current_language = db_data[current_chat_id]["current_language"]
if "last_mentioned_name" not in st.session_state:
    st.session_state.last_mentioned_name = db_data[current_chat_id]["last_mentioned_name"]

def persist_current_state():
    db = load_db()
    if current_chat_id not in db:
        db[current_chat_id] = {}
    db[current_chat_id]["messages"] = st.session_state.messages
    db[current_chat_id]["recent_chats"] = st.session_state.recent_chats
    db[current_chat_id]["current_language"] = st.session_state.current_language
    db[current_chat_id]["last_mentioned_name"] = st.session_state.last_mentioned_name
    save_db(db)

# --- EMOJI REMOVER UTILITY FOR VOICE ---
def remove_emojis(text):
    return re.sub(
        r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]|[\uD800-\uDBFF][\uDC00-\uDFFF]|[\U0001f300-\U0001f5ff]|[\U0001f600-\U0001f64f]|[\U0001f680-\U0001f6ff]|[\u2600-\u26ff]|[\u2700-\u27bf]|[\U0001f900-\U0001f9ff]|[\U0001fa70-\U0001faff]|[\u231a-\u231b]|[\u23e9-\u23ec]|[\u23f0]|[\u23f3]|[\u25aa-\u25ab]|[\u25b6]|[\u25c0]|[\u25fb-\u25fe]|[\u2600-\u27ef]|[\u2b50]|[\u2b55]|[\u3030]|[\u303d]|[\u3297]|[\u3299]',
        '',
        text
    )

# --- READ ALOUD & STOP CONTROLS COMPONENT ---
def render_voice_and_copy_toolbar(text_to_speak, unique_id, lang_code="hi-IN"):
    clean_speech_text = remove_emojis(text_to_speak)
    json_speech = json.dumps(clean_speech_text)
    json_copy = json.dumps(text_to_speak)
    
    html_toolbar = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 8px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .action-btn {{
            border-radius: 16px;
            padding: 3px 12px;
            font-size: 12px;
            border: 1px solid #dadce0;
            background-color: #f8f9fa;
            color: #3c4043;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
        }}
        .action-btn:hover {{
            background-color: #e8eaed;
            color: #202124;
        }}
    </style>
    </head>
    <body>
        <button class="action-btn" id="speak_{unique_id}" onclick="toggleSpeak()">
            🔊 Read Aloud
        </button>
        <button class="action-btn" id="copy_{unique_id}" onclick="doCopy()">
            📋 Copy
        </button>
        <script>
            let utterance_{unique_id} = null;

            function toggleSpeak() {{
                const btn = document.getElementById('speak_{unique_id}');
                
                if (window.speechSynthesis.speaking) {{
                    window.speechSynthesis.cancel();
                    btn.innerHTML = '🔊 Read Aloud';
                    return;
                }}

                const text = {json_speech};
                if ('speechSynthesis' in window) {{
                    utterance_{unique_id} = new SpeechSynthesisUtterance(text);
                    utterance_{unique_id}.lang = '{lang_code}';
                    utterance_{unique_id}.rate = 0.93; 
                    utterance_{unique_id}.pitch = 1.0; 

                    const voices = window.speechSynthesis.getVoices();
                    const targetLang = '{lang_code}'.substring(0, 2);
                    
                    let bestVoice = voices.find(v => v.lang.includes(targetLang) && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Microsoft')));
                    if (!bestVoice) {{
                        bestVoice = voices.find(v => v.lang.includes(targetLang));
                    }}
                    if (bestVoice) {{
                        utterance_{unique_id}.voice = bestVoice;
                    }}
                    
                    btn.innerHTML = '⏹️ Stop';
                    
                    utterance_{unique_id}.onend = function() {{
                        btn.innerHTML = '🔊 Read Aloud';
                    }};
                    utterance_{unique_id}.onerror = function() {{
                        btn.innerHTML = '🔊 Read Aloud';
                    }};
                    
                    window.speechSynthesis.speak(utterance_{unique_id});
                }} else {{
                    alert('Text-to-speech is not supported in this browser.');
                }}
            }}

            if ('speechSynthesis' in window) {{
                window.speechSynthesis.onvoiceschanged = function() {{
                    window.speechSynthesis.getVoices();
                }};
            }}

            function doCopy() {{
                const text = {json_copy};
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(text).then(showSuccess);
                }} else {{
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    ta.style.position = 'fixed';
                    ta.style.left = '-9999px';
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    showSuccess();
                }}
            }}
            function showSuccess() {{
                const b = document.getElementById('copy_{unique_id}');
                b.innerHTML = '✓ Copied!';
                b.style.backgroundColor = '#e6f4ea';
                b.style.color = '#137333';
                b.style.borderColor = '#ceead6';
                setTimeout(() => {{
                    b.innerHTML = '📋 Copy';
                    b.style.backgroundColor = '#f8f9fa';
                    b.style.color = '#3c4043';
                    b.style.borderColor = '#dadce0';
                }}, 2000);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_toolbar, height=35)

def run_aerial_celebration():
    st.balloons()
    anim_js = """
    <script>
    const parentDoc = window.parent.document;
    for(let i = 0; i < 45; i++) {
        let el = parentDoc.createElement('div');
        el.innerText = ['🎆', '✨', '🏮', '🚀', '⭐', '🎉'][Math.floor(Math.random() * 6)];
        el.style.position = 'fixed';
        el.style.left = Math.random() * 95 + 'vw';
        el.style.bottom = '-50px';
        el.style.fontSize = (Math.random() * 24 + 20) + 'px';
        el.style.zIndex = '999999';
        el.style.transition = 'all ' + (Math.random() * 1.8 + 1.2) + 's cubic-bezier(0.25, 1, 0.5, 1)';
        el.style.opacity = '1';
        el.style.pointerEvents = 'none';
        parentDoc.body.appendChild(el);

        setTimeout(() => {
            el.style.bottom = (Math.random() * 55 + 40) + 'vh';
            el.style.transform = 'scale(' + (Math.random() * 1.5 + 1) + ') rotate(' + (Math.random() * 360) + 'deg)';
        }, 30);

        setTimeout(() => {
            el.style.opacity = '0';
        }, 2200);

        setTimeout(() => {
            el.remove();
        }, 3200);
    }
    </script>
    """
    components.html(anim_js, height=0)

def on_new_chat_clicked():
    if st.session_state.messages:
        user_queries = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        title_text = user_queries[-1] if user_queries else "Chat"
        short_title = (title_text[:22] + "..") if len(title_text) > 22 else title_text
        
        new_entry = {
            "title": short_title,
            "messages": list(st.session_state.messages)
        }
        st.session_state.recent_chats.insert(0, new_entry)
        st.session_state.recent_chats = st.session_state.recent_chats[:3]

    st.session_state.messages = []
    st.session_state.current_language = "HINDI"
    st.session_state.last_mentioned_name = None
    
    new_id = str(uuid.uuid4())
    st.query_params["chat_id"] = new_id
    persist_current_state()

def restore_chat(idx):
    if idx < len(st.session_state.recent_chats):
        st.session_state.messages = list(st.session_state.recent_chats[idx]["messages"])
        persist_current_state()

def clean_val_display(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
        return "N/A"
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except Exception:
        return str(val).strip()

# Sidebar - Admin Panel with Contact Info (Phone & WhatsApp: 77789 26285)
with st.sidebar:
    st.markdown("### 🎓 BC Tech Ai Assistant")
    st.markdown('<div id="new_chat_btn_wrap">', unsafe_allow_html=True)
    if st.button("➕ New Chat", key="side_new_chat_btn", on_click=on_new_chat_clicked):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("🕒 Recent (Last 3)", expanded=True):
        if st.session_state.recent_chats:
            for i, item in enumerate(st.session_state.recent_chats):
                st.button(
                    f"💬 {item['title']}", 
                    key=f"btn_restore_{i}",
                    on_click=restore_chat,
                    args=(i,)
                )
        else:
            st.caption("No recent chats yet.")

    st.markdown("---")
    st.markdown("### 🔒 Teacher / Admin Panel")
    with st.expander("📁 Upload & Manage Papers", expanded=False):
        admin_pass = st.text_input("Enter Password", type="password", key="admin_pass_input")
        if admin_pass == "bctech1AA@":
            st.success("Access Granted!")
            uploaded_file = st.file_uploader("Upload Question Paper (PDF / JPG / PNG)", type=["pdf", "jpg", "jpeg", "png"])
            
            if uploaded_file is not None:
                original_filename = uploaded_file.name
                base_name = os.path.splitext(original_filename)[0]
                st.info(f"Detected Paper Name: **{base_name}**")
                
                if st.button("Upload & Save Paper"):
                    p_key = base_name.strip().lower()
                    os.makedirs("uploaded_papers", exist_ok=True)
                    file_path = os.path.join("uploaded_papers", original_filename)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    file_ext = os.path.splitext(original_filename)[1].lower()
                    mimetype = "application/pdf" if file_ext == ".pdf" else (f"image/{file_ext[1:]}" if file_ext in [".jpg", ".jpeg", ".png"] else "application/octet-stream")

                    st.session_state.papers_data[p_key] = {
                        "display_name": base_name,
                        "filename": original_filename,
                        "path": file_path,
                        "mime": mimetype,
                        "locked": True
                    }
                    save_papers_db(st.session_state.papers_data)
                    st.success(f"Paper '{base_name}' successfully uploaded!")
            
            if st.session_state.papers_data:
                st.markdown("**Existing Papers Status:**")
                for pk, p_info in list(st.session_state.papers_data.items()):
                    d_name = p_info.get("display_name", pk)
                    status_str = "🔒 Locked" if p_info["locked"] else "🟢 Unlocked"
                    
                    st.text(f"{d_name} ({status_str})")
                    col_t, col_d = st.columns(2)
                    
                    if col_t.button("Toggle Lock", key=f"tog_{pk}"):
                        st.session_state.papers_data[pk]["locked"] = not p_info["locked"]
                        save_papers_db(st.session_state.papers_data)
                        st.rerun()
                        
                    if col_d.button("🗑️ Delete", key=f"del_{pk}"):
                        try:
                            if os.path.exists(p_info["path"]):
                                os.remove(p_info["path"])
                        except Exception:
                            pass
                        del st.session_state.papers_data[pk]
                        save_papers_db(st.session_state.papers_data)
                        st.success(f"Deleted '{d_name}' successfully!")
                        st.rerun()
        elif admin_pass != "":
            st.error("Incorrect Password!")

    st.markdown("---")
    st.markdown("### संपर्क:")
    st.markdown("📞 फ़ोन: **77789 26285**")
    st.markdown("📱 व्हाट्सएप: **77789 26285**")
    st.markdown("🌐 वेबसाइट: [Official Website](https://sites.google.com/view/bctechcomputer/about-us)")
    st.markdown("📍 [Branch Location](https://sites.google.com/view/bctechcomputer/about-us)")

st.title("🎓 BC Tech Ai Assistant")

SHEET_ID = "1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15)
def load_all_sheets_data():
    try:
        res = requests.get(EXCEL_URL, timeout=15)
        if res.status_code == 200 and len(res.content) > 100:
            excel_file = io.BytesIO(res.content)
            all_dfs = pd.read_excel(excel_file, sheet_name=None)
            combined_rows = []
            
            for sheet_name, df in all_dfs.items():
                if df is not None and not df.empty and len(df.columns) >= 2:
                    cols = list(df.columns)
                    first_col = cols[0]
                    second_col = cols[1]

                    clean_df = df[df[first_col].notna()].copy()
                    clean_df = clean_df[~clean_df[first_col].astype(str).str.lower().str.contains("batch time", na=False)]
                    clean_df = clean_df[clean_df[first_col].astype(str).str.strip() != ""]
                    
                    clean_df[second_col] = clean_df[second_col].ffill()
                    
                    for _, row in clean_df.iterrows():
                        student_name = str(row[first_col]).strip()
                        name_words = sorted(student_name.lower().split())
                        name_signature = " ".join(name_words)
                        
                        raw_exam = str(row[second_col]).strip() if pd.notna(row[second_col]) else "Course"
                        exam_val = raw_exam.capitalize() if raw_exam.lower() != "nan" else "Course"
                        
                        record = {
                            "Student_Name_Std": student_name,
                            "Name_Signature_Std": name_signature,
                            "Exam_Std": exam_val,
                            "_Sheet_Tab": sheet_name
                        }
                        
                        for idx, c in enumerate(cols[2:], start=1):
                            val = row[c]
                            c_name = str(c).strip()
                            if "unnamed" in c_name.lower():
                                c_name = f"Marks_{idx}"
                            record[c_name] = clean_val_display(val)
                                
                        combined_rows.append(record)
                        
            if combined_rows:
                return pd.DataFrame(combined_rows), None
    except Exception as err:
        return None, str(err)
        
    return None, "Sheet data unavailable"

def update_language_state(text):
    text_clean = text.strip().lower()
    
    if any('\u0A80' <= ch <= '\u0AFF' for ch in text):
        st.session_state.current_language = "GUJARATI"
        return "GUJARATI"
        
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        st.session_state.current_language = "HINDI"
        return "HINDI"
    
    hindi_romanized = [
        "kaise", "kaisa", "kaisi", "kaha", "kahan", "kya", "hain", "ho", "hu", "mera", 
        "meri", "karo", "batao", "bata do", "aap", "tum", "kaun", "kisne", "kyu", "kyon",
        "kab", "mein", "main", "hai", "kya hai", "kon hai", "kaha ke hai", "ka bhi", "kare", "show", "dekh", "samay", "time", "date", "tarikh", "lock", "unlock", "open", "class", "batch", "chalu", "band", "timing"
    ]
    words = text_clean.split()
    
    english_indicators = ["my name is", "what is", "how are", "hello", "hi", "where is", "can you", "thank you", "result of", "timing", "batch", "class"]
    if any(ind in text_clean for ind in english_indicators) and not any(w in hindi_romanized for w in words):
        st.session_state.current_language = "ENGLISH"
        return "ENGLISH"
        
    if any(w in hindi_romanized for w in words):
        st.session_state.current_language = "HINDI"
        return "HINDI"
        
    english_common = ["name", "is", "the", "and", "you", "your", "what", "where", "how", "am", "time", "date", "lock", "unlock", "open", "timing", "batch", "class"]
    if any(w in english_common for w in words) and not any(w in hindi_romanized for w in words):
        st.session_state.current_language = "ENGLISH"
        return "ENGLISH"
        
    return st.session_state.current_language

def is_greeting(text):
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    greetings = ["hi", "hello", "hey", "hii", "hiii", "namaste", "kem cho", "kem chho", "halo", "हेलो", "નમસ્ते"]
    return text_clean in greetings

def check_is_name_intro(text):
    t = text.lower().strip()
    result_intent_words = ["result", "marks", "exam", "score", "reult", "rizalt", "marksheet", "show", "kare", "ka bhi", "bhi", "dekh"]
    if any(w in t for w in result_intent_words):
        return False
        
    name_triggers = ["mera naam", "my name is", "maru naam", "hu mara naam", "naam hai", "name is", "i am", "mein hu", "hu ", "maaru naam"]
    if any(p in t for p in name_triggers) or t.startswith("naam "):
        return True
    return False

def check_is_branch_intent(text):
    text = text.lower()
    branch_keywords = [
        "branch", "address", "location", "kaha par hai", "kaha hai", "kidhar hai", 
        "kahan hai", "bctech kaha", "bc tech kaha", "ક્યાં છે", "ક્યાં આવેલું", "સરનામું", "લોકેશન", "શાખા", "पता", "कहाँ है", "लोकेशन"
    ]
    return any(kw in text for kw in branch_keywords)

def check_is_creator_intent(text):
    text = text.lower()
    creator_keywords = ["kisne banaya", "kisne bnaya", "who made you", "who created you", "aapko kisne banaya", "ko kisne banaya"]
    return any(kw in text for kw in creator_keywords)

def check_is_where_from(text):
    text = text.lower().strip()
    where_keywords = ["aap kaha se ho", "tum kaha se ho", "where are you from", "kaha se ho", "apka office kaha hai", "kaise ho", "kya हाल है"]
    return any(kw in text for kw in where_keywords)

def search_student_all_sheets(query_text, df):
    if check_is_name_intro(query_text):
        return []

    if df is None or df.empty or "Student_Name_Std" not in df.columns:
        return []
    
    clean_q = query_text.strip().lower()
    block_list = ["or", "aur", "hi", "hello", "ok", "yes", "no", "hey", "kya", "hai", "a", "an", "the"]
    if clean_q in block_list or len(clean_q) <= 2:
        return []

    if "priya mam" in clean_q or "umesh sir" in clean_q or "sanjay sir" in clean_q or "ajay sir" in clean_q:
        return []

    img_triggers = ["image", "photo", "picture", "wallpaper", "banao", "create", "generate", "tasveer", "draw", "bana do"]
    if any(t in clean_q for t in img_triggers):
        return []

    fillers = [
        "result", "marks", "marx", "kya", "hai", "check", "batao", "bata do", "mera", "meri", "ka", "ki", "ko",
        "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam", "name",
        "show", "chhe", "che", "maru", "maro", "nu", "no", "na", "joiyu", "jovu", "aapo", "mam", "sir", "karo", "kar do", "kare", "dekh", "dikha",
        "મારું", "મારુ", "નામ", "આપો", "છે", "જોવું", "રીઝલ્ટ", "રિઝલ્ટ", "પરિણામ", "ka result", "ka marks", "hai", "my", "is", "ka bhi", "bhi"
    ]
    
    query_clean_words = [w for w in clean_q.split() if w not in fillers]
    search_query_str = " ".join(query_clean_words).strip()
    
    if not search_query_str or len(search_query_str) <= 2:
        return []

    matched = df[df["Student_Name_Std"].astype(str).str.lower().apply(lambda x: any(w == search_query_str or search_query_str in x.split() for w in x.split()))]

    if matched.empty:
        matched = df[df["Student_Name_Std"].astype(str).str.lower().str.contains(r'\b' + re.escape(search_query_str) + r'\b', na=False)]

    if matched.empty:
        matched = df[df["Student_Name_Std"].astype(str).str.lower().str.contains(re.escape(search_query_str), na=False)]

    if matched.empty:
        words = [w for w in query_clean_words if len(w) >= 2]
        if words:
            user_search_signature = " ".join(sorted(list(set(words))))
            matched = df[df["Name_Signature_Std"].astype(str) == user_search_signature]

    if not matched.empty:
        return matched.to_dict(orient="records")
    return []

def clean_ai_response(text):
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()

BRANCH_LINK = "https://sites.google.com/view/bctechcomputer/about-us"

KNOWLEDGE_BASE = f"""
About Bctech Computer Education:
- Institute: Bctech Computer Education
- Official Branch & Location Info Link: {BRANCH_LINK}
- Main Offerings: Professional computer training, practical learning, ISO certified courses, job assistance.
- Popular Courses (Strict Rule: NEVER mention duration in months or course fees/prices):
  1. बेसिक कंप्यूटर (Basic Computer) - Topics: Windows, MS Office, इंटरनेट
  2. ग्राफिक डिज़ाइन (Graphic Designing: CorelDraw, Photoshop, Illustrator) - Topics: लोगो डिज़ाइन, बैनर, फोटो एडिटिंग
  3. एकाउंटिंग & टैली प्राइम (Accounting & Tally Prime) - Topics: बुनियादी लेखा, टैली में लेन-देन
  4. वेब डेवलपमेंट (Web Development) - Topics: HTML, CSS, JavaScript, WordPress
  5. प्रोग्रामिंग (Programming: Python / C++) - Topics: बेसिक से एडवांस, प्रोजेक्ट वर्क
- Location/Address: Surat, Gujarat, India.
- Institute Timing (Class Open & Close Time): Class opens at 7:00 AM and remains active/open until 8:30 PM.
- Batch Timings: 
  - Morning Batches: 7:00 AM to 10:00 AM (Each batch is 1 hour long).
  - Regular/Other Batches: 10:00 AM to 8:30 PM (Each batch is 1.5 hours / 1 hour 30 minutes long).
- Contact Number / WhatsApp Number: 77789 26285
"""

# Render chat history with Read Aloud & Copy buttons
for idx, msg in enumerate(st.session_state.messages):
    is_user = (msg["role"] == "user")
    with st.chat_message(msg["role"], avatar="👤" if is_user else "🤖"):
        st.write(msg["content"])
        if not is_user:
            lang_code = "hi-IN" if st.session_state.current_language == "HINDI" else ("gu-IN" if st.session_state.current_language == "GUJARATI" else "en-US")
            render_voice_and_copy_toolbar(msg["content"], f"hist_{idx}", lang_code)

# Chat input with "Ask..." placeholder
query = st.chat_input("Ask...")

if query:
    clean_q_lower = query.strip().lower()
    lang = update_language_state(query)
    
    # Check if user is asking to open a specific uploaded paper
    paper_requested = None
    for pk, p_info in st.session_state.papers_data.items():
        d_name_lower = p_info.get("display_name", pk).lower()
        if d_name_lower in clean_q_lower:
            paper_requested = pk
            break

    if paper_requested:
        if "lock" in clean_q_lower and "unlock" not in clean_q_lower:
            st.session_state.papers_data[paper_requested]["locked"] = True
            save_papers_db(st.session_state.papers_data)
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👤"):
                st.write(query)
            with st.chat_message("assistant", avatar="🤖"):
                p_disp = st.session_state.papers_data[paper_requested].get("display_name", paper_requested)
                reply = f"🔒 Paper '{p_disp}' has been successfully locked."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                render_voice_and_copy_toolbar(reply, f"lock_ack_{len(st.session_state.messages)}", "hi-IN")
            persist_current_state()
        elif "unlock" in clean_q_lower:
            st.session_state.papers_data[paper_requested]["locked"] = False
            save_papers_db(st.session_state.papers_data)
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👤"):
                st.write(query)
            with st.chat_message("assistant", avatar="🤖"):
                p_disp = st.session_state.papers_data[paper_requested].get("display_name", paper_requested)
                reply = f"🟢 Paper '{p_disp}' has been successfully unlocked."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                render_voice_and_copy_toolbar(reply, f"unlock_ack_{len(st.session_state.messages)}", "hi-IN")
            persist_current_state()
        else:
            p_info = st.session_state.papers_data[paper_requested]
            d_name = p_info.get("display_name", paper_requested)

            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👤"):
                st.write(query)

            with st.chat_message("assistant", avatar="🤖"):
                if p_info["locked"]:
                    reply = f"Sorry! The paper '{d_name.upper()}' is currently the teacher's permission cannot be opened."
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    render_voice_and_copy_toolbar(reply, f"locked_p_{len(st.session_state.messages)}", "hi-IN")
                else:
                    st.write(f"📂 Here is your requested paper: **{d_name}**")
                    mtype = p_info.get("mime", "")
                    if "image/" in mtype:
                        st.image(p_info["path"], caption=d_name, use_container_width=True)
                        reply = f"Displayed large image paper: {d_name}"
                    else:
                        with open(p_info["path"], "rb") as pf:
                            pdf_bytes = pf.read()
                        st.download_button(
                            label=f"📂 Open Paper: {d_name}",
                            data=pdf_bytes,
                            file_name=p_info["filename"],
                            mime="application/pdf",
                            key=f"view_btn_{paper_requested}_{len(st.session_state.messages)}"
                        )
                        reply = f"Generated paper view button for: {d_name}"
                    st.session_state.messages.append({"role": "assistant", "content": reply})
            persist_current_state()

    else:
        # Normal chat/result queries
        if clean_q_lower in ["or", "aur", "hi", "hello", "ok", "hey", "h", "k"]:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👤"):
                st.write(query)
            with st.chat_message("assistant", avatar="🤖"):
                if lang == "HINDI":
                    reply = "हाँ, बताइए! मैं आपकी क्या मदद कर सकता हूँ? 😊"
                elif lang == "GUJARATI":
                    reply = "હા, જણાવો! હું આપને કેવી રીતે મદદ કરી શકું? 😊"
                else:
                    reply = "Yes, please tell me! How can I help you? 😊"
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                render_voice_and_copy_toolbar(reply, f"hard_block_{len(st.session_state.messages)}", lang_code)
            persist_current_state()
        else:
            st.session_state.messages.append({"role": "user", "content": query})
            
            with st.chat_message("user", avatar="👤"):
                st.write(query)

            df_sheet, err = load_all_sheets_data()
            
            with st.chat_message("assistant", avatar="🤖"):
                if err:
                    st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
                
                elif check_is_name_intro(query):
                    name_match = re.search(r"(?:mera naam|my name is|maru naam|hu mara naam|naam hai|name is|i am|hu|maaru naam)\s+([a-zA-Z\u0900-\u097F]+)", query, re.IGNORECASE)
                    if not name_match:
                        words = [w for w in query.split() if w.lower() not in ["mera", "naam", "hai", "is", "my", "name", "hu", "i", "am", "ka", "ki"]]
                        username = words[0].capitalize() if words else "User"
                    else:
                        username = name_match.group(1).capitalize()
                    
                    st.session_state.last_mentioned_name = username.lower()

                    if lang == "GUJARATI":
                        reply = f"નમસ્તે {username}! BC Tech માં આપનું સ્વાગત છે. જણાવો, હું આપને કેવી રીતે મદદ કરી શકું? 😊"
                    elif lang == "HINDI":
                        reply = f"नमस्ते {username}! BC Tech Computer Education में आपका स्वागत है। बताइए, मैं आपकी कैसे मदद कर सकता हूँ? 😊"
                    else:
                        reply = f"Hello {username}! Welcome to BC Tech Computer Education. How can I help you today? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"name_reply_{len(st.session_state.messages)}", lang_code)

                elif check_is_where_from(query):
                    if lang == "GUJARATI":
                        reply = "હું BC Tech Computer Education નો અસિસ્ટન્ટ છું, અને આપણી સંસ્થા સુરત, ગુજરાત, ભારતમાં આવેલી છે."
                    elif lang == "HINDI":
                        if "kaise ho" in clean_q_lower or "kaisa hai" in clean_q_lower:
                            reply = "मैं बहुत अच्छा हूँ! बताइए, मैं BC Tech Computer Education में आपकी कैसे मदद कर सकता हूँ? 😊"
                        else:
                            reply = "मैं BC Tech Computer Education का AI असिस्टेंट हूँ, और हमारी संस्था सूरत, गुजरात, भारत में स्थित है।"
                    else:
                        if "how are you" in clean_q_lower:
                            reply = "I am doing well, thank you! How can I help you with BC Tech Computer Education today?"
                        else:
                            reply = "I am the AI Assistant for BC Tech Computer Education, located in Surat, Gujarat, India."
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"where_{len(st.session_state.messages)}", lang_code)

                elif query.strip().lower() in ["gujarati", "gujrati", "gujarati ma", "gujarati mein baat karte hai", "gujarati main baat karte hai ok", "gujarati ma vaat kariye"]:
                    reply = "ચોક્કસ! હવે આપણે ગુજરાતીમાં વાત કરીશું. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    render_voice_and_copy_toolbar(reply, f"ack_{len(st.session_state.messages)}", "gu-IN")

                elif query.strip().lower() in ["hindi", "in hindi", "hindi me", "hindi main baat karo", "hindi me baat karte hai"]:
                    reply = "ज़रूर! अब हम हिंदी में बात करेंगे। मैं आपकी क्या सहायता कर सकता हूँ? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    render_voice_and_copy_toolbar(reply, f"ack_{len(st.session_state.messages)}", lang_code)

                elif is_greeting(query):
                    if lang == "GUJARATI":
                        reply = "નમસ્તે! BC Tech માં આપનું સ્વાગત છે. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
                    elif lang == "HINDI":
                        reply = "नमस्ते! BC Tech Computer Education में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूँ? 😊"
                    else:
                        reply = "Hello! Welcome to BC Tech Computer Education. How can I help you today? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"greet_{len(st.session_state.messages)}", lang_code)

                elif check_is_branch_intent(query):
                    if lang == "GUJARATI":
                        reply = f"BC Tech Computer Education સુરત, ગુજરાત, ભારતમાં આવેલું છે. વધુ વિગતો અને અન્ય શાખાના પત્તા માટે અધિકૃત વેબસાઇટની મુલાકાત લો:\n🔗 {BRANCH_LINK}\n\nસંપર્ક:\n📞 ફોન: 77789 26285\n📱 વ્હોટ્સએપ: 77789 26285"
                    elif lang == "HINDI":
                        reply = f"BC Tech Computer Education सूरत, गुजरात, भारत में स्थित है। अधिक विवरण और अन्य शाखाओं के पते के लिए आप आधिकारिक वेबसाइट पर जा सकते हैं:\n🔗 {BRANCH_LINK}\n\nसंपर्क:\n📞 फ़ोन: 77789 26285\n📱 व्हाट्सएप: 77789 26285"
                    else:
                        reply = f"BC Tech Computer Education is located in Surat, Gujarat, India. For more details and branch addresses, you can visit the official website:\n🔗 {BRANCH_LINK}\n\nContact:\n📞 Phone: 77789 26285\n📱 WhatsApp: 77789 26285"
                    
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"branch_{len(st.session_state.messages)}", lang_code)

                elif check_is_creator_intent(query):
                    if lang == "GUJARATI":
                        reply = "મને BC Tech Computer Education ના એડમિન અને ડેવલपर દ્વારા બનાવવામાં આવ્યો છે."
                    elif lang == "HINDI":
                        reply = "मुझे BC Tech Computer Education के डेवलपर और एडमिन द्वारा बनाया गया है।"
                    else:
                        reply = "I was created by the developer and admin of BC Tech Computer Education."
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"creator_{len(st.session_state.messages)}", lang_code)

                else:
                    search_query_to_use = query
                    result_intent_words = ["result", "marks", "exam", "mera", "meri", "score", "reult", "rizalt", "marksheet", "show", "kare", "ka bhi", "bhi", "dekh", "dikha"]
                    
                    if any(w in query.lower() for w in result_intent_words):
                        if "mera" in query.lower() or "meri" in query.lower() or "ka bhi" in query.lower() or "kare" in query.lower() or "dekh" in query.lower() or "dikha" in query.lower() or query.strip().lower() in ["result", "exam", "marks"]:
                            if st.session_state.last_mentioned_name:
                                search_query_to_use = st.session_state.last_mentioned_name

                    matched_records = search_student_all_sheets(search_query_to_use, df_sheet)
                    
                    if matched_records:
                        full_reply = ""
                        for record in matched_records:
                            f_name = record.get("Student_Name_Std", "")
                            f_exam = record.get("Exam_Std", "Course")
                            f_teacher = record.get("_Sheet_Tab", "Teacher")
                            
                            valid_theory = []
                            valid_practical = []
                            
                            for k, v in record.items():
                                val_str = str(v).strip()
                                if val_str and val_str.lower() != "n/a" and val_str.lower() != "nan" and val_str != "0":
                                    try:
                                        m_val = float(val_str)
                                        if "theory" in k.lower():
                                            valid_theory.append((k, m_val))
                                        elif "practical" in k.lower():
                                            valid_practical.append((k, m_val))
                                    except ValueError:
                                        pass
                            
                            tot_theory = int(sum([item[1] for item in valid_theory])) if valid_theory else 0
                            tot_prac = int(sum([item[1] for item in valid_practical])) if valid_practical else 0
                            total_obtained = tot_theory + tot_prac
                            
                            valid_tests_count = len(valid_theory) + len(valid_practical)
                            max_total = valid_tests_count * 50 if valid_tests_count > 0 else 50
                            percentage = round((total_obtained / max_total) * 100, 2) if max_total > 0 else 0

                            motivational_tip = ""
                            if percentage >= 80:
                                if lang == "GUJARATI":
                                    motivational_tip = "ખૂબ જ સરસ! તમારું પરિણામ ઉત્કૃષ્ટ છે. આવી જ મહેનત ચાલુ રાખો!"
                                elif lang == "HINDI":
                                    motivational_tip = "बहुत बढ़िया! आपका प्रदर्शन शानदार है। इसी तरह कड़ी मेहनत जारी रखें!"
                                else:
                                    motivational_tip = "Outstanding performance! Keep up the brilliant work!"
                            elif percentage >= 50:
                                if lang == "GUJARATI":
                                    motivational_tip = "સરસ પ્રયાસ! તમે સારી મહેનત કરી છે, થોડી વધુ મહેનતથી તમે ટોપ પર પહોંચી શકો છો."
                                elif lang == "HINDI":
                                    motivational_tip = "अच्छा प्रयास! आपने अच्छी मेहनत की है, थोड़ी और लगन से आप और भी बेहतर कर सकते हैं।"
                                else:
                                    motivational_tip = "Good effort! With a little more practice, you can achieve even higher goals."
                            else:
                                if lang == "GUJARATI":
                                    motivational_tip = "હિંમત ન હારો! નિષ્ફળતા જ સફળતાની પહેલી સીડી છે. થોડી વધુ પ્રેક્ટિસ કરો, તમે ચોક્કસ સફળ થશો!"
                                elif lang == "HINDI":
                                    motivational_tip = "निराश न हों! असफलता ही सफलता की पहली सीढ़ी है। थोड़ी और मेहनत करें, आप जरूर सफल होंगे!"
                                else:
                                    motivational_tip = "Don't get discouraged! Every setback is a setup for a comeback. Keep practicing!"

                            if lang == "GUJARATI":
                                full_reply += f"વિદ્યાર્થીનું નામ: {f_name}\nપરીક્ષાનું નામ: {f_exam}\nશિક્ષકનું નામ: {f_teacher}\n\n"
                                if valid_theory:
                                    full_reply += "થિયરી ટેસ્ટ:\n"
                                    for tk, tv in valid_theory:
                                        full_reply += f"- {tk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- કુલ થિયરી: {tot_theory}\n\n"
                                if valid_practical:
                                    full_reply += "પ્રૅક્ટિકલ ટેસ્ટ:\n"
                                    for pk, pv in valid_practical:
                                        full_reply += f"- {pk.capitalize()}: {int(pv) if pv.is_integer() else pv}\n"
                                    full_reply += f"- કુલ પ્રૅક્ટિકલ: {tot_prac}\n\n"
                                full_reply += f"કુલ ગુણ: {total_obtained} / {max_total}\n"
                                full_reply += f"ટકાવારી: {percentage}%\n\n"
                                full_reply += f"{motivational_tip}\n\n"
                            elif lang == "HINDI":
                                full_reply += f"विद्यार्थी का नाम: {f_name}\nपरीक्षा का नाम: {f_exam}\nशिक्षक का नाम: {f_teacher}\n\n"
                                if valid_theory:
                                    full_reply += "थ्योरी टेस्ट:\n"
                                    for tk, tv in valid_theory:
                                        full_reply += f"- {tk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- कुल थ्योरी: {tot_theory}\n\n"
                                if valid_practical:
                                    full_reply += "प्रैक्टिकल टेस्ट:\n"
                                    for pk, pv in valid_practical:
                                        full_reply += f"- {pk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                        full_reply += f"- कुल प्रैक्टिकल: {tot_prac}\n\n"
                                full_reply += f"कुल अंक: {total_obtained} / {max_total}\n"
                                full_reply += f"प्रतिशत: {percentage}%\n\n"
                                full_reply += f"{motivational_tip}\n\n"
                            else:
                                full_reply += f"Student Name: {f_name}\nExam Name: {f_exam}\nTeacher Name: {f_teacher}\n\n"
                                if valid_theory:
                                    full_reply += "Theory Tests:\n"
                                    for tk, tv in valid_theory:
                                        full_reply += f"- {tk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- Total Theory: {tot_theory}\n\n"
                                if valid_practical:
                                    full_reply += "Practical Tests:\n"
                                    for pk, pv in valid_practical:
                                        full_reply += f"- {pk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                        full_reply += f"- Total Practical: {tot_prac}\n\n"
                                full_reply += f"Total Marks: {total_obtained} / {max_total}\n"
                                full_reply += f"Percentage: {percentage}%\n\n"
                                full_reply += f"{motivational_tip}\n\n"

                        st.markdown(full_reply.strip())
                        st.session_state.messages.append({"role": "assistant", "content": full_reply.strip()})
                        run_aerial_celebration()
                        lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                        render_voice_and_copy_toolbar(full_reply.strip(), f"ast_curr_{len(st.session_state.messages)}", lang_code)
                    else:
                        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                        
                        # --- LIVE IST TIME & DATE CALCULATION ---
                        ist_zone = timezone(timedelta(hours=5, minutes=30))
                        current_ist_dt = datetime.now(ist_zone)
                        current_time_str = current_ist_dt.strftime("%B %d, %Y, %I:%M %p")
                        current_year_str = current_ist_dt.strftime("2026") # Locked strictly to current true current year 2026
                        
                        lang_name = "Gujarati" if lang == "GUJARATI" else ("Hindi" if lang == "HINDI" else "English")
                        
                        system_prop = f"""
                        You are an expert, highly knowledgeable, and precise AI Assistant for BC Tech Computer Education, Surat, Gujarat, India.
                        Current Exact Date and Time (IST - Indian Standard Time): {current_time_str}. Current Year: {current_year_str}.
                        
                        CRITICAL CALENDAR & FESTIVAL ACCURACY RULE (MOST IMPORTANT):
                        - The current year is strictly 2026 ({current_year_str}). 
                        - When a user asks about any festival date (like Diwali, Holi, Rakshabandhan, Eid, etc.), you MUST provide the correct date for the current year 2026 unless they explicitly ask for a different year (e.g., asking for 2027).
                        - For example, Diwali in 2026 falls on November 8, 2026. Holi in 2026 falls on March 3, 2026. Do NOT output wrong dates like October 2026 for Diwali. Always verify your calendar facts accurately.
                        
                        CRITICAL SOFTWARE TUTORIAL & PRACTICAL INSTRUCTION RESTRICTION (STRICTEST RULE):
                        - You are strictly FORBIDDEN from explaining, teaching, or giving tutorials or step-by-step instructions for ANY software (e.g. Photoshop, CorelDraw, Tally, Excel, Word, Coding, Python, C++, Web Development, Video Editing, etc.).
                        - If a user asks HOW to do something in software (e.g., "passport photo kaise banaye", "tally me entry kaise kare", "python me code kaise likhe", "design kaise kare"):
                          DO NOT provide any tutorial, steps, or software solutions.
                          INSTEAD, you must politely inform them that practical training and guidance are provided directly at the institute, and tell them to contact our branch or visit our website:
                          
                          - In Hindi: "इस विषय में प्रैक्टिकल ट्रेनिंग और सीखने के लिए आप हमारी ब्रांच से संपर्क कर सकते हैं या आधिकारिक वेबसाइट पर जा सकते हैं।\n\nसंपर्क:\n📞 फ़ोन: 77789 26285\n📱 व्हाट्सएप: 77789 26285\n🌐 वेबसाइट: {BRANCH_LINK}"
                          - In Gujarati: "આ વિષયમાં પ્રેક્ટિકલ તાલીમ અને માર્ગદર્શન માટે આપ અમારી બ્રાન્ચનો સંપર્ક કરી શકો છો અથવા વેબસાઇટની મુલાકાત લઈ શકો છો.\n\nસંપર્ક:\n📞 ફોન: 77789 26285\n📱 વ્હોટ્સએપ: 77789 26285\n🌐 વેબસાઇટ: {BRANCH_LINK}"
                          - In English: "For practical training and learning on this software, you can contact our branch or visit our official website:\n\nContact:\n📞 Phone: 77789 26285\n📱 WhatsApp: 77789 26285\n🌐 Website: {BRANCH_Link}"
                        
                        CRITICAL TIMINGS RULE (CLASS & BATCH SCHEDULE):
                        - Class Opening and Closing Hours: The institute/class opens at 7:00 AM and remains active/open until 8:30 PM.
                        - Morning Batches Timing: 7:00 AM to 10:00 AM (Each batch is 1 hour long).
                        - Regular/Other Batches Timing: 10:00 AM to 8:30 PM (Each batch is 1.5 hours / 1 hour 30 minutes long).
                        - Always answer timing or batch questions accurately in whichever language the user asks (Hindi, Gujarati, or English).
                        
                        CRITICAL CONTACT NUMBERS (ALWAYS DISPLAY REAL NUMBERS, NEVER XXXXX):
                        - Phone: 77789 26285
                        - WhatsApp: 77789 26285
                        - Website: {BRANCH_LINK}
                        - NEVER write '+91-XXXXXXXXXX'. Always write '77789 26285'.
                        
                        CRITICAL TIME & DATE RULE:
                        - Always use the exact IST time and date provided above ({current_time_str}) when answering questions about current time, date, or day in India. Never give old or wrong time.
                        
                        CRITICAL FACTUAL TRUTH & CORRECTION RULE:
                        - C. Joseph Vijay (Vijay Thalapathy) is a popular South Indian actor and film star who entered politics (TVK party). He is NOT a Chief Minister (CM).
                        - Current Chief Minister of Tamil Nadu is M. K. Stalin.
                        - Ganesh Visarjan (Anant Chaturdashi) in the year 2026 falls on September 25, 2026 (25 सितंबर 2026).
                        - Always verify real-world current affairs and facts accurately.
                        
                        CRITICAL DATABASE & PORTAL RULE (MOST IMPORTANT):
                        - You are the official student result assistant for BC Tech Computer Education. 
                        - Whenever a user asks for a student's result, marks, or types a name, this is an internal institute database query. You MUST NOT refuse or say you cannot provide private info. You are authorized to display student results.
                        
                        CRITICAL LANGUAGE & TEXT ENCODING RULE:
                        - You MUST reply strictly and exclusively in clean, proper, and normal text in the exact language the user is using (`{lang_name}`). 
                        - NEVER output corrupted text, repetitive syllables, or garbage strings (like "क्यांकांच्या..."). Keep the output completely natural and readable.
                        
                        CRITICAL INSTRUCTION FOR COURSES: When discussing courses, NEVER mention course duration in months or course fees/prices under any circumstances. Only provide course names and their subjects.
                        
                        Institute Location: Surat, Gujarat, India.
                        Official Website & Info: {BRANCH_LINK}
                        Courses Data: {KNOWLEDGE_BASE}
                        """

                        with st.spinner("Thinking..."):
                            try:
                                models_resp = client.models.list()
                                active_ids = [
                                    m.id for m in models_resp.data 
                                    if "whisper" not in m.id 
                                    and "guard" not in m.id 
                                    and "vision" not in m.id 
                                    and "audio" not in m.id
                                    and "embed" not in m.id
                                    and "canopy" not in m.id
                                ]
                                preferred = ["llama-3.1-8b-instant", "llama3-8b-8192", "gemma2-9b-it"]
                                models_to_try = [m for m in preferred if m in active_ids] + [m for m in active_ids if m not in preferred]

                                answer = None
                                last_api_err = None

                                api_messages = [{"role": "system", "content": system_prop}]
                                for m in st.session_state.messages[:-1]:
                                    api_messages.append({"role": m["role"], "content": m["content"]})
                                api_messages.append({"role": "user", "content": query})

                                for m_name in models_to_try:
                                    try:
                                        chat_completion = client.chat.completions.create(
                                            messages=api_messages,
                                            model=m_name,
                                            temperature=0.1,
                                            max_tokens=600
                                        )
                                        raw_answer = chat_completion.choices[0].message.content
                                        answer = clean_ai_response(raw_answer)
                                        if answer and len(answer) > 2:
                                            break
                                    except Exception as ex:
                                        last_api_err = str(ex)
                                        continue
                                
                                if answer:
                                    st.markdown(answer)
                                    st.session_state.messages.append({"role": "assistant", "content": answer})
                                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                                    render_voice_and_copy_toolbar(answer, f"ast_curr_{len(st.session_state.messages)}", lang_code)
                                else:
                                    st.error(f"API Error: {last_api_err}")
                            except Exception as e:
                                st.error(f"Error: {e}")
        persist_current_state()
