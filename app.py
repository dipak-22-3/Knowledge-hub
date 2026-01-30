import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

# 1. SETUP & AUTHENTICATION
# Try loading from .env (Local) or Secrets (Cloud)
load_dotenv()

# This logic checks if you are on Cloud (st.secrets) or Local (.env)
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ No API Key found! Please check your .env file or Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. PAGE CONFIGURATION
st.set_page_config(page_title="Knowledge Hub", layout="wide", page_icon="🧠")
st.title("🤖 The Knowledge Hub")
st.markdown("---")

# 3. SIDEBAR NAVIGATION
st.sidebar.title("Navigation")
choice = st.sidebar.radio(
    "Go to:",
    (
        "🏠 Home", 
        "📚 Chat with Docs (RAG)", 
        "📝 AI Planner", 
        "📊 Student Analytics", 
        "🎥 YouTube Summarizer"
    )
)

# ==========================================
# PAGE 1: HOME
# ==========================================
if choice == "🏠 Home":
    st.write("### Welcome to your Personal AI Dashboard.")
    st.info("Select a tool from the sidebar to begin.")
    st.markdown("""
    * **📚 Chat with Docs:** Upload PDFs and ask questions.
    * **📝 AI Planner:** Create lesson plans and quizzes instantly.
    * **📊 Student Analytics:** Analyze marks and find trends.
    * **🎥 YouTube Summarizer:** Turn videos into study notes.
    """)

# ==========================================
# PAGE 2: CHAT WITH DOCS (RAG)
# ==========================================
elif choice == "📚 Chat with Docs (RAG)":
    st.header("Chat with your Documents (Powered by Groq)")
    
    uploaded_file = st.file_uploader("Upload a PDF Document", type="pdf")
    
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
            
        st.success(f"✅ PDF Loaded! ({len(text)} characters detected)")
        
        user_question = st.text_input("Ask a question about this document:")
        
        if st.button("Get Answer"):
            if user_question:
                with st.spinner("Thinking..."):
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant. Answer the user's question based ONLY on the text provided below."
                            },
                            {
                                "role": "user",
                                "content": f"Context: {text}\n\nQuestion: {user_question}"
                            }
                        ],
                        model="llama3-8b-8192",
                    )
                    st.write("### 🤖 AI Answer:")
                    st.write(chat_completion.choices[0].message.content)

# ==========================================
# PAGE 3: AI PLANNER (AGENTS)
# ==========================================
elif choice == "📝 AI Planner":
    st.header("📝 AI Lesson & Project Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Enter Topic (e.g., 'Newton's Laws')")
    with col2:
        level = st.selectbox("Target Audience", ["Beginner", "Intermediate", "Advanced"])
    
    if st.button("Generate Plan"):
        if topic:
            with st.spinner("🤖 Agent 1 is writing the lesson plan..."):
                lesson_prompt = f"Create a clear, structured lesson plan for '{topic}' suitable for a {level}. Include: 1. Learning Objectives, 2. Key Concepts, 3. Real-world Examples."
                
                lesson_response = client.chat.completions.create(
                    messages=[{"role": "user", "content": lesson_prompt}],
                    model="llama3-8b-8192",
                )
                lesson_content = lesson_response.choices[0].message.content
                
            st.markdown("### 📘 The Lesson Plan")
            st.write(lesson_content)
            st.markdown("---")
            
            with st.spinner("🤖 Agent 2 is creating the quiz..."):
                quiz_prompt = f"Based ONLY on the lesson plan below, create a 5-question multiple choice quiz with answers at the end.\n\nLESSON PLAN:\n{lesson_content}"
                
                quiz_response = client.chat.completions.create(
                    messages=[{"role": "user", "content": quiz_prompt}],
                    model="llama3-8b-8192",
                )
                quiz_content = quiz_response.choices[0].message.content
                
            st.markdown("### ❓ The Quiz")
            st.write(quiz_content)

# ==========================================
# PAGE 4: STUDENT ANALYTICS (DATA)
# ==========================================
elif choice == "📊 Student Analytics":
    st.header("📊 Student Performance Dashboard")
    
    uploaded_file = st.file_uploader("Upload Student Marks (CSV)", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("File Uploaded Successfully!")
    else:
        st.info("No file? Click below to use dummy data for testing.")
        if st.button("Load Demo Data"):
            data = {
                'Name': ['Amit', 'Rahul', 'Priya', 'Sita', 'Vikram'],
                'Math': [85, 42, 90, 35, 78],
                'Science': [78, 50, 88, 40, 82],
                'English': [92, 60, 95, 55, 80]
            }
            df = pd.DataFrame(data)
        else:
            df = None

    if df is not None:
        st.write("### 📋 The Data")
        st.dataframe(df)
        
        st.write("### 📈 Visuals")
        st.bar_chart(df.set_index('Name'))
        
        st.write("### 🤖 AI Analysis")
        if st.button("Generate AI Report"):
            with st.spinner("Analyzing data trends..."):
                data_string = df.to_string()
                prompt = f"Analyze these student marks:\n{data_string}\n\n1. Identify top performer.\n2. Identify struggling students (below 50).\n3. Suggest 2 specific actions for the teacher."
                
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                )
                st.write(response.choices[0].message.content)

# ==========================================
# PAGE 5: YOUTUBE SUMMARIZER
# ==========================================
elif choice == "🎥 YouTube Summarizer":
    st.header("🎥 YouTube Video Summarizer")
    
    youtube_link = st.text_input("Paste a YouTube Link:")
    
    if st.button("Summarize Video"):
        if "youtube.com" in youtube_link or "youtu.be" in youtube_link:
            try:
                with st.spinner("🎧 Listening to the video..."):
                    # Extract Video ID logic
                    if "v=" in youtube_link:
                        video_id = youtube_link.split("v=")[1].split("&")[0]
                    elif "youtu.be" in youtube_link:
                        video_id = youtube_link.split("/")[-1]
                    
                    # Get Transcript
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    full_text = " ".join([d['text'] for d in transcript_list])
                    
                    # Send to AI
                    prompt = f"Summarize this video transcript in bullet points and give 3 key takeaways:\n\n{full_text[:12000]}"
                    
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192",
                    )
                    
                st.write("### 📝 Video Notes")
                st.write(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Error: Could not retrieve transcript. The video might not have captions enabled. (Error: {e})")
        else:
            st.warning("Please enter a valid YouTube link.")
  
