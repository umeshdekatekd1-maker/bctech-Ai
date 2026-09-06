import streamlit as st
from groq import Groq
import pandas as pd
import requests
import io
import re

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Custom Clean Google-like Styling
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
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
</style>
""", unsafe_allow_html=True)

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

# Strip <think> tags completely
def clean_ai_response(text):
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()

KNOWLEDGE_BASE = """
About Bctech Computer Education:
- Institute: Bctech Computer Education (Website: https://sites.google.com/view/bctechcomputer)
- Main Offerings: Professional computer training, practical learning, ISO certified courses, job assistance.
- Popular Courses: Basic Computer Course, Graphic Designing (CorelDraw, Photoshop, Illustrator), Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
if "waiting_for_result_name" not in st.session_state:
    st.session_state.waiting_for_result_name = False

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
                    3. Format details with concise bullet points:
                       - Name
                       - Exam Course
                       - Theory Marks
                       - Practical Marks
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
                2. NEVER output <think>, chain of thought, notes, or internal reasoning steps.
                3. NEVER tell, estimate, or discuss any fees or pricing. Always direct to branch contact.
                4. NEVER mention or use the word 'Free'.
                5. Match the user's language strictly (Hindi/Hinglish, Gujarati, or English).
                6. If user introduces their name, greet them in 1 short line.

                Institute Info:
                {KNOWLEDGE_BASE}
                """

            with st.spinner("Thinking..."):
                try:
                    # Dynamically get active models from Groq
                    models_resp = client.models.list()
                    active_ids = [
                        m.id for m in models_resp.data 
                        if "whisper" not in m.id and "guard" not in m.id and "vision" not in m.id
                    ]
                    
                    # Sort prioritizing top stable non-reasoning chat models
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
