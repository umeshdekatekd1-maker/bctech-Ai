import streamlit as st
from groq import Groq
import pandas as pd
import requests
import io

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Clean Styling
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

def is_generic_result_request(text):
    text = text.lower().strip()
    keywords = [
        "result check", "check result", "result dekhna", "result dekhna hai", "marks dekhna", 
        "result batao", "result", "exam result", "marks", "પરિણામ", "રિઝલ્ટ", "રીઝલ્ટ", 
        "માર્ક્સ", "રિઝલ્ટ ચેક", "પરિણામ જોવું છે"
    ]
    return any(kw in text for kw in keywords)

def search_student(query_text, df):
    if df is None or df.empty:
        return []
    
    clean_q = query_text.strip().lower()
    fillers = [
        "result", "marks", "kya", "hai", "check", "batao", "mera", "meri", "ka", "ki", 
        "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam", "name",
        "chhe", "che", "maru", "maro", "મારું", "મારુ", "નામ", "આપો", "છે", "જોવું"
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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("🔍 Yahan apna sawal ya Student Name likhein...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    df_sheet, err = load_sheet_data()
    
    with st.chat_message("assistant"):
        if err:
            st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
        elif is_generic_result_request(query) and len(query.strip().split()) <= 3 and not search_student(query, df_sheet):
            reply = "📋 Apna exam result dekhne ke liye kripya apna **Pura Naam (Student Name)** yahan type karein.\n\nતમારું પરિણામ જોવા માટે કૃપા કરીને તમારું **પૂરું નામ** અહીં લખો."
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            matched_records = search_student(query, df_sheet)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            with st.spinner("Soch raha hai..."):
                try:
                    if matched_records:
                        details_text = ""
                        for idx, record in enumerate(matched_records[:3], 1):
                            details_text += f"\n--- Student Record {idx} ---\n"
                            for k, v in record.items():
                                if pd.notna(v) and str(v).strip() != "" and "unnamed" not in str(k).lower():
                                    details_text += f"{k}: {v}\n"

                        system_prompt = f"""
                        You are the professional AI Assistant for Bctech Computer Education.
                        Verified exam record from sheet:
                        {details_text}

                        Rules:
                        1. Reply strictly in the language used by user (Gujarati, Hindi/Hinglish, or English).
                        2. Never output broken or repeating random text.
                        3. Clearly format student marks using clean bullet points.
                        4. Congratulate the student politely.
                        """
                    else:
                        system_prompt = f"""
                        You are the professional counselor for Bctech Computer Education.
                        
                        CRITICAL RULES:
                        1. NEVER tell, estimate, or discuss any fees or pricing. Politely direct to branch contact.
                        2. NEVER mention or use the word 'Free'.
                        3. If user is introducing themselves (e.g. 'mera naam ... hai' or 'maru name ... chhe'), greet them politely in 1-2 friendly sentences in the same language and ask how you can help.
                        4. If user asked for an exam result and that name was not found in records, tell them politely that the name was not found in the sheet.
                        5. Speak cleanly and naturally in Gujarati, Hinglish, or English. Never generate gibberish or unrelated scripts.
                        
                        Institute Info:
                        {KNOWLEDGE_BASE}
                        """

                    # Fetch currently live active chat models from Groq API directly
                    models_resp = client.models.list()
                    live_models = [
                        m.id for m in models_resp.data 
                        if "whisper" not in m.id and "guard" not in m.id and "vision" not in m.id
                    ]
                    
                    # Prioritize top stable chat models
                    preferred_order = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
                    sorted_models = [m for m in preferred_order if m in live_models] + [m for m in live_models if m not in preferred_order]

                    answer = None
                    last_api_err = None
                    for model_name in sorted_models:
                        try:
                            chat_completion = client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": query}
                                ],
                                model=model_name,
                                temperature=0.3,
                                max_tokens=400
                            )
                            answer = chat_completion.choices[0].message.content
                            if answer:
                                break
                        except Exception as ex:
                            last_api_err = ex
                            continue
                    
                    if answer:
                        st.write(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"Groq API Error: {last_api_err}")
                except Exception as e:
                    st.error(f"Error: {e}")
