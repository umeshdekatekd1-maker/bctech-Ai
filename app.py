import streamlit as st
from google import genai
import time

st.set_page_config(page_title="Bctech AI Assistant", layout="centered")

st.title("🎓 Bctech AI Assistant")
st.write("Bctech Computer Education ke courses, syllabus ya design/accounting doubts yahan puchein!")

# API Client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

user_query = st.text_area("Apna sawal likhein:", placeholder="Jaise: Graphic design sikhne ke baad freelance kaise karein?")

if st.button("Ask AI (Puchhein)"):
    if user_query.strip():
        with st.spinner("AI jawab taiyar kar raha hai..."):
            prompt = f"""
            You are a helpful AI counselor for 'Bctech Computer Education' institute.
            Help students with clear and simple advice in Hinglish.
            Question: {user_query}
            """
            
            # Retry loop for temporary 503 server load
            response_text = None
            last_error = None
            
            for attempt in range(4):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    response_text = response.text
                    break
                except Exception as e:
                    last_error = e
                    time.sleep(2)
            
            if response_text:
                st.success("AI Jawab:")
                st.write(response_text)
            else:
                st.error(f"Error: {last_error}")
    else:
        st.warning("Pehle apna sawal type karein.")
