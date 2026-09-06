import streamlit as st
from google import genai

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

    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    with st.chat_message("assistant"):
        with st.spinner("AI jawab taiyar kar raha hai..."):
            prompt = f"""
            You are a helpful AI counselor for Bctech Computer Education.
            Answer in friendly, helpful Hinglish.
            Question: {query}
            """
            try:
                res = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                answer = res.text
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                err_text = str(e)
                if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                    st.warning("Aaj ki free sawal puchne ki limit poori ho gayi hai. Kripya thodi der baad ya kal koshish karein.")
                else:
                    st.error(f"Error: {e}")
