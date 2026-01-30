import streamlit as st
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

# --- 1. SETUP & DATABASE ---
load_dotenv()

# Database Connection
def init_db():
    conn = sqlite3.connect('knowledge_hub.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, tool TEXT, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

# API Configuration
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("🚨 Critical Error: API Key missing. Please set GROQ_API_KEY in .env or Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# *** UPDATED MODEL NAME HERE ***
MODEL_NAME = "llama-3.3-70b-versatile" 

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="Knowledge Hub Pro", layout="wide", page_icon="🎓")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .main-header {
        font-size: 2.5rem;
        color: #333;
        text-align: center;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🎓 Knowledge Hub")
    st.markdown("---")
    menu = st.radio("Navigate:", 
        ["🏠 Home", "🤖 Chat with Docs", "📝 AI Planner", "🎥 YouTube Notes", "💾 Saved History"])
    st.markdown("---")
    st.caption(f"Powered by {MODEL_NAME}")

# --- 4. APP LOGIC ---

# === HOME ===
if menu == "🏠 Home":
    st.markdown('<div class="main-header">Welcome to Knowledge Hub</div>', unsafe_allow_html=True)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1: st.info("📚 **RAG System**\n\nUpload books and chat.")
    with col2: st.success("📝 **AI Planner**\n\nCreate Lesson Plans.")
    with col3: st.warning("💾 **Database**\n\nSave your work.")

# === CHAT WITH DOCS ===
elif menu == "🤖 Chat with Docs":
    st.header("🤖 Chat with Documents")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        st.success("PDF Loaded!")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask something about the PDF..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"Answer based ONLY on this text: {text[:20000]}"},
                            {"role": "user", "content": prompt}
                        ],
                        model=MODEL_NAME, # Updated Model
                    )
                    response = chat_completion.choices[0].message.content
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"API Error: {e}")

# === AI PLANNER ===
elif menu == "📝 AI Planner":
    st.header("📝 AI Lesson Planner")
    
    col1, col2 = st.columns(2)
    topic = col1.text_input("Enter Topic")
    level = col2.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    
    if st.button("Generate Plan"):
        if topic:
            with st.spinner("Generating Plan..."):
                try:
                    prompt = f"Create a structured lesson plan for '{topic}' ({level})."
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=MODEL_NAME, # Updated Model
                    ).choices[0].message.content
                    
                    st.session_state['last_plan'] = response
                    st.session_state['last_topic'] = topic
                except Exception as e:
                    st.error(f"Error: {e}")

    if 'last_plan' in st.session_state:
        st.markdown("### Generated Plan")
        st.write(st.session_state['last_plan'])
        
        if st.button("💾 Save to Database"):
            c = conn.cursor()
            c.execute("INSERT INTO history (tool, title, content) VALUES (?, ?, ?)", 
                     ("Planner", st.session_state['last_topic'], st.session_state['last_plan']))
            conn.commit()
            st.toast("Saved successfully!", icon="✅")

# === YOUTUBE NOTES ===
elif menu == "🎥 YouTube Notes":
    st.header("🎥 YouTube Summarizer")
    link = st.text_input("Paste YouTube Link")
    
    if st.button("Summarize"):
        if "v=" in link or "youtu.be" in link:
            try:
                if "v=" in link: video_id = link.split("v=")[1].split("&")[0]
                else: video_id = link.split("/")[-1]
                
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                text = " ".join([d['text'] for d in transcript])
                
                prompt = f"Summarize this video:\n{text[:15000]}"
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=MODEL_NAME, # Updated Model
                ).choices[0].message.content
                
                st.markdown("### Summary")
                st.write(response)
                
            except Exception as e:
                st.error("Could not fetch video. Ensure it has captions.")

# === SAVED HISTORY ===
elif menu == "💾 Saved History":
    st.header("💾 Database Records")
    c = conn.cursor()
    c.execute("SELECT id, tool, title, timestamp FROM history ORDER BY id DESC")
    rows = c.fetchall()
    
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Tool", "Title", "Date"])
        st.dataframe(df, use_container_width=True)
        
        record_id = st.number_input("Enter ID to view details", min_value=1, step=1)
        if st.button("Load Details"):
            c.execute("SELECT content FROM history WHERE id=?", (record_id,))
            data = c.fetchone()
            if data:
                st.markdown("---")
                st.markdown(data[0])
            else:
                st.error("ID not found.")
    else:
        st.info("Database is empty.")
