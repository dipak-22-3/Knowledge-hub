import streamlit as st
import os
import sqlite3
import pandas as pd
import requests
import tempfile
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from gtts import gTTS

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="KnowledgeOS Pro", 
    layout="wide", 
    page_icon="🧠", 
    initial_sidebar_state="expanded" # Ensures sidebar is open by default
)
load_dotenv()

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('knowledge_hub.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, tool TEXT, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. API SETUP ---
try:
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except:
    api_key = None

if not api_key:
    st.error("🚨 Critical Error: API Key missing. Check .env or Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODEL_NAME = "llama-3.3-70b-versatile"

# --- 4. ASSETS & STYLING ---

def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# Animations
lottie_robot = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_1LhsaB.json")
lottie_analyzing = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_gja1z1ru.json")

# CSS: Clean, Light, Professional (No broken glass effects)
st.markdown("""
    <style>
    /* Main Background - Clean White/Light Blue */
    .stApp {
        background-color: #F0F2F6;
    }
    
    /* Card Style for Stats */
    .stat-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #4F8BF9;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #333;
    }
    .stat-label {
        color: #666;
        font-size: 1rem;
    }
    
    /* Button Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
    
    /* Sidebar Text Color Fix */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def text_to_speech(text):
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts = gTTS(text=text, lang='en')
    tts.save(tfile.name)
    return tfile.name

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 6. SIDEBAR NAVIGATION (FIXED) ---
with st.sidebar:
    if lottie_robot:
        st_lottie(lottie_robot, height=150, key="sidebar_anim")
    
    st.title("KnowledgeOS")
    st.caption("v3.5 Stable Edition")
    
    # Navigation Menu - High Contrast
    selected = option_menu(
        menu_title="Main Menu",
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["house", "chat-text", "journal-text", "youtube", "folder"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#ffffff"},
            "icon": {"color": "#4F8BF9", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "color": "#222222"}, # Dark Text
            "nav-link-selected": {"background-color": "#E3F2FD", "color": "#4F8BF9"}, # Light Blue Active
        }
    )
    
    st.markdown("---")
    if st.button("🔄 Refresh System"):
        st.rerun()

# --- 7. MAIN PAGES ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.title("🚀 Command Center")
    st.markdown("Overview of your AI activity.")
    
    # Real-time Stats Query
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    data = dict(c.fetchall())
    
    total_files = sum(data.values())
    
    # Display Stats in Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{total_files}</div><div class="stat-label">Total Items</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{data.get("Planner", 0)}</div><div class="stat-label">Lesson Plans</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{data.get("YouTube", 0)}</div><div class="stat-label">Videos</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{data.get("Chat", 0)}</div><div class="stat-label">Chat Logs</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("💡 What would you like to do?")
    c1, c2 = st.columns(2)
    with c1:
        st.info("To create a new **Lesson Plan**, go to 'Planner Pro' in the sidebar.")
    with c2:
        st.success("To review past work, check 'My Library'. You can now delete old files!")

# === SMART CHAT ===
elif selected == "Smart Chat":
    st.header("🧠 Document Chat")
    
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = "".join([p.extract_text() for p in reader.pages])
        st.success("PDF Loaded Successfully!")
        
        # Chat History
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Input
        if prompt := st.chat_input("Ask a question..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.spinner("Analyzing..."):
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Context: {text[:20000]}"}, {"role": "user", "content": prompt}],
                    model=MODEL_NAME
                ).choices[0].message.content
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"): st.markdown(response)
                
                # Auto-save
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Chat", "Chat Log", f"Q: {prompt}\nA: {response}"))
                conn.commit()

# === PLANNER PRO ===
elif selected == "Planner Pro":
    st.header("📝 Lesson Planner")
    
    c1, c2 = st.columns([3, 1])
    with c1: topic = st.text_input("Topic", placeholder="Ex: Newton's Laws")
    with c2: level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    
    if st.button("Generate Plan ✨", type="primary"):
        with st.spinner("Generating..."):
            if lottie_analyzing: st_lottie(lottie_analyzing, height=100)
            
            plan = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Create a structured lesson plan for '{topic}' ({level})."}],
                model=MODEL_NAME
            ).choices[0].message.content
            
            st.session_state['gen_plan'] = plan
            st.session_state['gen_topic'] = topic

    if 'gen_plan' in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state['gen_plan'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save to Library"):
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", st.session_state['gen_topic'], st.session_state['gen_plan']))
                conn.commit()
                st.toast("Saved Successfully!", icon="✅")
                st.rerun() # Refresh stats immediately
        with col2:
            pdf_bytes = create_pdf(st.session_state['gen_plan'])
            st.download_button("📥 Download PDF", data=pdf_bytes, file_name=f"{st.session_state['gen_topic']}.pdf", mime='application/pdf')
        with col3:
            if st.button("🔊 Listen"):
                audio_file = text_to_speech(st.session_state['gen_plan'][:500])
                st.audio(audio_file)

# === MEDIA STUDIO ===
elif selected == "Media Studio":
    st.header("🎥 YouTube Summarizer")
    link = st.text_input("Paste YouTube Link")
    
    if st.button("Summarize"):
        try:
            video_id = link.split("v=")[1].split("&")[0] if "v=" in link else link.split("/")[-1]
            transcript = " ".join([d['text'] for d in YouTubeTranscriptApi.get_transcript(video_id)])
            
            with st.spinner("Summarizing..."):
                summary = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Summarize this:\n{transcript[:15000]}"}],
                    model=MODEL_NAME
                ).choices[0].message.content
            
            st.markdown("### Summary")
            st.markdown(summary)
            
            if st.button("💾 Save Summary"):
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("YouTube", "Video Summary", summary))
                conn.commit()
                st.toast("Saved!", icon="✅")
                st.rerun()
                
        except Exception as e:
            st.error("Error: Video likely has no captions.")

# === MY LIBRARY (IMPROVED) ===
elif selected == "My Library":
    st.header("🗄️ My Library")
    
    # Proactive Feature: Search
    search_query = st.text_input("🔍 Search files...", "")
    
    query = "SELECT id, tool, title, timestamp FROM history"
    params = []
    if search_query:
        query += " WHERE title LIKE ?"
        params.append(f"%{search_query}%")
    query += " ORDER BY id DESC"
    
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Tool", "Title", "Date"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("### Actions")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            selected_id = st.number_input("Enter ID:", min_value=0, step=1)
        with c2:
            if st.button("📂 Open"):
                data = c.execute("SELECT content FROM history WHERE id=?", (selected_id,)).fetchone()
                if data:
                    st.markdown("---")
                    st.markdown(data[0])
                else:
                    st.error("ID not found.")
        with c3:
            # Proactive Feature: DELETE
            if st.button("🗑️ Delete File", type="primary"):
                c.execute("DELETE FROM history WHERE id=?", (selected_id,))
                conn.commit()
                st.success(f"File ID {selected_id} deleted.")
                st.rerun()
    else:
        st.info("Library is empty. Go generate something!")
                                   
