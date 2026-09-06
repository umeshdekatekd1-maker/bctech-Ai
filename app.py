import streamlit as st
from google import genai
import time

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Custom Styling
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem; max-width: 720px;}
    
    /* Search box styling */
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

# Session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation history above
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input field at bottom
query = st.chat_input("🔍 Yahan apna sawal search karein...")

if query:
    # 1. Show user query immediately
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    # 2. Get AI Response
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    with st.chat_message("assistant"):
        with st.spinner("AI jawab taiyar kar raha hai..."):
            prompt = f"""
            You are a helpful AI counselor for Bctech Computer Education.
            Help students with clear and friendly guidance in Hinglish.
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
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"Traffic error: {last_err}")
