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
        
        # Save only the LAST chat (overwrites previous)
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

@st.cache_data(ttl=15)
def load_all_sheets_data():
    try:
        res = requests.get(EXCEL_URL, timeout=15)
        if res.status_code == 200 and len(res.content) > 100:
            excel_file = io.BytesIO(res.content)
            all_dfs = pd.read_excel(excel_file, sheet_name=None)
            combined_rows = []
            
            for sheet_name, df in all_dfs.items():
                if df is not None and not df.empty:
                    df.columns = [str(c).strip() for c in df.columns]
                    first_col = df.columns[0]
                    clean_df = df[df[first_col].notna()].copy()
                    clean_df = clean_df[~clean_df[first_col].astype(str).str.lower().str.contains("batch time", na=False)]
                    clean_df = clean_df[clean_df[first_col].astype(str).str.strip() != ""]
                    
                    for record in clean_df.to_dict(orient="records"):
                        record["_Sheet_Tab"] = sheet_name
                        combined_rows.append(record)
                        
            if combined_rows:
                return pd.DataFrame(combined_rows), None
    except Exception:
        pass

    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
    try:
        res = requests.get(csv_url, timeout=10)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.content.decode("utf-8")))
            df.columns = [str(c).strip() for c in df.columns]
            first_col = df.columns[0]
            df = df[df[first_col].notna()]
            df = df[~df[first_col].astype(str).str.lower().str.contains("batch time", na=False)]
            df = df[df[first_col].astype(str).str.strip() != ""]
            return df, None
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

def is_gujarati_input(text):
    if any('\u0A80' <= ch <= '\u0AFF' for ch in text):
        return True
    guj_words = ["maru", "maro", "chhe", "che", "kem", "tamaro", "tamare", "jovu"]
    words = text.lower().split()
    return any(w in words for w in guj_words)

def is_greeting(text):
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    greetings = ["hi", "hello", "hey", "hii", "hiii", "namaste", "kem cho", "kem chho", "halo", "હેલો", "નમસ્તે"]
    return text_clean in greetings

def check_is_result_intent(text):
    text = text.lower()
    keywords = [
        "result", "marks", "marx", "score", "grade", "pass", "fail", 
        "પરિણામ", "રિઝલ્ટ", "રીઝલ્ટ", "માર્ક્સ", "નંબર"
    ]
    return any(kw in text for kw in keywords)

def check_is_branch_intent(text):
    text = text.lower()
    branch_keywords = [
        "branch", "address", "location", "kaha par hai", "kaha hai", "kidhar hai", 
        "kahan hai", "bctech kaha", "bc tech kaha", "ક્યાં છે", "ક્યાં આવેલું", "સરનામું", "લોકેશન", "શાખા"
    ]
    return any(kw in text for kw in branch_keywords)

def search_student_all_sheets(query_text, df):
    if df is None or df.empty:
        return []
    clean_q = query_text.strip().lower()
    fillers = [
        "result", "marks", "kya", "hai", "check", "batao", "mera", "meri", "ka", "ki", 
        "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam", "name",
        "chhe", "che", "maru", "maro", "nu", "no", "na", "joiyu", "jovu", "aapo",
        "મારું", "મારુ", "નામ", "આપો", "છે", "જોવું", "રીઝલ્ટ", "રિઝલ્ટ", "પરિણામ"
    ]
    words = [w for w in clean_q.split() if w not in fillers and len(w) >= 2]
    if not words:
        words = [clean_q]
        
    search_term = " ".join(words)
    name_col = df.columns[0]
    name_series = df[name_col].astype(str).str.strip().str.lower()
    
    matched = df[name_series == search_term]
    if matched.empty:
        matched = df[name_series.str.contains(search_term, regex=False, na=False)]
    if matched.empty:
        for w in words:
            matched = df[name_series.str.contains(w, regex=False, na=False)]
            if not matched.empty:
                break
                
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

    df_sheet, err = load_all_sheets_data()
    user_wants_gujarati = is_gujarati_input(query)
    is_img_req, enhanced_prompt = detect_image_request(query)
    
    with st.chat_message("assistant"):
        if err:
            st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
        
        # 1. 4K Ultra-HD Realistic Image
        elif is_img_req:
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

        # 2. Greeting Handler
        elif is_greeting(query):
            if user_wants_gujarati:
                reply = "નમસ્તે! BC Tech માં આપનું સ્વાગત છે. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
            else:
                reply = "Hello! Welcome to BC Tech Computer Education. How can I help you today? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            col_l, col_r = st.columns([0.85, 0.15])
            with col_r:
                if st.button("📋 Copy", key=f"copy_greet_{len(st.session_state.messages)}"):
                    st.code(reply, language=None)
                    st.toast("Copied!", icon="📋")

        # 3. Branch Intent
        elif check_is_branch_intent(query):
            if user_wants_gujarati:
                reply = f"BC Tech Computer Education ની શાખા और लोकेशन की संपूर्ण जानकारी के लिए यहाँ क्लिक करें:\n🔗 {BRANCH_LINK}"
            else:
                reply = f"You can check the branch location and address details of BC Tech Computer Education here:\n🔗 {BRANCH_LINK}"
            
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            col_l, col_r = st.columns([0.85, 0.15])
            with col_r:
                if st.button("📋 Copy", key=f"copy_branch_{len(st.session_state.messages)}"):
                    st.code(reply, language=None)
                    st.toast("Copied!", icon="📋")

        # 4. Sheet Result or Normal Counseling
        else:
            matched_records = search_student_all_sheets(query, df_sheet)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            is_found_result = False
            
            if matched_records:
                is_found_result = True
                st.session_state.waiting_for_result_name = False
                
                details_text = ""
                # Agar ek se jyada sheets me record ho to sabhi ko include karein
                for i, record in enumerate(matched_records[:5], 1):
                    sheet_tab = record.get("_Sheet_Tab", f"Record {i}")
                    details_text += f"\n--- Record #{i} (From Sheet: {sheet_tab}) ---\n"
                    for k, v in record.items():
                        if k != "_Sheet_Tab" and pd.notna(v) and str(v).strip() != "" and "unnamed" not in str(k).lower():
                            details_text += f"- {k}: {v}\n"

                system_prompt = f"""
                You are the AI Assistant for BC Tech Computer Education.
                Verified Student Data from sheets:
                {details_text}

                CRITICAL INSTRUCTION FOR MULTIPLE RECORDS:
                - If the student is found in multiple sheets or courses, YOU MUST DISPLAY ALL OF THEM clearly one after another.
                - Do not skip or merge any record.
                
                LANGUAGE RULE:
                - Target Language: {"GUJARATI" if user_wants_gujarati else "ENGLISH"}.
                - Unless user specifically typed in Gujarati script, output 100% in pure, professional ENGLISH.

                Output Format for each record found:
                📌 [Course / Sheet Name]
                - Name: [Student Name]
                - Exam / Course: [Course]
                - Theory Marks: [Score]
                - Practical Marks: [Score]
                - Result: [Pass / Grade if available]

                Add 1 short congratulatory/encouraging line at the end.
                Output ONLY the verified student result details.
                """
            elif check_is_result_intent(query) or st.session_state.waiting_for_result_name:
                st.session_state.waiting_for_result_name = True
                if user_wants_gujarati:
                    reply = "परिणाम देखने के लिए कृपया अपना पूरा नाम यहाँ लिखें."
                else:
                    reply = "Please enter your full Student Name to check your exam result."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                system_prompt = None
            else:
                system_prompt = f"""
                You are the counselor for BC Tech Computer Education.
                
                LANGUAGE RULE:
                - Target Language: {"GUJARATI" if user_wants_gujarati else "ENGLISH"}.
                - Unless user specifically typed in Gujarati script, reply strictly in ENGLISH.
                
                CRITICAL INSTRUCTIONS:
                1. Give direct, concise answer (2 to 4 sentences max).
                2. If asked about BRANCH or LOCATION, provide this link: {BRANCH_LINK}
                3. NEVER discuss or quote fees/pricing.
                4. NEVER use the word 'Free'.
                5. Output ONLY the answer without <think> or notes.

                Institute Details:
                {KNOWLEDGE_BASE}
                """

            if system_prompt:
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
                                    max_tokens=350
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
