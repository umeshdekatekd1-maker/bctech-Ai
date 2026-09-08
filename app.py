import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import pandas as pd
import requests
import io
import re
import json
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="BC Tech Ai Assistant", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# Custom Modern Chat Bubbles Styles
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden !important;}
    header {visibility: visible !important;}
    
    footer {display: none !important;}
    .stApp > header {background-color: transparent;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    .viewerBadge_container__1QSob {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    
    .block-container {padding-top: 1.5rem; max-width: 780px;}
    
    div[data-baseweb="input"] {
        border-radius: 28px !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.18) !important;
        border: 1px solid #dfe1e5 !important;
        padding-left: 10px;
    }
    div[data-baseweb="input"]:focus-within {
        box-shadow: 0 2px 8px rgba(32,33,36,0.3) !important;
        border-color: #4285F4 !important;
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

# Session States initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = []
if "current_language" not in st.session_state:
    st.session_state.current_language = "ENGLISH"
if "last_mentioned_name" not in st.session_state:
    st.session_state.last_mentioned_name = None

# Clean One-Click Clipboard Button
def render_clean_copy_button(text_to_copy, unique_id):
    json_text = json.dumps(text_to_copy)
    html_btn = f"""
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .copy-btn {{
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
        .copy-btn:hover {{
            background-color: #e8eaed;
            color: #202124;
        }}
    </style>
    </head>
    <body>
        <button class="copy-btn" id="btn_{unique_id}" onclick="doCopy()">
            📋 Copy
        </button>
        <script>
            function doCopy() {{
                const text = {json_text};
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
                const b = document.getElementById('btn_{unique_id}');
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
    components.html(html_btn, height=30)

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
    st.session_state.current_language = "ENGLISH"
    st.session_state.last_mentioned_name = None

def restore_chat(idx):
    if idx < len(st.session_state.recent_chats):
        st.session_state.messages = list(st.session_state.recent_chats[idx]["messages"])

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

# Sidebar
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
    st.markdown("**📌 Quick Links:**")
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
    
    guj_triggers = [
        "gujarati", "gujrati", "gujaratin", "in gujarati", "gujarati ma", "gujarati mein",
        "kem cho", "kem chho", "halo", "maru", "maro", "chhe", "che", "tamaru", "tame"
    ]
    if any(re.search(r"\b" + re.escape(w) + r"\b", text_clean) for w in guj_triggers):
        st.session_state.current_language = "GUJARATI"
        return "GUJARATI"
        
    hindi_triggers = [
        "hindi", "in hindi", "hindi me", "hindi main", "bat kro", "baat karo", "batao",
        "namaste", "mera", "meri", "kaise", "chahiye", "kya hai", "kaha hai", "kab aaya tha", "time", "samay", "aaj", "date", "kisne", "bnaya", "banaya", "or batao", "konsa", "course", "sakti"
    ]
    if any(re.search(r"\b" + re.escape(w) + r"\b", text_clean) for w in hindi_triggers):
        st.session_state.current_language = "HINDI"
        return "HINDI"
        
    english_triggers = ["english", "in english", "speak english", "time", "date"]
    if any(re.search(r"\b" + re.escape(w) + r"\b", text_clean) for w in english_triggers):
        st.session_state.current_language = "ENGLISH"

    return st.session_state.current_language

def is_greeting(text):
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    greetings = ["hi", "hello", "hey", "hii", "hiii", "namaste", "kem cho", "kem chho", "halo", "હેલો", "નમસ્ते"]
    return text_clean in greetings

def check_is_name_intro(text):
    t = text.lower().strip()
    return "mera naam" in t or "my name is" in t or "hu mara naam" in t or "maru naam" in t or t.startswith("naam ")

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

def search_student_all_sheets(query_text, df):
    if df is None or df.empty or "Student_Name_Std" not in df.columns:
        return []
    
    clean_q = query_text.strip().lower()
    
    ignore_phrases = ["or batao", "aur batao", "kya haal hai", "or kya", "aur kya", "batao", "kya chal raha hai", "konsa course", "course kar sakti"]
    if any(p in clean_q for p in ignore_phrases) and len(clean_q.split()) <= 4:
        return []

    if "priya mam" in clean_q or "umesh sir" in clean_q or "sanjay sir" in clean_q or "ajay sir" in clean_q:
        return []

    img_triggers = ["image", "photo", "picture", "wallpaper", "banao", "create", "generate", "tasveer", "draw", "bana do"]
    if any(t in clean_q for t in img_triggers):
        return []

    fillers = [
        "result", "marks", "marx", "kya", "hai", "check", "batao", "bata do", "mera", "meri", "ka", "ki", "ko",
        "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam", "name",
        "show", "chhe", "che", "maru", "maro", "nu", "no", "na", "joiyu", "jovu", "aapo", "mam", "sir", "karo", "kar do",
        "મારું", "મારુ", "નામ", "આપો", "છે", "જોવું", "રીઝલ્ટ", "રિઝલ્ટ", "પરિણામ"
    ]
    
    query_clean_words = [w for w in clean_q.split() if w not in fillers]
    search_query_str = " ".join(query_clean_words).strip()
    
    if not search_query_str:
        return []

    matched = df[df["Student_Name_Std"].astype(str).str.lower().str.contains(search_query_str, na=False)]

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
    
    words = cleaned.split()
    if len(words) > 10:
        for i in range(1, len(words) // 2):
            phrase = " ".join(words[:i])
            if phrase and cleaned.count(phrase) > 3:
                cleaned = phrase + "."
                break
    return cleaned.strip()

BRANCH_LINK = "https://sites.google.com/view/bctechcomputer/about-us"

KNOWLEDGE_BASE = f"""
About Bctech Computer Education:
- Institute: Bctech Computer Education
- Official Branch & Location Info Link: {BRANCH_LINK}
- Main Offerings: Professional computer training, practical learning, ISO certified courses, job assistance.
- Popular Courses: Basic Computer Course, Graphic Designing (CorelDraw, Photoshop, Illustrator), Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
- Location/Address: Surat, Gujarat, India.
"""

# Render chat history
for idx, msg in enumerate(st.session_state.messages):
    is_user = (msg["role"] == "user")
    with st.chat_message(msg["role"], avatar="👤" if is_user else "🤖"):
        st.write(msg["content"])
        if not is_user:
            render_clean_copy_button(msg["content"], f"hist_{idx}")

query = st.chat_input("")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    
    with st.chat_message("user", avatar="👤"):
        st.write(query)

    df_sheet, err = load_all_sheets_data()
    lang = update_language_state(query)
    
    with st.chat_message("assistant", avatar="🤖"):
        if err:
            st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
        
        elif check_is_name_intro(query):
            name_match = re.search(r"(?:mera naam|my name is|maru naam)\s+([a-zA-Z\u0900-\u097F]+)", query, re.IGNORECASE)
            if not name_match:
                words = [w for w in query.split() if w.lower() not in ["mera", "naam", "hai", "is", "my", "name"]]
                username = words[0].capitalize() if words else "User"
            else:
                username = name_match.group(1).capitalize()
            
            st.session_state.last_mentioned_name = username.lower()

            if lang == "GUJARATI":
                reply = f"નમસ્તે {username}! BC Tech માં આપનું સ્વાગત છે. જણાવો, હું આપને કેવી રીતે મદદ કરી શકું? 😊"
            else:
                reply = f"नमस्ते {username}! BC Tech Computer Education में आपका स्वागत है। बताइए, मैं आपकी कैसे मदद कर सकता हूँ? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"name_reply_{len(st.session_state.messages)}")

        elif query.strip().lower() in ["gujarati", "gujrati", "gujarati ma", "gujarati mein baat karte hai", "gujarati main baat karte hai ok", "gujarati ma vaat kariye"]:
            reply = "ચોક્કસ! હવે આપણે ગુજરાતીમાં વાત કરીશું. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"ack_{len(st.session_state.messages)}")

        elif query.strip().lower() in ["hindi", "in hindi", "hindi me", "hindi main baat karo", "hindi me baat karte hai"]:
            reply = "ज़रूर! अब हम हिंदी में बात करेंगे। मैं आपकी क्या सहायता कर सकता हूँ? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"ack_{len(st.session_state.messages)}")

        elif is_greeting(query):
            if lang == "GUJARATI":
                reply = "નમસ્તે! BC Tech માં આપનું સ્વાગત છે. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
            elif lang == "HINDI":
                reply = "नमस्ते! BC Tech Computer Education में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूँ? 😊"
            else:
                reply = "Hello! Welcome to BC Tech Computer Education. How can I help you today? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"greet_{len(st.session_state.messages)}")

        elif check_is_branch_intent(query):
            if lang == "GUJARATI":
                reply = f"BC Tech Computer Education સુરત, ગુજરાત, ભારતમાં આવેલું છે. વધુ વિગતો અને અન્ય શાખાના પત્તા માટે અધિકૃત વેબસાઇટની મુલાકાત લો:\n🔗 {BRANCH_LINK}"
            elif lang == "HINDI":
                reply = f"BC Tech Computer Education सूरत, गुजरात, भारत में स्थित है। अधिक विवरण और अन्य शाखाओं के पते के लिए आप आधिकारिक वेबसाइट पर जा सकते हैं:\n🔗 {BRANCH_LINK}"
            else:
                reply = f"BC Tech Computer Education is located in Surat, Gujarat, India. For more details and branch addresses, you can visit the official website:\n🔗 {BRANCH_LINK}"
            
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"branch_{len(st.session_state.messages)}")

        elif check_is_creator_intent(query):
            if lang == "GUJARATI":
                reply = "મને BC Tech Computer Education ના એડમિન અને ડેવલપર દ્વારા બનાવવામાં આવ્યો છે."
            elif lang == "HINDI":
                reply = "मुझे BC Tech Computer Education के डेवलपर और एडमिन द्वारा बनाया गया है।"
            else:
                reply = "I was created by the developer and admin of BC Tech Computer Education."
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"creator_{len(st.session_state.messages)}")

        elif len(query.strip()) <= 3 and query.strip().lower() in ["ok", "h", "k", "hi", "ok.", "okay", "ha", "haan"]:
            reply = "हाँ, बताइए! मैं आपकी क्या मदद कर सकता हूँ? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            render_clean_copy_button(reply, f"ack_{len(st.session_state.messages)}")

        else:
            matched_records = search_student_all_sheets(query, df_sheet)
            
            if matched_records:
                full_reply = ""
                for record in matched_records:
                    f_name = record.get("Student_Name_Std", "")
                    f_exam = record.get("Exam_Std", "Course")
                    f_teacher = record.get("_Sheet_Tab", "Teacher")
                    
                    valid_tests_count = 0
                    t_marks = []
                    p_marks = []
                    
                    for k, v in record.items():
                        if "theory" in k.lower():
                            val_str = str(v).strip()
                            if val_str and val_str.lower() != "n/a" and val_str.lower() != "nan":
                                try:
                                    m_val = float(val_str)
                                    t_marks.append(m_val)
                                    valid_tests_count += 1
                                except ValueError:
                                    pass
                        elif "practical" in k.lower():
                            val_str = str(v).strip()
                            if val_str and val_str.lower() != "n/a" and val_str.lower() != "nan":
                                try:
                                    m_val = float(val_str)
                                    p_marks.append(m_val)
                                    valid_tests_count += 1
                                except ValueError:
                                    pass
                    
                    tot_theory = int(sum(t_marks))
                    tot_prac = int(sum(p_marks))
                    total_obtained = tot_theory + tot_prac
                    
                    # Dynamically count only the attempted/present exams (each exam is 50 marks)
                    max_total = valid_tests_count * 50 if valid_tests_count > 0 else 50
                    percentage = round((total_obtained / max_total) * 100, 2) if max_total > 0 else 0

                    full_reply += f"""Student Name: {f_name}
Exam Name: {f_exam}
Teacher Name: {f_teacher}

Theory Tests
- Test 1: {record.get('Theory-1', 'N/A')}
- Test 2: {record.get('Theory-2', 'N/A')}
- Test 3: {record.get('Theory-3', 'N/A')}
- Total Theory: {tot_theory}

Practical Tests
- Test 1: {record.get('practical-1', 'N/A')}
- Test 2: {record.get('practical-2', 'N/A')}
- Test 3: {record.get('practical-3', 'N/A')}
- Total Practical: {tot_prac}

Total Marks: {total_obtained} / {max_total}
Percentage: {percentage}%

"""
                st.write(full_reply.strip())
                st.session_state.messages.append({"role": "assistant", "content": full_reply.strip()})
                run_aerial_celebration()
                render_clean_copy_button(full_reply.strip(), f"ast_curr_{len(st.session_state.messages)}")
            else:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                current_time_str = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %I:%M:%S %p (%A)")
                lang_name = "Gujarati" if lang == "GUJARATI" else ("Hindi" if lang == "HINDI" else "English")
                
                system_prop = f"""
                You are BC Tech AI Assistant, a smart, professional assistant for BC Tech Computer Education.
                
                EXACT CURRENT INDIAN STANDARD TIME (IST):
                - Current Date and Time: {current_time_str}
                
                CRITICAL INSTRUCTIONS:
                1. BC Tech Computer Education is strictly located in Surat, Gujarat, India.
                2. Reply strictly and naturally in {lang_name} without repeating words.
                3. Course offerings & details: {KNOWLEDGE_BASE}
                4. Location link: {BRANCH_LINK}
                5. Keep answers direct, helpful, and concise.
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
                                    temperature=0.3,
                                    max_tokens=400
                                )
                                raw_answer = chat_completion.choices[0].message.content
                                answer = clean_ai_response(raw_answer)
                                if answer:
                                    break
                            except Exception as ex:
                                last_api_err = str(ex)
                                continue
                        
                        if answer:
                            st.write(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                            render_clean_copy_button(answer, f"ast_curr_{len(st.session_state.messages)}")
                        else:
                            st.error(f"API Error: {last_api_err}")
                    except Exception as e:
                        st.error(f"Error: {e}")

# Save state to browser's localStorage automatically
msgs_json = json.dumps(st.session_state.messages)
recent_json = json.dumps(st.session_state.recent_chats)

persistence_component = f"""
<html>
<body>
<script>
    const STORAGE_KEY_MSGS = "bctech_persisted_messages_v16";
    const STORAGE_KEY_RECENT = "bctech_persisted_recent_v16";
    try {{
        localStorage.setItem(STORAGE_KEY_MSGS, {json.dumps(msgs_json)});
        localStorage.setItem(STORAGE_KEY_RECENT, {json.dumps(recent_json)});
    }} catch(e) {{}}
</script>
</body>
</html>
"""
components.html(persistence_component, height=0)
