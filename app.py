import streamlit as st
from groq import Groq
import pandas as pd

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
</style>
""", unsafe_allow_html=True)

st.title("🎓 Bctech AI Assistant")

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=15)
def load_sheet_data():
    try:
        # Load CSV and clean columns
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = [str(c).strip() for c in df.columns]
        # Ignore empty or separator rows like 'Batch Times'
        first_col = df.columns[0]
        df = df[df[first_col].notna()]
        df = df[~df[first_col].astype(str).str.lower().str.contains("batch time", na=False)]
        return df
    except Exception:
        return None

def is_generic_result_request(text):
    text = text.lower().strip()
    keywords = ["result check", "check result", "result dekhna", "result dekhna hai", "marks dekhna", "result batao", "result", "exam result", "marks"]
    return any(text == kw or text.replace(" ", "") == kw.replace(" ", "") for kw in keywords)

def search_student_by_name(query_text, df):
    if df is None or df.empty:
        return []
    
    clean_q = query_text.strip().lower()
    # Remove conversation filler words, but KEEP names
    fillers = ["result", "marks", "kya", "hai", "check", "batao", "mera", "meri", "ka", "ki", "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam"]
    words = [w for w in clean_q.split() if w not in fillers and len(w) >= 2]
    
    if not words:
        words = [clean_q]

    search_term = " ".join(words)
    first_col = df.columns[0] # Student Name column

    # 1. Direct name match in first column (Student Name)
    name_series = df[first_col].astype(str).str.strip().str.lower()
    
    # Exact full name match
    matched = df[name_series == search_term]
    
    # Partial / First name match if exact not found
    if matched.empty:
        for w in words:
            matched = df[name_series.str.contains(w, regex=False, na=False)]
            if not matched.empty:
                break
                
    # Fallback: Search in entire table
    if matched.empty:
        for col in df.columns:
            matched = df[df[col].astype(str).str.strip().str.lower().str.contains(search_term, regex=False, na=False)]
            if not matched.empty:
                break

    if not matched.empty:
        return matched.dropna(how="all").to_dict(orient="records")
    return []

KNOWLEDGE_BASE = """
About Bctech Computer Education:
- Institute: Bctech Computer Education (Website: https://sites.google.com/view/bctechcomputer)
- Main Offerings: Professional computer training, practical learning, ISO certified courses, job assistance.
- Popular Courses: Basic Computer Course, Graphic Designing, Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
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

    df_sheet = load_sheet_data()
    
    with st.chat_message("assistant"):
        if is_generic_result_request(query):
            reply = "📋 Apna exam result dekhne ke liye kripya apna **Pura Naam (Student Name)** yahan type karein."
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            matched_records = search_student_by_name(query, df_sheet)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            with st.spinner("Record check kiya ja raha hai..."):
                try:
                    models_data = client.models.list()
                    active_models = [m.id for m in models_data.data if "whisper" not in m.id]
                    
                    if matched_records:
                        details_text = ""
                        for idx, record in enumerate(matched_records[:3], 1):
                            details_text += f"\n--- Student Record {idx} ---\n"
                            for k, v in record.items():
                                if pd.notna(v) and str(v).strip() != "":
                                    details_text += f"{k}: {v}\n"

                        system_prompt = f"""
                        You are the AI Assistant for Bctech Computer Education.
                        A student entered their name and here is their exam record from the sheet:
                        {details_text}

                        Instructions:
                        1. Display the student's name, exam name, theory marks, and practical marks in a neat bulleted list or small table.
                        2. Congratulate them on their performance.
                        3. Reply in natural, polite Hinglish.
                        """
                    else:
                        system_prompt = f"""
                        You are the official AI Counselor for Bctech Computer Education.
                        STRICT RESTRICTIONS:
                        1. NEVER tell, estimate, or guess any COURSE FEES or charges. Politely refuse: "Fees ki jankari ke liye kripya direct institute branch par visit karein ya diye gaye number par call karein."
                        2. NEVER mention or use the word 'Free'.
                        3. If user entered a name and it is not found, inform: "Ye naam result sheet me nahi mila. Kripya sahi spelling check karein."
                        4. Reply in natural, friendly Hinglish.

                        Institute Information:
                        {KNOWLEDGE_BASE}
                        """

                    answer = None
                    for selected_model in active_models:
                        try:
                            chat_completion = client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": query}
                                ],
                                model=selected_model,
                            )
                            answer = chat_completion.choices[0].message.content
                            break
                        except Exception:
                            continue
                    
                    if answer:
                        st.write(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Filhal AI uplabdh nahi hai. Thodi der baad try karein.")
                except Exception as e:
                    st.error(f"Error: {e}")
