import streamlit as st
from google import genai
import time

st.set_page_config(page_title="Bctech AI", layout="centered", initial_sidebar_state="collapsed")

# Google Style CSS
st.markdown("""
<style>
    /* Hide Streamlit default header/footer */
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 680px;}
    
    /* Google style logo */
    .google-title {
        text-align: center;
        font-family: 'Product Sans', Roboto, sans-serif;
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .google-title span:nth-child(1) { color: #4285F4; }
    .google-title span:nth-child(2) { color: #EA4335; }
    .google-title span:nth-child(3) { color: #FBBC05; }
    .google-title span:nth-child(4) { color: #4285F4; }
    .google-title span:nth-child(5) { color: #34A853; }
    .google-title span:nth-child(6) { color: #EA4335; }
    
    .subtitle {
        text-align: center;
        color: #5f6368;
        font-size: 14px;
        margin-bottom: 24px;
    }
    
    /* Search box styling */
    div[data-baseweb="input"] {
        border-radius: 28px !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important;
        border: 1px solid #dfe1e5 !important;
        padding-left: 10px;
    }
    div[data-baseweb="input"]:focus-within {
        box-shadow: 0 1px 6px rgba(32,33,36,0.4) !important;
    }
    
    /* Google Search Button */
    .stButton button {
        background-color: #f8f9fa !important;
        color: #3c4043 !important;
        border: 1px solid #f8f9fa !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        padding: 8px 18px !important;
        margin: 0 auto;
        display: block;
    }
    .stButton button:hover {
        border: 1px solid #dadce0 !important;
        background-color: #f1f3f4 !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# Logo
st.markdown('<div class="google-title"><span>B</span><span>c</span><span>t</span><span>e</span><span>c</span><span>h</span></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask any question about Courses, Fees & Careers</div>', unsafe_allow_html=True)

# Input
query = st.text_input("", placeholder="Search courses or ask anything...", label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    search_clicked = st.button("Google Search")

if (search_clicked or query) and query.strip():
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    with st.spinner("Searching..."):
        prompt = f"""
        You are an intelligent counselor for 'Bctech Computer Education'.
        Give direct, accurate, and friendly answers in Hinglish.
        Question: {query}
        """
        MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.6-flash"]
        answer = None
        
        for m in MODELS_TO_TRY:
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                answer = res.text
                break
            except Exception:
                time.sleep(1)
        
        if answer:
            st.markdown("---")
            st.markdown(f"**Result for:** *{query}*")
            st.write(answer)
