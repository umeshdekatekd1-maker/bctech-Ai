import streamlit as st
from groq import Groq
import pandas as pd
import requests
import io

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Custom Clean Styling
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
        border-radius: 18px;
        padding: 2px 14px;
        font-size: 13px;
        border: 1px solid #dadce0;
        background-color: #f8f9fa;
        color: #3c4043;
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

# Check if query asks for result
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

# Render conversation history with copy button
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            col_b, _ = st.columns([0.2, 0.8])
            with col_b:
                if st.button("📋 Copy", key=f"copy_hist_{idx}"):
                    st.code(msg["content"], language=None)
                    st.toast("Copied to clipboard!", icon="📋")

query = st.chat_input("🔍 Yahan apna sawal likhein / અહીં તમારો પ્રશ્ન લખો...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    df_sheet, err = load_sheet_data()
    
    with st.chat_message("assistant"):
        if err:
            st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
        else:
            is_result_query = check_is_result_intent(query) or st.session_state.waiting_for_result_name
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Case 1: Student is asking for exam result
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
                    1. Detect the user's language (Gujarati, Hindi, or English) and reply in that same language.
                    2. IMPORTANT: Keep English student names and numbers exact. Do NOT corrupt characters or generate . Write names cleanly (e.g., 'Ganesh' or 'ગણેશ').
                    3. Format details clearly with bullet points:
                       - Name
                       - Exam Course
                       - Theory Marks
                       - Practical Marks
                    4. Congratulate them politely.
                    """
                else:
                    # User asked for result but didn't provide name yet, or name wasn't found
                    st.session_state.waiting_for_result_name = True
                    system_prompt = f"""
                    You are the AI Assistant for Bctech Computer Education.
                    The user wants to check an exam result, but no matching name was found in the sheet.
                    
                    Instructions:
                    - If user spoke Gujarati: "પરિણામ જોવા માટે કૃપા કરીને તમારું સાચું પૂરું નામ (Student Name) અહીં લખો."
                    - If user spoke Hindi/Hinglish: "Apna exam result dekhne ke liye kripya apna sahi Pura Naam (Student Name) yahan type karein."
                    - If user spoke English: "Please type your full Student Name to check your exam result."
                    """
            else:
                # Case 2: Normal conversation or introduction (NOT a result request)
                system_prompt = f"""
                You are the professional counselor for Bctech Computer Education institute.
                
                STRICT RESTRICTIONS:
                1. NEVER tell, estimate, or discuss any fees or pricing. Always say to contact branch directly.
                2. NEVER mention or use the word 'Free'.
                3. DO NOT SHOW ANY EXAM RESULTS OR MARKS here.
                4. If the user introduces themselves (e.g., 'maru name ... chhe', 'mera naam ... hai', 'my name is ...'), greet them politely and warmly in THAT SAME LANGUAGE (Gujarati, Hindi, or English) in 1-2 friendly sentences and ask how you can assist them today.
                5. Output only clean, proper text without corrupted characters ().

                Institute Info:
                {KNOWLEDGE_BASE}
                """

            with st.spinner("Processing..."):
                try:
                    models_resp = client.models.list()
                    live_models = [m.id for m in models_resp.data if "whisper" not in m.id and "guard" not in m.id]
                    preferred = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
                    candidate_models = [m for m in preferred if m in live_models] + [m for m in live_models if m not in preferred]

                    answer = None
                    for m_name in candidate_models:
                        try:
                            chat_completion = client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": query}
                                ],
                                model=m_name,
                                temperature=0.2,
                                max_tokens=400
                            )
                            answer = chat_completion.choices[0].message.content
                            if answer:
                                break
                        except Exception:
                            continue
                    
                    if answer:
                        st.write(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        col_btn, _ = st.columns([0.2, 0.8])
                        with col_btn:
                            if st.button("📋 Copy", key=f"copy_latest_{len(st.session_state.messages)}"):
                                st.code(answer, language=None)
                                st.toast("Copied to clipboard!", icon="📋")
                    else:
                        st.error("Filhal AI uplabdh nahi hai. Thodi der baad prayas karein.")
                except Exception as e:
                    st.error(f"Error: {e}")
