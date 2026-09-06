import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import pandas as pd
import requests
import io
import re
import urllib.parse
import random

st.set_page_config(
    page_title="BC Tech Ai Assistant", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# Custom Clean Styling
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    header {visibility: visible !important;}
    .block-container {padding-top: 1.5rem; max-width: 720px;}
    
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
    
    .stButton>button {
        border-radius: 16px;
        padding: 2px 12px;
        font-size: 12px;
        border: 1px solid #dadce0;
        background-color: #f8f9fa;
        color: #3c4043;
        float: right;
        margin-top: 4px;
    }
    .stButton>button:hover {
        background-color: #e8eaed;
        border-color: #dadce0;
        color: #202124;
    }
    
    /* Recent Button Styling */
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

# Session States
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_recent_chat" not in st.session_state:
    st.session_state.last_recent_chat = None
if "waiting_for_result_name" not in st.session_state:
    st.session_state.waiting_for_result_name = False
if "waiting_for_image_prompt" not in st.session_state:
    st.session_state.waiting_for_image_prompt = False

def on_new_chat_clicked():
    if st.session_state.messages:
        user_queries = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        title_text = user_queries[-1] if user_queries else "Last Chat"
        short_title = (title_text[:22] + "..") if len(title_text) > 22 else title_text
        
        st.session_state.last_recent_chat = {
            "title": short_title,
            "messages": list(st.session_state.messages)
        }
    st.session_state.messages = []
    st.session_state.waiting_for_result_name = False
    st.session_state.waiting_for_image_prompt = False

def restore_last_chat():
    if st.session_state.last_recent_chat:
        st.session_state.messages = list(st.session_state.last_recent_chat["messages"])

# Helper function to remove .0 from numbers
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
    
    with st.expander("🕒 Recent", expanded=True):
        if st.session_state.last_recent_chat:
            st.button(
                f"💬 {st.session_state.last_recent_chat['title']}", 
                key="btn_restore_last_search",
                on_click=restore_last_chat
            )
        else:
            st.caption("No recent search yet.")
            
    st.markdown("---")
    st.markdown("**📌 Quick Links:**")
    st.markdown("🌐 [Official Website](https://sites.google.com/view/bctechcomputer)")
    st.markdown("📍 [Branch Location](https://sites.google.com/view/bctechcomputer/about-us)")

st.title("🎓 BC Tech Ai Assistant")

SHEET_ID = "1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# Unified Sheet Loader (Cleans .0 decimals)
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
        "generate", "tasveer", "chhavi", "તસવીર", "ફોટો", "draw"
    ]
    
    if st.session_state.waiting_for_image_prompt:
        st.session_state.waiting_for_image_prompt = False
        base_prompt = text_lower
    else:
        is_img_query = any(t in text_lower for t in triggers)
        if not is_img_query:
            return False, ""
        
        remove_words = [
            "mere liye", "ek", "please", "can you", "kro", "karo", "banao", "chahiye",
            "image", "photo", "picture", "create", "generate", "make", "of", "ki", "ka", 
            "ke liye", "dikhao", "draw"
        ]
        pattern = r"\b(" + "|".join(remove_words) + r")\b"
        cleaned = re.sub(pattern, "", text_lower).strip()
        base_prompt = re.sub(r"\s+", " ", cleaned)
        if len(base_prompt) < 2:
            base_prompt = "breathtaking cinematic mountain landscape sunrise"

    hd_boosted_prompt = (
        f"{base_prompt}, ultra photorealistic, 8k resolution, 4k uhd, masterpiece, "
        "hyperrealistic photography, natural volumetric lighting, 35mm photograph, shot on DSLR, "
        "extremely detailed textures, cinematic octane render"
    )
    return True, hd_boosted_prompt

# Advanced Multilingual Detection
def get_target_language(text):
    text = text.strip()
    
    # 1. Check Devanagari (Hindi) or Gujarati script directly
    if any('\u0900' <= ch <= '\u097F' for ch in text): return "HINDI"
    if any('\u0A80' <= ch <= '\u0AFF' for ch in text): return "GUJARATI"
    
    text_lower = text.lower()
    
    # 2. Check Gujarati Hinglish keywords
    guj_hinglish_words = ["kem chho", "kem cho", "halo", "maru", "maro", "chhe", "che", "tamaru", "tame"]
    if any(w in text_lower for w in guj_hinglish_words):
        return "GUJARATI"
        
    # 3. Check Hindi Hinglish keywords or direct requests
    hindi_hinglish_words = ["namaste", "halo", "mera", "meri", "kya hai", "kaise", "batao", "chahiye", "bat kro", "हिंदी", "हिंदी में", "इन हिंदी"]
    if any(w in text_lower for w in hindi_hinglish_words):
        return "HINDI"
        
    return "ENGLISH"

def is_greeting(text):
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    greetings = ["hi", "hello", "hey", "hii", "hiii", "namaste", "kem cho", "kem chho", "halo", "હેલો", "નમસ્તે"]
    return text_clean in greetings

def check_is_result_intent(text):
    text = text.lower()
    keywords = [
        "result", "marks", "marx", "score", "grade", "pass", "fail", 
        "પરિણામ", "રિઝલ્ટ", "રીઝલ્ટ", "માર્ક્સ", "નંબર", "परिणाम", "नंबर", "मार्क्स", "रिजल्ट"
    ]
    return any(kw in text for kw in keywords)

def check_is_branch_intent(text):
    text = text.lower()
    branch_keywords = [
        "branch", "address", "location", "kaha par hai", "kaha hai", "kidhar hai", 
        "kahan hai", "bctech kaha", "bc tech kaha", "ક્યાં છે", "ક્યાં આવેલું", "સરનામું", "લોકેશન", "શાખા", "पता", "कहाँ है", "लोकेशन", "शाखा"
    ]
    return any(kw in text for kw in branch_keywords)

# Matches ONLY the specified name across all sheets with high flexibility (sorted word signatures)
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
    # Remove filler words to get only the name parts
    words = [w for w in clean_q.split() if w not in fillers and len(w) >= 2]
    if not words:
        return []
        
    # Create the search signature from user input (sorted unique words)
    user_search_signature = " ".join(sorted(list(set(words))))
    
    # Check exact match on the Name_Signature_Std column
    name_signatures = df["Name_Signature_Std"].astype(str)
    matched = df[name_signatures == user_search_signature]
    
    # Final check on original standardized name in case sorted signature misses nuances
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

# Counselor Knowledge Base
KNOWLEDGE_BASE = f"""
About Bctech Computer Education:
- Institute: Bctech Computer Education
- Official Branch & Location Info Link: {BRANCH_LINK}
- Main Offerings: Professional computer training, practical learning, ISO certified courses, job assistance.
- Popular Courses: Basic Computer Course, Graphic Designing (CorelDraw, Photoshop, Illustrator), Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
"""

# New All-knowledge system prompt
SYSTEM_PROMPT_ALL_KNOWLEDGE = f"""
You are an advanced, multilingual AI expert assistant. You are not physically located anywhere.
Your primary task is to help users by providing right, factual, and helpful answers to *ANY* question they ask.

KNOWLEDGE CAPABILITIES:
1.  **General Knowledge:** You can answer general knowledge questions about history (e.g., "google कब आया था"), science, geography, etc. Provide concise, right answers in the target language.
2.  **Multilingual:** You can communicate perfectly in Hindi (Devanagari or Hinglish), English, or Gujarati. Use the target language provided.
3.  **Bctech Computer Education:** If a user asks about computer courses, fees (never discuss or quote pricing), location, job assistance, or other specifics mentioned in the KNOWLEDGE BASE, answer using the following context concisely:
    {KNOWLEDGE_BASE}
4.  **Student Results (Sheet Data):** If the user is asking for student marks or results, you will be provided with specific verified data for *one* student. Use that data to create a clear, bulleted report based on specific rules.
    - If provided student data shows multiple records (e.g., across courses), display ALL of them clearly with separate headings. Never mix data.
    - Display numbers as clean whole numbers (e.g., '23', not '23.0').
    - If data is N/A or missing, show 'N/A'.
    - DO NOT add or mention Pass/Fail status.
    - In Gujarati/Hindi, use pure professional language for the report.
"""

# Render history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("is_image", False):
            st.image(msg["content"], caption=msg.get("caption", "Ultra HD Output"), use_container_width=True)
        else:
            st.write(msg["content"])
            col_l, col_r = st.columns([0.85, 0.15])
            with col_r:
                if st.button("📋 Copy", key=f"copy_hist_{idx}"):
                    st.code(msg["content"], language=None)
                    st.toast("Copied!", icon="📋")

query = st.chat_input("")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    
    with st.chat_message("user"):
        st.write(query)
        col_l, col_r = st.columns([0.85, 0.15])
        with col_r:
            if st.button("📋 Copy", key=f"copy_user_curr_{len(st.session_state.messages)}"):
                st.code(query, language=None)
                st.toast("Copied!", icon="📋")

    # Image request handling first
    is_img_req, enhanced_prompt = detect_image_request(query)
    
    if is_img_req:
        with st.chat_message("assistant"):
            with st.spinner("🎨 Rendering 4K Ultra-HD Realistic Image..."):
                encoded_prompt = urllib.parse.quote(enhanced_prompt)
                seed = random.randint(1000, 999999)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&model=flux&seed={seed}&nologo=true"
                st.image(image_url, caption="✨ 4K Ultra-HD Photorealistic Output", use_container_width=True)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": image_url,
                    "caption": "✨ 4K Ultra-HD Photorealistic Output",
                    "is_image": True
                })
    
    # Text-based handling for all knowledge
    else:
        df_sheet, err = load_all_sheets_data()
        lang = get_target_language(query)
        
        with st.chat_message("assistant"):
            if err:
                st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
            
            # Identify special intents first (Greetings, Branch)
            # 1. Greeting Handler
            elif is_greeting(query):
                if lang == "GUJARATI":
                    reply = "નમસ્તે! BC Tech માં આપનું સ્વાગત છે. હું તમને કેવી રીતે મદદ करी शकूं? 😊"
                elif lang == "HINDI":
                    reply = "नमस्ते! BC Tech Computer Education में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूँ? 😊"
                else:
                    reply = "Hello! Welcome to BC Tech Computer Education. How can I help you today? 😊"
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                col_l, col_r = st.columns([0.85, 0.15])
                with col_r:
                    if st.button("📋 Copy", key=f"copy_greet_{len(st.session_state.messages)}"):
                        st.code(reply, language=None)
                        st.toast("Copied!", icon="📋")

            # 2. Branch Intent
            elif check_is_branch_intent(query):
                if lang == "GUJARATI":
                    reply = f"BC Tech Computer Education ની શાખા અને લોકેશનની સંપૂર્ણ વિગત માટે અહીં ક્લિક કરો:\n🔗 {BRANCH_LINK}"
                elif lang == "HINDI":
                    reply = f"BC Tech Computer Education की शाखा और पता की जानकारी के लिए यहाँ क्लिक करें:\n🔗 {BRANCH_LINK}"
                else:
                    reply = f"You can check the branch location and address details of BC Tech Computer Education here:\n🔗 {BRANCH_LINK}"
                
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                col_l, col_r = st.columns([0.85, 0.15])
                with col_r:
                    if st.button("📋 Copy", key=f"copy_branch_{len(st.session_state.messages)}"):
                        st.code(reply, language=None)
                        st.toast("Copied!", icon="📋")

            # 3. Handle Sheet Data or General/Computer Knowledge
            else:
                matched_records = search_student_all_sheets(query, df_sheet)
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                is_found_result = False
                
                final_system_prompt = SYSTEM_PROMPT_ALL_KNOWLEDGE
                final_user_content = query

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

                    # Format dynamic multilingual prompt for result data
                    lang_instr = "Apply language format: English."
                    if lang == "GUJARATI": lang_instr = "Apply language format: Gujarati professional."
                    if lang == "HINDI": lang_instr = "Apply language format: Hindi professional."

                    final_user_content = f"""
                        Verified data for student {found_name}:
                        {details_text}

                        Use this data to create a detailed student report.
                        {lang_instr}
                    """
                
                # Check for other knowledge areas (all knowledge handling)
                else:
                    lang_instr = "Respond concisely in English."
                    if lang == "GUJARATI": lang_instr = "Respond concisely in professional Gujarati."
                    if lang == "HINDI": lang_instr = "Respond concisely in professional Hindi."
                    final_user_content = f"{query} | {lang_instr}"

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
                                        {"role": "system", "content": final_system_prompt},
                                        {"role": "user", "content": final_user_content}
                                    ],
                                    model=m_name,
                                    temperature=0.3,
                                    max_tokens=600
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

                            col_l, col_r = st.columns([0.85, 0.15])
                            with col_r:
                                if st.button("📋 Copy", key=f"copy_ast_curr_{len(st.session_state.messages)}"):
                                    st.code(answer, language=None)
                                    st.toast("Copied!", icon="📋")
                        else:
                            st.error(f"API Error: {last_api_err}")
                    except Exception as e:
                        st.error(f"Error: {e}")
