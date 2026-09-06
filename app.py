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
    .stButton>button:hover {
        background-color: #f1f3f4;
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
    
    # 1. Exact match
    matched = df[name_series == search_term]
    
    # 2. Contains match
    if matched.empty:
        matched = df[name_series.str.contains(search_term, regex=False, na=False)]
        
    # 3. Individual word match
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
- Main Offerings: Professional computer training, practical practical-oriented learning, ISO certified courses, job assistance.
- Popular Courses: Basic Computer Course, Graphic Designing (CorelDraw, Photoshop, Illustrator), Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages with copy button
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            col1, _ = st.columns([0.2, 0.8])
            with col1:
                # Copy trigger using code block helper
                if st.button("📋 Copy", key=f"copy_hist_{idx}"):
                    st.code(msg["content"], language=None)
                    st.toast("Text box me copy karne ke liye ready hai!", icon="📋")

query = st.chat_input("🔍 Type your question or Student Name here...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    df_sheet, err = load_sheet_data()
    
    with st.chat_message("assistant"):
        if err:
            st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
        elif is_generic_result_request(query) and len(query.strip().split()) <= 3 and not search_student(query, df_sheet):
            reply = "📋 **Result Check:**\n- **Hindi/Hinglish:** Apna result dekhne ke liye kripya apna **Pura Naam (Student Name)** yahan type karein.\n- **ગુજરાતી:** તમારું પરિણામ જોવા માટે કૃપા કરીને તમારું **પૂરું નામ** અહીં લખો.\n- **English:** Please enter your **Full Student Name** to check your exam result."
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            matched_records = search_student(query, df_sheet)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            with st.spinner("Processing..."):
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

                        STRICT LANGUAGE RULE:
                        - If the user wrote in Gujarati (or Gujarati script/words like 'kem chho', 'naam'), reply 100% in natural, pure GUJARATI.
                        - If the user wrote in Hindi or Hinglish, reply 100% in natural, polite HINDI/HINGLISH.
                        - If the user wrote in English, reply 100% in professional, clear ENGLISH.
                        - Never mix multiple languages or output broken words.

                        Format:
                        - Display marks in clear bullet points (Student Name, Exam Course, Theory Marks, Practical Marks).
                        - Congratulate them warmly.
                        """
                    else:
                        system_prompt = f"""
                        You are the professional counselor for Bctech Computer Education.
                        
                        CRITICAL RESTRICTIONS:
                        1. NEVER tell, estimate, or discuss any COURSE FEES or charges.
                           - If asked in Hindi/Hinglish: "Fees ki jankari ke liye kripya direct institute branch par visit karein ya diye gaye number par call/WhatsApp karein."
                           - If asked in Gujarati: "ફી અંગેની સંપૂર્ણ માહિતી માટે કૃપા કરીને રૂબરૂ સંસ્થાની મુલાકાત લો અથવા સંપર્ક નંબર પર કોલ/વોટ્સએપ કરો."
                           - If asked in English: "For complete details regarding course fees, please visit our institute branch directly or contact us via call/WhatsApp."
                        2. NEVER mention or use the word 'Free'.
                        3. If user introduces themselves (e.g. 'mera naam ...', 'maru name ...', 'my name is ...'), greet them politely in 1-2 lines in THAT SAME LANGUAGE and ask how you can assist.
                        4. If user searched for an exam result and the name was not found:
                           - In Hindi: "Ye naam result sheet me nahi mila. Kripya sahi spelling check karein."
                           - In Gujarati: "આ નામ રીઝલ્ટ શીટમાં મળ્યું નથી. કૃપા કરીને સ્પેલિંગ ચેક કરો."
                           - In English: "This name was not found in the result sheet. Please verify the spelling."
                        
                        STRICT LANGUAGE MATCHING:
                        - User asks in English -> Respond entirely in polished English.
                        - User asks in Hindi/Hinglish -> Respond entirely in polite Hindi/Hinglish.
                        - User asks in Gujarati -> Respond entirely in pure Gujarati.
                        - Do NOT mix scripts or output corrupted tokens.
                        
                        Institute Information:
                        {KNOWLEDGE_BASE}
                        """

                    # Fetch currently live active chat models from Groq API directly
                    models_resp = client.models.list()
                    live_models = [
                        m.id for m in models_resp.data 
                        if "whisper" not in m.id and "guard" not in m.id and "vision" not in m.id
                    ]
                    
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
                                max_tokens=450
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
                        
                        # Copy button for the latest answer
                        col_btn, _ = st.columns([0.2, 0.8])
                        with col_btn:
                            if st.button("📋 Copy", key=f"copy_latest_{len(st.session_state.messages)}"):
                                st.code(answer, language=None)
                                st.toast("Text copy karne ke liye ready hai!", icon="📋")
                    else:
                        st.error(f"Groq API Error: {last_api_err}")
                except Exception as e:
                    st.error(f"Error: {e}")
