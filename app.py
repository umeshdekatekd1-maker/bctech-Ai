import streamlit as st
from groq import Groq

st.set_page_config(page_title="Bctech AI Assistant", layout="centered", initial_sidebar_state="collapsed")

# Styling
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

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("🔍 Yahan apna sawal search karein...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # Active supported models on Groq
    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.2-3b-preview",
        "llama-3.2-11b-vision-preview",
        "gemma2-9b-it"
    ]
    
    with st.chat_message("assistant"):
        with st.spinner("AI jawab taiyar kar raha hai..."):
            answer = None
            last_err = None
            
            for mod in AVAILABLE_MODELS:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful and friendly AI counselor for Bctech Computer Education institute. Guide students on courses, fees, syllabus, and computer career advice in simple Hinglish."
                            },
                            {
                                "role": "user",
                                "content": query,
                            }
                        ],
                        model=mod,
                    )
                    answer = chat_completion.choices[0].message.content
                    break
                except Exception as e:
                    last_err = e
                    continue
            
            if answer:
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"Model Error: {last_err}")
