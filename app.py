import streamlit as st
from groq import Groq
import pandas as pd

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Custom Styling
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

# Google Sheet CSV URL
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=15)
def load_sheet_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = [str(c).strip() for c in df.columns]
        # Unnamed columns hatayein
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return df
    except Exception as e:
        return None

# Powerful Smart Search - Sheet ke har cell me check karega
def search_student_data(query_text, df):
    if df is None or df.empty:
        return []
    
    clean_q = query_text.strip().lower()
    stop_words = {"result", "marks", "kya", "hai", "check", "batao", "mera", "meri", "ka", "ki", "dekho", "please", "sir", "bctech", "mujhko", "dekhna"}
    
    words = [w for w in clean_q.split() if w not in stop_words and len(w) >= 2]
    if not words:
        words = [clean_q]

    matched_indices = set()
    
    # 1. Check complete query match across all text
    for col in df.columns:
        col_series = df[col].astype(str).str.strip().str.lower()
        exact_hits = df[col_series == clean_q].index
        matched_indices.update(exact_hits)

    # 2. Check each word match
    if not matched_indices:
        for word in words:
            for col in df.columns:
                col_series = df[col].astype(str).str.strip().str.lower()
                hits = df[col_series.str.contains(word, regex=False, na=False)].index
                matched_indices.update(hits)

    if matched_indices:
        results_df = df.loc[list(matched_indices)]
        return results_df.dropna(how='all').to_dict(orient="records")
    return []

# Website Knowledge Base
KNOWLEDGE_BASE = """
About Bctech Computer Education:
- Institute: Bctech Computer Education (Website: https://sites.google.com/view/bctechcomputer)
- Main Offerings: Professional computer training, practical practical-oriented learning, ISO certified courses, job assistance.
- Popular Courses: Basic Computer Course, Graphic Designing (CorelDraw, Photoshop), Accounting & Tally Prime, Web Development, Programming (Python, C++), Digital Marketing, Advanced Excel.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("🔍 Apna Naam ya Course ka sawal search karein...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    df_sheet = load_sheet_data()
    matched_records = search_student_data(query, df_sheet)

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    with st.chat_message("assistant"):
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
                    A student has searched for their result and we FOUND their record in the institute Google Sheet:
                    {details_text}

                    Instructions:
                    1. Show their details in an easy-to-read, clean format (Name, Course, Marks/Grade, Status).
                    2. Congratulate them if they passed.
                    3. Do not ask for their name again because their record is already found above.
                    4. Reply in polite, clear Hinglish.
                    """
                else:
                    system_prompt = f"""
                    You are the official AI Counselor for Bctech Computer Education.
                    STRICT RESTRICTIONS:
                    1. NEVER tell, estimate, or guess any COURSE FEES or charges. Politely refuse: "Fees ki jankari ke liye kripya direct institute branch par visit karein ya call karein."
                    2. NEVER mention or use the word 'Free'.
                    3. If the user appears to be searching for an exam result or marks, explain that their name was not found in the sheet and ask them to type their exact spelling/full name as per admission record.
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
