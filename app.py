import streamlit as st
import google.generativeai as genai
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="MBA Talent Scout AI", layout="wide")
st.title("🎯 Strategic Talent Scout")
st.subheader("Gemini-Powered Candidate Ranking for MBA Projects")

# --- SETUP API KEY ---
# In a real app, use st.secrets for security
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- SIDEBAR: JOB DESCRIPTION ---
    st.sidebar.header("Step 1: Job Details")
    jd_text = st.sidebar.text_area("Paste Job Description Here:", height=300)

    # --- MAIN AREA: UPLOAD ---
    st.header("Step 2: Upload Resumes")
    uploaded_files = st.file_uploader("Upload PDF Resumes", type="pdf", accept_multiple_files=True)

    if st.button("🚀 Analyze & Rank Candidates"):
        if not jd_text or not uploaded_files:
            st.error("Please provide both a JD and at least one resume.")
        else:
            with st.spinner("Gemini is analyzing career trajectories..."):
                # Prepare the prompt
                prompt = f"""
                You are a Senior Executive Recruiter. Analyze the following resumes against this Job Description:
                JD: {jd_text}
                
                Provide a ranked list in a Markdown table with:
                1. Candidate Name
                2. Match Score (0-100)
                3. Strategic Fit (Briefly explain why based on leadership/impact)
                4. Potential Gap (One thing they are missing)
                """
                
                # Convert PDFs to a format Gemini understands
                # Note: For simplicity in this script, we send them as parts
                files_to_send = []
                for uploaded_file in uploaded_files:
                    # Reading the PDF bytes
                    file_data = uploaded_file.read()
                    files_to_send.append({"mime_type": "application/pdf", "data": file_data})

                # Generate Content
                response = model.generate_content([prompt] + files_to_send)
                
                st.success("Analysis Complete!")
                st.markdown(response.text)
else:
    st.warning("Please enter your Google AI API Key in the sidebar to begin.")
