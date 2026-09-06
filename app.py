import streamlit as st
from google import genai
import time

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Google Style Search Bar CSS
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 700px;}
    
    /* Clean rounded search box */
    div[data-baseweb="input"] {
        border-radius: 28px !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.20) !important;
        border: 1px solid #dfe1e5 !important;
        padding-left: 12px;
    }
    div[data-baseweb="input"]:focus-within {
        box-shadow: 0 2px 8px rgba(32,33,36,0.35) !important;
        border-color: #4285F4 !important;
    }
    
    /* Search button */
    .stButton button {
        border-radius: 20px !important;
        padding: 8px 24px !important;
        font-weight: 500;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Purana Title aur Subtitle
st.title("🎓 Bctech AI Assistant")
st.write("Bctech Computer Education ke courses, syllabus ya design/accounting doubts yahan puchein!")

# Google Style Search Bar
query = st.text_input("Search", placeholder="🔍 Yahan apna sawal search karein...", label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    search_btn = st.button("Search with AI")

if (search_btn or query) and query.strip():
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    with st.spinner("Dhoondh raha hai..."):
        prompt = f"""
        You are a helpful AI counselor for 'Bctech Computer Education' institute.
        Help students with clear and simple advice in Hinglish.
        Question: {query}
        """
        
        MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.6-flash"]
        answer = None
        last_err = None

        for m in MODELS_TO_TRY:
            try:
                res = client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                answer = res.text
                break
            except Exception as e:
                last_err = e
                time.sleep(1)
        
        if answer:
            st.success("AI Jawab:")
            st.write(answer)
        else:
            st.error(f"Traffic error: {last_err}")
