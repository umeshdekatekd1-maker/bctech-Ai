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

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg/export?format=csv"

@st.cache_data(ttl=30)
def load_sheet_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception:
        return None

# Website Knowledge Base
KNOWLEDGE_BASE = """
About Bctech Computer Education:
- Institute: Bctech Computer Education (Website: https://sites.google.com/view/bctechcomputer)
- Main Offerings: Professional computer training, practical practical-oriented learning, ISO certified courses, job assistance.
- Popular Courses:
  1. Basic Computer Course (Windows, MS Office - Word, Excel, PowerPoint)
  2. Graphic Designing (CorelDraw, Photoshop, Illustrator, Adobe Express)
  3. Accounting & Tally (Tally Prime, GST filing)
  4. Web Designing & Development (HTML, CSS, JavaScript)
  5. Programming & Coding (Python, C, C++)
  6. Digital Marketing
  7. Advanced Excel & Data Entry
"""

# Name-only Search Function
def search_student_by_name(query_text, df):
    if df is None or df.empty:
        return None
    
    clean_query = query_text.strip().lower()
    
    # Common words ignore list
    stop_words = {"result", "marks", "kya", "hai", "check", "batao", "mera", "meri", "ka", "ki", "dekho", "please", "sir", "bctech"}
    query_words = [w for w in clean_query.split() if w not in stop_words and len(w) >= 2]
    
    if not query_words:
        return None

    # Identify name column automatically
    name_cols = [col for col in df.columns if any(term in col.lower() for term in ["name", "student", "naam", "candidate"])]
    target_cols = name_cols if name_cols else list(df.columns)

    results = []

    # 1. Exact Full Name Check
    full_name_query = " ".join(query_words)
    for col in target_cols:
        matched = df[df[col].astype(str).str.strip().str.lower() == full_name_query]
        if not matched.empty:
            return matched.to_dict(orient="records")

    # 2. Partial / First Name Match
    for col in target_cols:
        for word in query_words:
            matched = df[df[col].astype(str).str.strip().str.lower().str.contains(word, regex=False, na=False)]
            if not matched.empty:
                for record in matched.to_dict(orient="records"):
                    if record not in results:
                        results.append(record)

    return results if results else None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("🔍 Apna Naam ya Course ka sawal search karein...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    df_sheet = load_sheet_data(SHEET_CSV_URL)
    matched_records = search_student_by_name(query, df_sheet)

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    with st.chat_message("assistant"):
        with st.spinner("Record check kiya ja raha hai..."):
            try:
                models_data = client.models.list()
                active_models = [m.id for m in models_data.data if "whisper" not in m.id]
                
                if matched_records:
                    details_text = ""
                    for idx, student in enumerate(matched_records[:3], 1):
                        details_text += f"\nRecord {idx}:\n"
                        for k, v in student.items():
                            if pd.notna(v):
                                details_text += f"- {k}: {v}\n"
                    
                    system_prompt = f"""
                    You are the AI Assistant for Bctech Computer Education.
                    Found student result record(s) matching the entered name:
                    {details_text}
                    
                    Instructions:
                    1. Present the result clearly with student name, course, marks/grade, and pass/fail status.
                    2. If there are multiple records with similar names, list them clearly so the student can identify theirs.
                    3. Congratulate them if they passed.
                    4. Reply politely in natural Hinglish.
                    """
                else:
                    system_prompt = f"""
                    You are the official AI Counselor for Bctech Computer Education.
                    STRICT RESTRICTIONS:
                    1. NEVER tell, estimate, or guess any COURSE FEES or charges. Politely refuse: "Fees ki jankari ke liye kripya direct institute branch par visit karein ya diye gaye number par call karein."
                    2. NEVER mention or use the word 'Free'.
                    3. If student is asking for result, ask them: "Apna sahi aur pura Naam type karein taaki hum sheet se result check kar sakein."
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
                    st.error("Filhal AI uplabdh nahi hai. Kripya thodi der baad prayas karein.")
            except Exception as e:
                st.error(f"Error: {e}")
