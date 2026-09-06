import streamlit as st
from google import genai

st.set_page_config(page_title="Bctech AI Assistant", layout="centered")

st.title("🎓 Bctech AI Assistant")
st.write("Bctech Computer Education ke courses, syllabus ya design/accounting doubts yahan puchein!")

# API Client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

user_query = st.text_area("Apna sawal likhein:", placeholder="Jaise: Graphic design sikhne ke baad freelance kaise karein?")

if st.button("Ask AI (Puchhein)"):
    if user_query.strip():
        with st.spinner("AI jawab taiyar kar raha hai..."):
            try:
                prompt = f"""
                You are a helpful AI counselor for 'Bctech Computer Education' institute.
                Help students with clear and simple advice in Hinglish.
                Question: {user_query}
                """
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                st.success("AI Jawab:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Pehle apna sawal type karein.")
