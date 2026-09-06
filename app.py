import streamlit as st
from groq import Groq
import pandas as pd

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Custom Google Styling
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

# Direct CSV export from your Google Sheet
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg/export?format=csv"

@st.cache_data(ttl=60)
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

def search_student_result(query_text, df):
    if df is None or df.empty:
        return None
    words = query_text.strip().split()
    for word in words:
        clean_word = word.strip().lower()
        if len(clean_word) >= 2:
            for col in df.columns:
                matches = df[df[col].astype(str).str.strip().str.lower() == clean_word]
                if not matches.empty:
                    return matches.iloc[0].dropna().to_dict()
    return None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("🔍 Yahan apna sawal ya Roll Number search karein...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    df_sheet = load_sheet_data(SHEET_CSV_URL)
    found_student = search_student_result(query, df_sheet)

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    with st.chat_message("assistant"):
        with st.spinner("Jankari check ho rahi hai..."):
            try:
                models_data = client.models.list()
                active_models = [m.id for m in models_data.data if "whisper" not in m.id]
                
                if found_student:
                    student_info_str = "\n".join([f"{k}: {v}" for k, v in found_student.items()])
                    system_prompt = f"""
                    You are the AI Assistant for Bctech Computer Education.
                    A student has checked their exam result. Here is their verified record directly from the official Google Sheet:
                    {student_info_str}
                    
                    Instructions:
                    1. Present the result in a clean, professional, and readable table or bullet list.
                    2. Congratulate them if they passed.
                    3. Do not show any unnecessary technical details.
                    4. Reply in friendly Hinglish.
                    """
                else:
                    system_prompt = f"""
                    You are the official AI Counselor for Bctech Computer Education.
                    STRICT RESTRICTIONS:
                    1. NEVER tell, estimate, or guess any COURSE FEES or charges. Politely refuse: "Fees ki jankari ke liye kripya direct institute branch par visit karein ya diye gaye contact number par call karein."
                    2. NEVER mention or use the word 'Free'.
                    3. If student is searching for their exam result, ask them to type their exact Roll Number or Enrollment No.
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
                    st.error("Filhal AI uplabdh nahi hai. Thodi der baad koshish karein.")
            except Exception as e:
                st.error(f"Error: {e}")
