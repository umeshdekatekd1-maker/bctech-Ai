import json
import os
from datetime import datetime, timezone, timedelta
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import pandas as pd
import requests
import io
import re
import uuid
import random
import time
import base64

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

# --- BULLET-PROOF PERSISTENT STORAGE DB MANAGER ---
DB_FILE = "bctech_chat_storage.json"
PAPERS_META_FILE = "bctech_papers_store.json"
BACKUP_PAPERS_FILE = "bctech_papers_backup.json"
GAME_ROOMS_FILE = "bctech_game_rooms.json"

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
    data = {}
    if os.path.exists(PAPERS_META_FILE):
        try:
            with open(PAPERS_META_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    if not data and os.path.exists(BACKUP_PAPERS_FILE):
        try:
            with open(BACKUP_PAPERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(PAPERS_META_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return data

def save_papers_db(papers_db):
    try:
        with open(PAPERS_META_FILE, "w", encoding="utf-8") as f:
            json.dump(papers_db, f, ensure_ascii=False, indent=2)
        with open(BACKUP_PAPERS_FILE, "w", encoding="utf-8") as f:
            json.dump(papers_db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_room_store():
    if os.path.exists(GAME_ROOMS_FILE):
        try:
            with open(GAME_ROOMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_room_store(rooms):
    try:
        with open(GAME_ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(rooms, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if "papers_data" not in st.session_state:
    st.session_state.papers_data = load_papers_db()
else:
    disk_papers = load_papers_db()
    if disk_papers and not st.session_state.papers_data:
        st.session_state.papers_data = disk_papers

if "game_state" not in st.session_state:
    st.session_state.game_state = "IDLE"

if "active_room_code" not in st.session_state:
    st.session_state.active_room_code = None

if "player_role" not in st.session_state:
    st.session_state.player_role = None

query_params = st.query_params
if "room_code" in query_params and query_params["room_code"] and st.session_state.game_state == "IDLE":
    r_code = query_params["room_code"].strip().upper()
    all_rooms = load_room_store()
    if r_code in all_rooms:
        st.session_state.active_room_code = r_code
        st.session_state.game_state = all_rooms[r_code].get("game_state", "PLAYING")
        if "role" in query_params:
            st.session_state.player_role = query_params["role"]

# QUESTION BANK
QUESTION_BANK = {
    "Basic Computer & Internet": {
        "pool_1": [
            {"q": "कंप्यूटर में किसी फाइल को कॉपी करने की शॉर्टकट की क्या है?", "options": ["Ctrl + C", "Ctrl + V", "Ctrl + X", "Ctrl + S"], "answer": "Ctrl + C"},
            {"q": "WWW का पूरा नाम क्या है?", "options": ["World Wide Web", "World Web Wide", "Web World Wide", "Wide World Web"], "answer": "World Wide Web"},
            {"q": "इनमें से कौन सा एक आउटपुट डिवाइस है?", "options": ["कीबोर्ड", "माउस", "मॉनिटर", "स्कैनर"], "answer": "मॉनिटर"},
            {"q": "कंप्यूटर का दिमाग किसे कहा जाता है?", "options": ["RAM", "CPU", "Hard Disk", "Monitor"], "answer": "CPU"},
            {"q": "इंटरनेट का जनक किसे कहा जाता है?", "options": ["विंट सर्फ", "बिल गेट्स", "स्टीव जॉब्स", "मार्क जुकरबर्ग"], "answer": "विंट सर्फ"}
        ]
    }
}

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

def remove_emojis(text):
    return re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]|[\uD800-\uDBFF][\uDC00-\uDFFF]|[\U0001f300-\U0001f5ff]|[\U0001f600-\U0001f64f]|[\U0001f680-\U0001f6ff]|[\u2600-\u26ff]|[\u2700-\u27bf]|[\U0001f900-\U0001f9ff]|[\U0001fa70-\U0001faff]|[\u231a-\u231b]|[\u23e9-\u23ec]|[\u23f0]|[\u23f3]|[\u25aa-\u25ab]|[\u25b6]|[\u25c0]|[\u25fb-\u25fe]|[\u2600-\u27ef]|[\u2b50]|[\u2b55]|[\u3030]|[\u303d]|[\u3297]|[\u3299]', '', text)

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
    st.session_state.game_state = "IDLE"
    st.session_state.active_room_code = None
    
    new_id = str(uuid.uuid4())
    st.query_params["chat_id"] = new_id
    persist_current_state()

def restore_chat(idx):
    if idx < len(st.session_state.recent_chats):
        st.session_state.messages = list(st.session_state.recent_chats[idx]["messages"])
        st.session_state.game_state = "IDLE"
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

# Sidebar - Admin Panel with Safe Paper Handling
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
                    file_bytes = uploaded_file.getvalue()
                    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
                    
                    file_ext = os.path.splitext(original_filename)[1].lower()
                    mimetype = "application/pdf" if file_ext == ".pdf" else (f"image/{file_ext[1:]}" if file_ext in [".jpg", ".jpeg", ".png"] else "application/octet-stream")

                    st.session_state.papers_data[p_key] = {
                        "display_name": base_name,
                        "filename": original_filename,
                        "data_b64": encoded_file,
                        "mime": mimetype,
                        "locked": True
                    }
                    save_papers_db(st.session_state.papers_data)
                    st.success(f"Paper '{base_name}' successfully saved permanently!")
            
            if st.session_state.papers_data:
                st.markdown("**Existing Papers Status:**")
                for pk, p_info in list(st.session_state.papers_data.items()):
                    d_name = p_info.get("display_name", pk)
                    is_locked = p_info.get("locked", True)
                    status_str = "🔒 Locked" if is_locked else "🟢 Unlocked"
                    
                    st.text(f"{d_name} ({status_str})")
                    col_t, col_d = st.columns(2)
                    
                    if col_t.button("Toggle Lock", key=f"tog_{pk}"):
                        st.session_state.papers_data[pk]["locked"] = not is_locked
                        save_papers_db(st.session_state.papers_data)
                        st.rerun()
                        
                    if col_d.button("🗑️ Delete", key=f"del_{pk}"):
                        del st.session_state.papers_data[pk]
                        save_papers_db(st.session_state.papers_data)
                        st.success(f"Deleted '{d_name}' successfully!")
                        st.rerun()
        elif admin_pass != "":
            st.error("Incorrect Password!")

    st.markdown("---")
    st.markdown("🌐 [Official Website](https://sites.google.com/view/bctechcomputer)")
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
        "kab", "mein", "main", "hai", "kya hai", "kon hai", "kaha ke hai", "ka bhi", "kare", "show", "dekh", "samay", "time", "date", "tarikh", "open", "class", "batch", "chalu", "band", "timing"
    ]
    words = text_clean.split()
    
    english_indicators = ["my name is", "what is", "how are", "hello", "hi", "where is", "can you", "thank you", "result of", "timing", "batch", "class"]
    if any(ind in text_clean for ind in english_indicators) and not any(w in hindi_romanized for w in words):
        st.session_state.current_language = "ENGLISH"
        return "ENGLISH"
        
    if any(w in hindi_romanized for w in words):
        st.session_state.current_language = "HINDI"
        return "HINDI"
        
    english_common = ["name", "is", "the", "and", "you", "your", "what", "where", "how", "am", "time", "date", "open", "timing", "batch", "class"]
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
- Popular Courses:
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
"""

# Render chat history with Read Aloud & Copy buttons
for idx, msg in enumerate(st.session_state.messages):
    is_user = (msg["role"] == "user")
    with st.chat_message(msg["role"], avatar="👤" if is_user else "🤖"):
        st.write(msg["content"])
        if not is_user:
            lang_code = "hi-IN" if st.session_state.current_language == "HINDI" else ("gu-IN" if st.session_state.current_language == "GUJARATI" else "en-US")
            render_voice_and_copy_toolbar(msg["content"], f"hist_{idx}", lang_code)

query = st.chat_input("Ask...")

if query:
    clean_q_lower = query.strip().lower()
    lang = update_language_state(query)
    
    if "play game" in clean_q_lower or "quiz" in clean_q_lower or "game" in clean_q_lower:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="👤"):
            st.write(query)
        st.session_state.game_state = "CREATING"
        bot_reply = "बहुत बढ़िया! 🧠 BC Tech Brain Battle शुरू करने के लिए नीचे दिए गए Battle Zone से अपना बैटल ज़ोन बनाएं या जुड़ें।"
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(bot_reply)
        persist_current_state()
        st.rerun()

    paper_requested = None
    for pk, p_info in st.session_state.papers_data.items():
        d_name_lower = p_info.get("display_name", pk).lower()
        if d_name_lower in clean_q_lower:
            paper_requested = pk
            break

    if paper_requested:
        p_info = st.session_state.papers_data[paper_requested]
        d_name = p_info.get("display_name", paper_requested)
        is_locked = p_info.get("locked", False)

        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="👤"):
            st.write(query)

        with st.chat_message("assistant", avatar="🤖"):
            if is_locked:
                reply = "⏳ This question paper is currently unavailable. Please ask your teacher for access."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                render_voice_and_copy_toolbar(reply, f"locked_p_{len(st.session_state.messages)}", "hi-IN")
            elif "data_b64" not in p_info:
                reply = f"⚠️ The paper '{d_name}' file data is missing. Please re-upload it from the Admin panel."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                st.write(f"📂 Here is your requested paper: **{d_name}**")
                mtype = p_info.get("mime", "")
                try:
                    raw_bytes = base64.b64decode(p_info["data_b64"])
                    if "image/" in mtype:
                        st.image(raw_bytes, caption=d_name, use_container_width=True)
                        reply = f"Displayed large image paper: {d_name}"
                    else:
                        st.download_button(
                            label=f"📂 Open Paper: {d_name}",
                            data=raw_bytes,
                            file_name=p_info.get("filename", f"{d_name}.pdf"),
                            mime="application/pdf",
                            key=f"view_btn_{paper_requested}_{len(st.session_state.messages)}"
                        )
                        reply = f"Generated paper view button for: {d_name}"
                except Exception as e:
                    reply = f"Error loading file for {d_name}: {e}"
                    st.error(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        persist_current_state()

    else:
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
                    render_voice_and_copy_toolbar(reply, f"ack_{len(st.session_state.messages)}", lang_code)

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
                        reply = f"BC Tech Computer Education સુરત, ગુજરાત, ભારતમાં આવેલું છે. વધુ વિગતો અને અન્ય શાખાના પત્તા માટે અધિકૃત વેબસાઇટની મુલાકાત લો:\n🔗 {BRANCH_LINK}"
                    elif lang == "HINDI":
                        reply = f"BC Tech Computer Education सूरत, गुजरात, भारत में स्थित है। अधिक विवरण और अन्य शाखाओं के पते के लिए आप आधिकारिक वेबसाइट पर जा सकते हैं:\n🔗 {BRANCH_LINK}"
                    else:
                        reply = f"BC Tech Computer Education is located in Surat, Gujarat, India. For more details and branch addresses, you can visit the official website:\n🔗 {BRANCH_LINK}"
                    
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"branch_{len(st.session_state.messages)}", lang_code)

                elif check_is_creator_intent(query):
                    if lang == "GUJARATI":
                        reply = f"મને BC Tech Computer Education ના એડમિન અને ડેવલपर દ્વારા બનાવવામાં આવ્યો છે."
                    elif lang == "HINDI":
                        reply = f"मुझे BC Tech Computer Education के डेवलपर और एडमिन द्वारा बनाया गया है।"
                    else:
                        reply = f"I was created by the developer and admin of BC Tech Computer Education."
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
                                    motivational_tip = "निराश न हों! असफलता ही सफलता की पहली सीढ़ी है। थोड़ी और मेहनत करें, आप जरूर सफल होंगे!"
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
                                        full_reply += f"- {pk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
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
                        
                        ist_zone = timezone(timedelta(hours=5, minutes=30))
                        current_ist_dt = datetime.now(ist_zone)
                        
                        days_map_hi = {"Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार", "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"}
                        months_map_hi = {1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून", 7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर"}
                        
                        eng_day = current_ist_dt.strftime("%A")
                        hi_day = days_map_hi.get(eng_day, eng_day)
                        hi_month = months_map_hi.get(current_ist_dt.month, "")
                        formatted_date_hi = f"{current_ist_dt.day} {hi_month} {current_ist_dt.year}, {hi_day}"
                        formatted_date_en = current_ist_dt.strftime("%A, %B %d, %Y")
                        formatted_time = current_ist_dt.strftime("%I:%M %p")
                        
                        system_prop = f"""
                        You are an expert, highly knowledgeable, fluent, and precise AI Assistant for BC Tech Computer Education, Surat, Gujarat, India.
                        
                        CRITICAL LANGUAGE & GRAMMAR RULE:
                        - Always respond in flawless, natural, and grammatically correct Hindi or Gujarati depending on the user's language. Never write broken or ungrammatical sentences (tuti-futi hindi). Ensure high linguistic quality.
                        
                        CRITICAL LIVE DATE & FESTIVAL ACCURACY INSTRUCTIONS:
                        - Current Live Exact Date and Time (IST): {formatted_date_en} at {formatted_time}.
                        - Today in Hindi: आज {formatted_date_hi} है, और समय {formatted_time} हो रहा है।
                        - When a user asks about any festival, date, or tithi (e.g., Raksha Bandhan 2027, Anant Chaturdashi, etc.), you must verify calculations precisely according to the Hindu Panchang or Gregorian calendar for the target year. For instance, Raksha Bandhan in 2027 falls on August 17, 2027 (Tuesday). Never guess or provide random incorrect dates. Always double-check accurate calendar data.
                        
                        CRITICAL SOFTWARE TUTORIAL & PRACTICAL INSTRUCTION RESTRICTION (STRICTEST RULE):
                        - You are strictly FORBIDDEN from explaining, teaching, or giving tutorials or step-by-step instructions for ANY software.
                        - If a user asks HOW to do something in software, politely inform them to contact our branch or visit our website:
                          - In Hindi: "इस विषय में प्रैक्टिकल ट्रेनिंग और सीखने के लिए आप हमारी ब्रांच से संपर्क कर सकते हैं या आधिकारिक वेबसाइट पर जा सकते हैं。\n\nवेबसाइट: {BRANCH_LINK}"
                          - In Gujarati: "આ વિષયમાં પ્રેક્ટિકલ તાલીમ અને માર્ગદર્શન માટે આપ અમારી બ્રાન્चનો સંપર્ક કરી શકો છો અથવા વેબસાઇટની મુલાકાत લઈ શકો છો.\n\nવેબસાઇટ: {BRANCH_LINK}"
                          - In English: "For practical training and learning on this software, you can contact our branch or visit our official website:\n\nWebsite: {BRANCH_LINK}"
                        
                        CRITICAL TIMINGS RULE:
                        - Class Opening and Closing Hours: 7:00 AM to 8:30 PM.
                        - Morning Batches Timing: 7:00 AM to 10:00 AM (1 hour long).
                        - Regular Batches Timing: 10:00 AM to 8:30 PM (1.5 hours long).
                        
                        CRITICAL INSTRUCTION FOR COURSES: NEVER mention course duration in months or course fees/prices under any circumstances.
                        
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
                                        
                                answer = answer.replace("{BRANCH_Link}", BRANCH_LINK)
                                
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

# ---------------------------------------------------------
# 🧠 BC Tech Brain Battle - BATTLE ZONE ARENA
# ---------------------------------------------------------
if st.session_state.game_state in ["CREATING", "WAITING", "CATEGORY", "PLAYING", "LEVEL_TRANSITION", "RESULT"]:
    st.markdown("---")
    
    rooms = load_room_store()
    curr_room_code = st.session_state.active_room_code
    my_role = st.session_state.player_role

    if curr_room_code and curr_room_code in rooms:
        room_info = rooms[curr_room_code]
        p1_name = room_info.get("p1_name", "")
        p2_name = room_info.get("p2_name", "")
        category = room_info.get("category", "")
        current_level = room_info.get("current_level", 1)
        current_q_index = room_info.get("current_q_index", 0)
        p1_score = room_info.get("p1_score", 0)
        p2_score = room_info.get("p2_score", 0)
        turn = room_info.get("turn", 1)
        shared_game_state = room_info.get("game_state", "WAITING")
        history_log = room_info.get("history_log", [])
        
        if "question_start_time" not in room_info:
            room_info["question_start_time"] = time.time()
            save_room_store(rooms)
        q_start_time = room_info.get("question_start_time", time.time())
    else:
        p1_name, p2_name, category, current_level, current_q_index, p1_score, p2_score, turn, shared_game_state, history_log = "", "", "", 1, 0, 0, 0, 1, "CREATING", []
        q_start_time = time.time()

    if curr_room_code in rooms and rooms[curr_room_code]["game_state"] != st.session_state.game_state:
        st.session_state.game_state = rooms[curr_room_code]["game_state"]

    if st.session_state.game_state == "CREATING":
        st.subheader("🧠 BC Tech Brain Battle")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚔️ Battle Zone बनाएं (Player 1)")
            p1_name_input = st.text_input("Player 1 का नाम दर्ज करें:", key="p1_input")
            if st.button("Generate Battle Code"):
                if p1_name_input.strip() != "":
                    code = f"BC-{random.randint(100, 999)}"
                    st.session_state.active_room_code = code
                    st.session_state.player_role = "P1"
                    
                    rooms[code] = {
                        "p1_name": p1_name_input,
                        "p2_name": "",
                        "category": "",
                        "current_level": 1,
                        "current_q_index": 0,
                        "p1_score": 0,
                        "p2_score": 0,
                        "turn": 1,
                        "game_state": "WAITING",
                        "questions": [],
                        "history_log": [],
                        "question_start_time": time.time()
                    }
                    save_room_store(rooms)
                    st.session_state.game_state = "WAITING"
                    st.query_params["room_code"] = code
                    st.query_params["role"] = "P1"
                    st.success(f"Battle Code जनरेट हो गया: {code}")
                    st.rerun()
                else:
                    st.warning("कृपया अपना नाम दर्ज करें!")

        with col2:
            st.markdown("### 🔗 Battle Zone में जुड़ें (Player 2)")
            p2_name_input = st.text_input("Player 2 का नाम दर्ज करें:", key="p2_input")
            room_code_input = st.text_input("Battle Code दर्ज करें (जैसे bc-123):", key="code_input")
            if st.button("Connect to Battle Zone"):
                if p2_name_input.strip() != "" and room_code_input.strip() != "":
                    clean_input_code = room_code_input.strip().upper()
                    matched_key = None
                    for k in rooms.keys():
                        if k.upper() == clean_input_code:
                            matched_key = k
                            break
                            
                    if matched_key:
                        rooms[matched_key]["p2_name"] = p2_name_input
                        rooms[matched_key]["game_state"] = "CATEGORY"
                        save_room_store(rooms)
                        
                        st.session_state.active_room_code = matched_key
                        st.session_state.player_role = "P2"
                        st.session_state.game_state = "CATEGORY"
                        st.query_params["room_code"] = matched_key
                        st.query_params["role"] = "P2"
                        st.success("सफलतापूर्वक Battle Zone से कनेक्ट हो गए!")
                        st.rerun()
                    else:
                        st.error("यह Battle Code मौजूद नहीं है! सही कोड डालें।")
                else:
                    st.warning("कृपया नाम और सही Battle Code दोनों भरें!")

        if st.button("⬅️ वापस चैट पर जाएं"):
            st.session_state.game_state = "IDLE"
            st.query_params.clear()
            st.query_params["chat_id"] = current_chat_id
            st.rerun()

    elif st.session_state.game_state == "WAITING":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        
        if curr_code in rooms and rooms[curr_code]["game_state"] != "WAITING":
            st.session_state.game_state = rooms[curr_code]["game_state"]
            st.rerun()

        st.subheader(f"⏳ Battle Code: `{curr_code}`")
        st.info(f"खिलाड़ी **{rooms.get(curr_code, {}).get('p1_name', 'P1')}** बैटल ज़ोन में तैयार हैं। दूसरे खिलाड़ी को यह कोड दें ताकि वह जुड़ सके।")
        
        st.markdown("---")
        st.markdown("### 🔗 यदि आप Player 2 हैं, तो यहाँ से Battle Zone जॉइन करें:")
        p2_wait_name = st.text_input("Player 2 अपना नाम दर्ज करें:", key="p2_wait_input")
        wait_code_input = st.text_input("यही Battle Code दोबारा दर्ज करें:", key="wait_code_input")
        if st.button("Join Battle Zone Now"):
            if p2_wait_name.strip() != "" and wait_code_input.strip() != "":
                clean_input_code = wait_code_input.strip().upper()
                matched_key = None
                for k in rooms.keys():
                    if k.upper() == clean_input_code:
                        matched_key = k
                        break
                        
                if matched_key:
                    rooms[matched_key]["p2_name"] = p2_wait_name
                    rooms[matched_key]["game_state"] = "CATEGORY"
                    save_room_store(rooms)
                    
                    st.session_state.active_room_code = matched_key
                    st.session_state.player_role = "P2"
                    st.session_state.game_state = "CATEGORY"
                    st.query_params["room_code"] = matched_key
                    st.query_params["role"] = "P2"
                    st.success("सफलतापूर्वक कनेक्ट हो गए!")
                    st.rerun()
                else:
                    st.error("गलत Battle Code!")
            else:
                st.warning("कृपया नाम और Battle Code दोनों भरें!")

        if st.button("🔄 चेक करें क्या दूसरा खिलाड़ी जुड़ गया है?"):
            st.rerun()

        if st.button("❌ गेम रद्द करें"):
            st.session_state.game_state = "IDLE"
            st.query_params.clear()
            st.query_params["chat_id"] = current_chat_id
            st.rerun()

    elif st.session_state.game_state == "CATEGORY":
        st.subheader("🎯 युद्ध का विषय (Category) चुनें")
        st.write(f"खिलाड़ी: **{p1_name}** vs **{p2_name}**")
        
        cat_choice = st.selectbox("कृपया क्विज के लिए विषय चुनें:", list(QUESTION_BANK.keys()))
        
        if st.button("🚀 Battle Start करें! (Launch Arena)"):
            rooms = load_room_store()
            curr_code = st.session_state.active_room_code
            
            pool_1_qs = QUESTION_BANK[cat_choice]["pool_1"].copy()
            random.shuffle(pool_1_qs)
            selected_qs = pool_1_qs[:5]
            
            rooms[curr_code]["category"] = cat_choice
            rooms[curr_code]["current_level"] = 1
            rooms[curr_code]["current_q_index"] = 0
            rooms[curr_code]["p1_score"] = 0
            rooms[curr_code]["p2_score"] = 0
            rooms[curr_code]["turn"] = 1
            rooms[curr_code]["questions"] = selected_qs
            rooms[curr_code]["history_log"] = []
            rooms[curr_code]["question_start_time"] = time.time()
            rooms[curr_code]["game_state"] = "PLAYING"
            save_room_store(rooms)
            
            st.session_state.game_state = "PLAYING"
            st.rerun()

    elif st.session_state.game_state == "PLAYING":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        if curr_code not in rooms:
            st.warning("बैटल ज़ोन समाप्त हो गया है।")
            st.session_state.game_state = "IDLE"
            st.rerun()

        r_data = rooms[curr_code]
        q_list = r_data.get("questions", [])
        q_idx = r_data.get("current_q_index", 0)
        curr_lvl = r_data.get("current_level", 1)
        turn = r_data.get("turn", 1)
        p1_name = r_data.get("p1_name", "P1")
        p2_name = r_data.get("p2_name", "P2")
        active_player = p1_name if turn == 1 else p2_name
        active_role = "P1" if turn == 1 else "P2"

        max_q_limit = 5 if curr_lvl == 1 else 10
        is_my_turn = (st.session_state.player_role == active_role)

        elapsed = time.time() - q_start_time
        remaining = max(0, int(30 - elapsed))

        if remaining == 0:
            r_data["history_log"].append({
                "level": curr_lvl,
                "player": active_player,
                "question": q_list[q_idx]['q'],
                "chosen": "समय समाप्त (Timeout)",
                "correct": q_list[q_idx]["answer"],
                "status": "Timeout (0 अंक)"
            })
            
            if turn == 1:
                r_data["turn"] = 2
            else:
                r_data["turn"] = 1
                r_data["current_q_index"] += 1
            
            if r_data["current_q_index"] >= max_q_limit:
                if curr_lvl < 3:
                    r_data["game_state"] = "LEVEL_TRANSITION"
                else:
                    r_data["game_state"] = "RESULT"

            r_data["question_start_time"] = time.time()
            save_room_store(rooms)
            st.rerun()

        if q_idx < len(q_list) and q_idx < max_q_limit:
            current_q_data = q_list[q_idx]

            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(f"🧠 BC Tech Brain Battle - लेवल {curr_lvl} | सवाल {q_idx + 1} / {max_q_limit}")
            with col_b:
                st.markdown(f"**बारी:** 👤 {active_player}")

            st.markdown("---")

            if not is_my_turn:
                st.info(f"🔵 **प्रतीक्षा करें (Waiting):** यह **{active_player}** की बारी है। कृपया प्रतीक्षा करें...")
                time.sleep(1)
                st.rerun()
                st.stop()
            
            st.success(f"🟢 **आपकी बारी (Your Turn)!** शेष समय: **{remaining} सेकंड**")
            st.progress(remaining / 30.0)

            st.markdown(f"### ❓ {current_q_data['q']}")
            options = current_q_data["options"]
            correct_ans = current_q_data["answer"]

            for opt in options:
                if st.button(f"👉 {opt}", key=f"opt_btn_{curr_lvl}_{q_idx}_{opt}"):
                    status_str = ""
                    if opt == correct_ans:
                        status_str = "सही (Right) (+1 अंक)"
                        if turn == 1:
                            r_data["p1_score"] += 1
                        else:
                            r_data["p2_score"] += 1
                    else:
                        status_str = "गलत (Wrong) (0 अंक)"
                    
                    r_data["history_log"].append({
                        "level": curr_lvl,
                        "player": active_player,
                        "question": current_q_data['q'],
                        "chosen": opt,
                        "correct": correct_ans,
                        "status": status_str
                    })
                    
                    if turn == 1:
                        r_data["turn"] = 2
                    else:
                        r_data["turn"] = 1
                        r_data["current_q_index"] += 1
                    
                    if r_data["current_q_index"] >= max_q_limit:
                        if curr_lvl < 3:
                            r_data["game_state"] = "LEVEL_TRANSITION"
                        else:
                            r_data["game_state"] = "RESULT"

                    r_data["question_start_time"] = time.time()
                    save_room_store(rooms)
                    st.session_state.game_state = r_data["game_state"]
                    st.rerun()

            st.markdown("---")
            if st.button("🔄 स्क्रीन सिंक करें (Refresh View)", key=f"sync_btn_{q_idx}_{turn}"):
                st.rerun()
        else:
            if curr_lvl < 3:
                r_data["game_state"] = "LEVEL_TRANSITION"
            else:
                r_data["game_state"] = "RESULT"
            save_room_store(rooms)
            st.session_state.game_state = r_data["game_state"]
            st.rerun()

    elif st.session_state.game_state == "LEVEL_TRANSITION":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        r_data = rooms.get(curr_code, {})
        finished_lvl = r_data.get("current_level", 1)
        next_lvl = finished_lvl + 1
        
        st.success(f"🎉 शानदार! **लेवल {finished_lvl}** सफलतापूर्वक पूरा हो गया है!")
        
        lvl_logs = [log for log in r_data.get("history_log", []) if log["level"] == finished_lvl]
        p1 = r_data.get("p1_name", "P1")
        p2 = r_data.get("p2_name", "P2")
        
        p1_lvl_score = sum(1 for log in lvl_logs if log['player'] == p1 and "सही" in log['status'])
        p2_lvl_score = sum(1 for log in lvl_logs if log['player'] == p2 and "सही" in log['status'])
        
        st.markdown(f"### 📊 लेवल {finished_lvl} परिणाम (Level {finished_lvl} Winner):")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric(label=f"👤 {p1}", value=f"{p1_lvl_score} सही जवाब")
        with col_s2:
            st.metric(label=f"👤 {p2}", value=f"{p2_lvl_score} सही जवाब")
            
        if p1_lvl_score > p2_lvl_score:
            st.success(f"🏆 **लेवल {finished_lvl} के विजेता:** {p1} 🎊")
        elif p2_lvl_score > p1_lvl_score:
            st.success(f"🏆 **लेवल {finished_lvl} के विजेता:** {p2} 🎊")
        else:
            st.info(f"🤝 **लेवल {finished_lvl} टाई (Tie) रहा!**")

        st.markdown("---")
        
        if st.button(f"लेवल {next_lvl} पर आगे बढ़ें 🚀"):
            cat = r_data.get("category", "Basic Computer & Internet")
            
            pool_key = f"pool_{next_lvl}"
            if pool_key in QUESTION_BANK[cat]:
                next_pool = QUESTION_BANK[cat][pool_key].copy()
                random.shuffle(next_pool)
                next_qs = next_pool[:10]
            else:
                next_qs = []

            r_data["current_level"] = next_lvl
            r_data["questions"] = next_qs
            r_data["current_q_index"] = 0
            r_data["question_start_time"] = time.time()
            r_data["game_state"] = "PLAYING"
            save_room_store(rooms)
            
            st.session_state.game_state = "PLAYING"
            st.rerun()

    elif st.session_state.game_state == "RESULT":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        r_data = rooms.get(curr_code, {})
        
        st.balloons()
        st.header("🏆 BC Tech Brain Battle - फाइनल स्कोरकार्ड & समीक्षा")
        
        p1 = r_data.get("p1_name", "P1")
        p2 = r_data.get("p2_name", "P2")
        s1 = r_data.get("p1_score", 0)
        s2 = r_data.get("p2_score", 0)
        
        col1, col2 = st.columns(2)
        col1.metric(label=f"👤 {p1}", value=f"{s1} कुल अंक")
        col2.metric(label=f"👤 {p2}", value=f"{s2} कुल अंक")
            
        st.markdown("---")
        if s1 > s2:
            st.success(f"🎊 महा-विजेता (Overall Winner): **{p1}** ने शानदार प्रदर्शन करते हुए मुकाबला जीत लिया है! 🏆")
        elif s2 > s1:
            st.success(f"🎊 महा-विजेता (Overall Winner): **{p2}** ने शानदार प्रदर्शन करते हुए मुकाबला जीत लिया है! 🏆")
        else:
            st.info("🤝 कुल मुकाबला **टाई (Tie)** रहा! दोनों खिलाड़ियों ने अद्भुत खेल दिखाया।")
            
        with st.expander("📜 सभी लेवल्स के विस्तृत जवाब देखें (Full Game Review)", expanded=True):
            for idx, log in enumerate(r_data.get("history_log", []), 1):
                st.markdown(f"""
                **[लेवल {log['level']}] {idx}. {log['question']}**  
                - खिलाड़ी: *{log['player']}* | चुना गया उत्तर: `{log['chosen']}` ({log['status']})  
                - 🟢 **सही उत्तर: `{log['correct']}`**  
                ---
                """)

        if st.button("🔄 दोबारा खेलें (Play Again)"):
            st.session_state.game_state = "IDLE"
            st.session_state.active_room_code = None
            st.query_params.clear()
            st.query_params["chat_id"] = current_chat_id
            st.rerun()
