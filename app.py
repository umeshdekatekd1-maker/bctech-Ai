import streamlit as st
from groq import Groq
import pandas as pd
import requests
import io
import re

st.set_page_config(
    page_title="Bctech AI Assistant", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# Custom Clean Styling
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    header {visibility: visible !important;}
    .block-container {padding-top: 1.5rem; max-width: 720px;}
    
    /* Search box rounded */
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
    
    /* Copy Button Right-Aligned */
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
    
    /* Left Sidebar Buttons */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton>button {
        width: 100% !important;
        float: none !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        font-size: 13px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: #f8f9fa !important;
        border: 1px solid #e8eaed !important;
        color: #3c4043 !important;
        margin-bottom: 5px !important;
        cursor: pointer !important;
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

# State initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "saved_sessions" not in st.session_state:
    st.session_state.saved_sessions = []
if "waiting_for_result_name" not in st.session_state:
    st.session_state.waiting_for_result_name = False

def start_new_chat():
    # Save conversation using the LAST user query as the title
    if st.session_state.messages:
        user_messages = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        if user_messages:
            last_msg = user_messages[-1]
            title = (last_msg[:24] + "..") if len(last_msg) > 24 else last_msg
        else:
            title = "Chat"

        st.session_state.saved_sessions.append({
            "title": title,
            "messages": list(st.session_state.messages)
        })
    st.session_state.messages = []
    st.session_state.waiting_for_result_name = False

def load_saved_chat(session_index):
    if 0 <= session_index < len(st.session_state.saved_sessions):
        st.session_state.messages = list(st.session_state.saved_sessions[session_index]["messages"])

# --- Left Sidebar: New Chat & Recent Archived Chats ---
with st.sidebar:
    st.markdown("### 🎓 Bctech AI")
    st.markdown('<div id="new_chat_btn_wrap">', unsafe_allow_html=True)
    if st.button("➕ New Chat", key="side_new_chat_btn", on_click=start_new_chat):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent Section: Shows previously closed chats with last query title
    with st.expander("Recent", expanded=True):
        if st.session_state.saved_sessions:
            for idx, session_item in enumerate(reversed(st.session_state.saved_sessions)):
                actual_idx = len(st.session_state.saved_sessions) - 1 - idx
                st.button(
                    f"💬 {session_item['title']}", 
                    key=f"recent_chat_{actual_idx}",
                    on_click=load_saved_chat,
                    args=(actual_idx,)
                )
        else:
            st.caption("New chat lene ke baad yahan aakhri sawal dikhega.")
            
    st.markdown("---")
    st.markdown("**📌 Quick Links:**")
    st.markdown("🌐 [Official Website](https://sites.google.com/view/bctechcomputer)")
    st.markdown("📍 [Branch Location](https://sites.google.com/view/bctechcomputer/about-us)")

st.title("🎓 Bctech AI Assistant")

SHEET_ID = "1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg"
URL_GVIZ = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
URL_EXPORT = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=15)
def load_sheet_data():
    csv_text = None
    last_error = None
    for url in [URL_GVIZ, URL_EXPORT]:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200 and len(res.content) > 50:
                csv_text = res.content.decode("utf-8")
                break
            else:
                last_error = f"Status Code: {res.status_code}"
        except Exception as e:
            last_error = str(e)
            
    if not csv_text:
        return None, last_error

    try:
        df = pd.read_csv(io.StringIO(csv_text))
        df.columns = [str(c).strip() for c in df.columns]
        first_col = df.columns[0]
        df = df[df[first_col].notna()]
        df = df[~df[first_col].astype(str).str.lower().str.contains("batch time", na=False)]
        df = df[df[first_col].astype(str).str.strip() != ""]
        return df, None
    except Exception as e:
        return None, str(e)

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

def search_student(query_text, df):
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

# Render history with right-aligned copy button
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
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

    df_sheet, err = load_sheet_data()
    
    with st.chat_message("assistant"):
        if err:
            st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
        
        elif is_greeting(query):
            reply = "Hello! Welcome to Bctech Computer Education. How can I help you today? 😊"
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            col_l, col_r = st.columns([0.85, 0.15])
            with col_r:
                if st.button("📋 Copy", key=f"copy_greet_{len(st.session_state.messages)}"):
                    st.code(reply, language=None)
                    st.toast("Copied!", icon="📋")

        elif check_is_branch_intent(query):
            q_lower = query.lower()
            if any(w in q_lower for w in ["ક્યાં", "સરનામું", "શાખા"]):
                reply = f"Bctech Computer Education ની શાખા અને લોકેશનની સંપૂર્ણ વિગત માટે અહીં ક્લિક કરો:\n🔗 {BRANCH_LINK}"
            elif any(w in q_lower for w in ["where", "location", "address"]):
                reply = f"You can check the exact branch location and address details of Bctech Computer Education here:\n🔗 {BRANCH_LINK}"
            else:
                reply = f"Bctech Computer Education ki branch aur location ki puri jankari ke liye kripya hamari website par visit karein:\n🔗 {BRANCH_LINK}"
            
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            col_l, col_r = st.columns([0.85, 0.15])
            with col_r:
                if st.button("📋 Copy", key=f"copy_branch_{len(st.session_state.messages)}"):
                    st.code(reply, language=None)
                    st.toast("Copied!", icon="📋")

        else:
            is_result_query = check_is_result_intent(query) or st.session_state.waiting_for_result_name
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            if is_result_query:
                matched_records = search_student(query, df_sheet)
                
                if matched_records:
                    st.session_state.waiting_for_result_name = False
                    details_text = ""
                    for idx, record in enumerate(matched_records[:2], 1):
                        details_text += f"\nStudent Record:\n"
                        for k, v in record.items():
                            if pd.notna(v) and str(v).strip() != "" and "unnamed" not in str(k).lower():
                                details_text += f"- {k}: {v}\n"

                    system_prompt = f"""
                    You are the AI Assistant for Bctech Computer Education.
                    Student Exam Record:
                    {details_text}

                    Instructions:
                    1. Respond directly in the same language as user query (Gujarati, Hindi, or English).
                    2. Keep student names exact.
                    3. Format details with concise bullet points (Name, Exam Course, Theory Marks, Practical Marks).
                    4. Congratulate them in 1 short line.
                    5. Output ONLY the final answer. NEVER output thinking process, notes, or analysis.
                    """
                else:
                    st.session_state.waiting_for_result_name = True
                    system_prompt = f"""
                    You are the AI Assistant for Bctech Computer Education.
                    The user wants to check an exam result, but no matching name was found.
                    Reply in 1 single short sentence asking for their full name in their language:
                    - If Gujarati: "પરિણામ જોવા માટે કૃપા કરીને તમારું સાચું પૂરું નામ અહીં લખો."
                    - If Hindi/Hinglish: "Apna result dekhne ke liye kripya apna pura naam yahan likhein."
                    - If English: "Please type your full Student Name to check your exam result."
                    Output ONLY this sentence.
                    """
            else:
                system_prompt = f"""
                You are the professional counselor for Bctech Computer Education.
                
                CRITICAL INSTRUCTIONS:
                1. Give ONLY direct, final answer (2 to 4 sentences maximum).
                2. If asked about BRANCH, LOCATION, or WHERE BCTECH IS, provide this link: {BRANCH_LINK}
                3. NEVER output <think>, chain of thought, notes, or internal reasoning steps.
                4. NEVER tell, estimate, or discuss any fees or pricing. Always direct to visit branch or check the website.
                5. NEVER mention or use the word 'Free'.
                6. Match the user's language strictly (Hindi/Hinglish, Gujarati, or English).
                7. If user introduces their name, greet them in 1 short line.

                Institute Info:
                {KNOWLEDGE_BASE}
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
                                temperature=0.3,
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
                        col_l, col_r = st.columns([0.85, 0.15])
                        with col_r:
                            if st.button("📋 Copy", key=f"copy_ast_curr_{len(st.session_state.messages)}"):
                                st.code(answer, language=None)
                                st.toast("Copied!", icon="📋")
                    else:
                        st.error(f"API Error: {last_api_err}")
                except Exception as e:
                    st.error(f"Error: {e}")
