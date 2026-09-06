import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import pandas as pd
import requests
import io
import re
import json
import urllib.parse
import random
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="BC Tech Ai Assistant", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# Custom Modern Chat Bubbles Styling (User on Right, AI on Left)
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    header {visibility: visible !important;}
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
    
    /* Streamlit Chat Message alignment modifications */
    /* User Message Container */
    [data-testid="stChatMessage"]:has(div.st-emotion-cache-1c7y2kd) {
        flex-direction: row-reverse;
        text-align: right;
    }
    
    /* General message bubble layout adjustments */
    [data-testid="stChatMessage"] {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 10px;
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

# Persistence Script
def render_persistence_script():
    persistence_js = """
    <script>
        const STORAGE_KEY_MSGS = "bctech_chat_messages_v7";
        const STORAGE_KEY_RECENT = "bctech_recent_chats_v7";

        window.addEventListener('DOMContentLoaded', () => {
            try {
                const savedMsgs = localStorage.getItem(STORAGE_KEY_MSGS);
                const savedRecent = localStorage.getItem(STORAGE_KEY_RECENT);
                if (savedMsgs && (!window.parent.sessionRestored)) {
                    window.parent.sessionRestored = true;
                }
            } catch(e) {}
        });
    </script>
    """
    components.html(persistence_js, height=0)

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

# Direct Image Download Button Component
def render_direct_download_button(img_url, unique_id):
    json_url = json.dumps(img_url)
    download_html = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .dl-btn {{
            border-radius: 16px;
            padding: 5px 16px;
            font-size: 12px;
            border: 1px solid #dadce0;
            background-color: #f8f9fa;
            color: #3c4043;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        .dl-btn:hover {{
            background-color: #e8eaed;
            color: #202124;
            border-color: #bdc1c6;
        }}
    </style>
    </head>
    <body>
        <button class="dl-btn" id="dl_{unique_id}" onclick="downloadImage()">
            📥 Download Image
        </button>
        <script>
            async function downloadImage() {{
                const btn = document.getElementById('dl_{unique_id}');
                btn.innerHTML = '⏳ Downloading...';
                try {{
                    const response = await fetch({json_url});
                    const blob = await response.blob();
                    const blobUrl = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = blobUrl;
                    a.download = 'bctech_portrait_' + Date.now() + '.jpg';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(blobUrl);
                    document.body.removeChild(a);
                    btn.innerHTML = '✓ Downloaded!';
                    setTimeout(() => {{ btn.innerHTML = '📥 Download Image'; }}, 2500);
                }} catch (e) {{
                    window.open({json_url}, '_blank');
                    btn.innerHTML = '📥 Download Image';
                }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(download_html, height=40)

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

# Session States initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = []
if "waiting_for_result_name" not in st.session_state:
    st.session_state.waiting_for_result_name = False
if "current_language" not in st.session_state:
    st.session_state.current_language = "ENGLISH"

render_persistence_script()

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
    st.session_state.waiting_for_result_name = False
    st.session_state.current_language = "ENGLISH"

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
                    
                    for _, row in clean_df.iterrows():
                        student_name = str(row[first_col]).strip()
                        name_words = sorted(student_name.lower().split())
                        name_signature = " ".join(name_words)
                        exam_val = str(row[second_col]).strip() if pd.notna(row[second_col]) else "Course"
                        
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

def detect_image_request(text):
    text_lower = text.lower().strip()
    triggers = [
        "image", "photo", "picture", "wallpaper", "banao", "create", 
        "generate", "tasveer", "chhavi", "તસવીર", "ફોટો", "draw", "kare",
        "badlo", "change", "edit", "karo", "kro", "redesign", "modify"
    ]
    
    is_img_query = any(t in text_lower for t in triggers)
    if not is_img_query:
        return False, ""
    
    remove_words = [
        "mere liye", "ek", "please", "can you", "kro", "karo", "banao", "chahiye",
        "image", "photo", "picture", "create", "generate", "make", "of", "ki", "ka", 
        "ke liye", "dikhao", "draw", "kare", "yesi", "aisi", "wala", "wali",
        "badlo", "change", "edit", "modify", "isame", "is me", "bana do"
    ]
    pattern = r"\b(" + "|".join(remove_words) + r")\b"
    cleaned = re.sub(pattern, "", text_lower).strip()
    base_prompt = re.sub(r"\s+", " ", cleaned)
    
    if len(base_prompt) < 3:
        base_prompt = "full length portrait photography of a beautiful simple person standing naturally"

    hd_boosted_prompt = (
        f"{base_prompt}, full length vertical portrait, shot on 35mm lens, DSLR camera capture, "
        "natural lighting, sharp focus from head to toe, realistic skin texture, beautiful background, magazine quality"
    )
    return True, hd_boosted_prompt

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
        "namaste", "mera", "meri", "kaise", "chahiye", "kya hai", "kaha hai", "kab aaya tha", "time", "samay", "aaj", "date"
    ]
    if any(re.search(r"\b" + re.escape(w) + r"\b", text_clean) for w in hindi_triggers):
        st.session_state.current_language = "HINDI"
        return "HINDI"
        
    english_triggers = ["english", "in english", "speak english", "time", "date"]
    if any(re.search(r"\b" + re.escape(w) + r"\b", text_clean) for w in english_triggers):
        st.session_state.current_language = "ENGLISH"
        return "ENGLISH"

    return st.session_state.current_language

def is_greeting(text):
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    greetings = ["hi", "hello", "hey", "hii", "hiii", "namaste", "kem cho", "kem chho", "halo", "હેલો", "નમસ્તે"]
    return text_clean in greetings

def check_is_branch_intent(text):
    text = text.lower()
    branch_keywords = [
        "branch", "address", "location", "kaha par hai", "kaha hai", "kidhar hai", 
        "kahan hai", "bctech kaha", "bc tech kaha", "ક્યાં છે", "ક્યાં આવેલું", "સરનામું", "લોકેશન", "શાખા", "पता", "कहाँ है", "लोकेशन"
    ]
    return any(kw in text for kw in branch_keywords)

def search_student_all_sheets(query_text, df):
    if df is None or df.empty or "Name_Signature_Std" not in df.columns:
        return []
    clean_q = query_text.strip().lower()
    fillers = [
        "result", "marks", "marx", "kya", "hai", "check", "batao", "mera", "meri", "ka", "ki", 
        "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam", "name",
        "show", "chhe", "che", "maru", "maro", "nu", "no", "na", "joiyu", "jovu", "aapo",
        "મારું", "મારુ", "નામ", "આપો", "છે", "જોવું", "રીઝલ્ટ", "રિઝલ્ટ", "પરિણામ"
    ]
    words = [w for w in clean_q.split() if w not in fillers and len(w) >= 2]
    if not words:
        return []
        
    user_search_signature = " ".join(sorted(list(set(words))))
    name_signatures = df["Name_Signature_Std"].astype(str)
    matched = df[name_signatures == user_search_signature]
    
    if matched.empty:
        search_term_original = " ".join(words)
        matched = df[df["Student_Name_Std"].astype(str).str.lower().str.strip() == search_term_original]

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
- Popular Courses: Basic Computer Course, Graphic Designing (CorelDraw, Photoshop, Illustrator), Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
"""

# Render chat history with explicit user/assistant styling
for idx, msg in enumerate(st.session_state.messages):
    is_user = (msg["role"] == "user")
    with st.chat_message(msg["role"], avatar="👤" if is_user else "🤖"):
        if msg.get("is_image", False):
            st.image(msg["content"], caption=msg.get("caption", "DSLR Vertical Output"), use_container_width=True)
            render_direct_download_button(msg["content"], f"hist_dl_{idx}")
        else:
            st.write(msg["content"])
            if not is_user:
                render_clean_copy_button(msg["content"], f"hist_{idx}")

query = st.chat_input("")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    
    with st.chat_message("user", avatar="👤"):
        st.write(query)

    is_img_req, enhanced_prompt = detect_image_request(query)
    
    if is_img_req:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🎨 Rendering DSLR Vertical Full-Body Image..."):
                encoded_prompt = urllib.parse.quote(enhanced_prompt)
                seed = random.randint(1000, 999999)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux&seed={seed}&nologo=true"
                st.image(image_url, caption="✨ DSLR Vertical Full-Body Output", use_container_width=True)
                render_direct_download_button(image_url, f"curr_dl_{len(st.session_state.messages)}")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": image_url,
                    "caption": "✨ DSLR Vertical Full-Body Output",
                    "is_image": True
                })
    else:
        df_sheet, err = load_all_sheets_data()
        lang = update_language_state(query)
        
        with st.chat_message("assistant", avatar="🤖"):
            if err:
                st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
            
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
                    reply = f"BC Tech Computer Education ની શાખા અને લોકેશનની સંપૂર્ણ વિગત માટે અહીં ક્લિક કરો:\n🔗 {BRANCH_LINK}"
                elif lang == "HINDI":
                    reply = f"BC Tech Computer Education की शाखा और पता की जानकारी के लिए यहाँ क्लिक करें:\n🔗 {BRANCH_LINK}"
                else:
                    reply = f"You can check the branch location and address details of BC Tech Computer Education here:\n🔗 {BRANCH_LINK}"
                
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                render_clean_copy_button(reply, f"branch_{len(st.session_state.messages)}")

            else:
                matched_records = search_student_all_sheets(query, df_sheet)
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                is_found_result = False
                
                if matched_records:
                    is_found_result = True
                    st.session_state.waiting_for_result_name = False
                    
                    details_text = ""
                    found_name = matched_records[0].get("Student_Name_Std", "")

                    for i, record in enumerate(matched_records, 1):
                        sheet_tab = record.get("_Sheet_Tab", f"Sheet {i}")
                        s_exam = record.get("Exam_Std", "")
                        details_text += f"\n--- Record {i} (Exam: {s_exam} | Sheet: {sheet_tab}) ---\n"
                        for k, v in record.items():
                            if k not in ["Name_Signature_Std", "Exam_Std", "_Sheet_Tab", "Student_Name_Std"]:
                                details_text += f"- {k}: {v}\n"

                    lang_name = "Gujarati" if lang == "GUJARATI" else ("Hindi" if lang == "HINDI" else "English")

                    system_prompt = f"""
                    You are the AI Assistant for BC Tech Computer Education.
                    Student verified records:
                    {details_text}

                    CRITICAL RULES:
                    - Target Language: {lang_name}. Output strictly in {lang_name}.
                    - Display all {len(matched_records)} records separately.
                    - Show clean whole numbers without decimals (e.g., 23, 41).
                    - DO NOT write 'Result: Pass' or any status.
                    - Format:
                      📌 Record [Number]: [Exam Name]
                      - Name: {found_name}
                      - Exam: [Exam Name]
                      - Marks: [Marks list]
                    """
                else:
                    ist_tz = timezone(timedelta(hours=5, minutes=30))
                    current_time_str = datetime.now(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p (%A)")
                    
                    lang_name = "Gujarati" if lang == "GUJARATI" else ("Hindi" if lang == "HINDI" else "English")
                    system_prompt = f"""
                    You are BC Tech AI Assistant, a smart, professional assistant for BC Tech Computer Education and general queries.
                    
                    EXACT CURRENT INDIAN STANDARD TIME (IST):
                    - Current Date and Time: {current_time_str}
                    
                    CRITICAL LANGUAGE RULE:
                    - Reply strictly in {lang_name}.
                    - If Gujarati, reply in clean Gujarati script.
                    - If Hindi, reply in clean Hindi script.
                    
                    CRITICAL INSTRUCTIONS:
                    1. When the user asks for time, date, day, or general queries, answer accurately using the real-time context provided above ({current_time_str}).
                    2. Answer general knowledge questions accurately in 2-3 direct sentences.
                    3. For BC Tech courses, refer to:
                    {KNOWLEDGE_BASE}
                    4. If asked about location, provide: {BRANCH_LINK}
                    5. Output ONLY the response text without greetings or meta notes.
                    """

                with st.spinner("Thinking..."):
                    try:
                        models_resp = client.models.list()
                        active_ids = [
                            m.id for m in models_resp.data 
                            if "whisper" not in m.id and "guard" not in m.id and "vision" not in m.id
                        ]
                        preferred = ["llama-3.1-8b-instant", "llama3-8b-8192", "gemma2-9b-it"]
                        models_to_try = [m for m in preferred if m in active_ids] + [m for m in active_ids if m not in preferred]

                        answer = None
                        last_api_err = None

                        for m_name in models_to_try:
                            try:
                                chat_completion = client.chat.completions.create(
                                    messages=[
                                        {"role": "system", "content": system_prompt},
                                        {"role": "user", "content": query}
                                    ],
                                    model=m_name,
                                    temperature=0.2,
                                    max_tokens=450
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
                            if is_found_result:
                                run_aerial_celebration()

                            render_clean_copy_button(answer, f"ast_curr_{len(st.session_state.messages)}")
                        else:
                            st.error(f"API Error: {last_api_err}")
                    except Exception as e:
                        st.error(f"Error: {e}")
