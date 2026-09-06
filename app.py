import streamlit as st
from groq import Groq

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

# Website Knowledge Base
KNOWLEDGE_BASE = """
About Bctech Computer Education:
- Institute: Bctech Computer Education (Website: https://sites.google.com/view/bctechcomputer)
- Main Offerings: Professional computer training, practical practical-oriented learning, ISO certified courses, job assistance.
- Popular Courses:
  1. Basic Computer Course (Windows, MS Office - Word, Excel, PowerPoint, Internet concepts)
  2. Graphic Designing (CorelDraw, Photoshop, Illustrator, Adobe Express, banner & brochure designing)
  3. Accounting & Tally (Tally Prime, GST filing, inventory management, taxation)
  4. Web Designing & Development (HTML, CSS, JavaScript, responsive web development)
  5. Programming & Coding (Python, C, C++, Data structures)
  6. Digital Marketing (SEO, Social Media Marketing, Ads setup)
  7. Advanced Excel & Data Entry
"""

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
    
    with st.chat_message("assistant"):
        with st.spinner("AI jawab taiyar kar raha hai..."):
            try:
                models_data = client.models.list()
                active_models = [m.id for m in models_data.data if "whisper" not in m.id]
                
                system_prompt = f"""
                You are the official AI Counselor for Bctech Computer Education.
                STRICT RESTRICTIONS:
                1. NEVER tell, estimate, or guess any COURSE FEES or charges. If someone asks about fees, price, cost, discounts, or offers, politely refuse and say: "Fees ki jankari ke liye kripya direct institute branch par visit karein ya diye gaye WhatsApp/Contact number par call karein."
                2. NEVER mention or use the word 'Free'.
                3. Only guide students about course syllabus, benefits, practical lab sessions, and career scopes.
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
