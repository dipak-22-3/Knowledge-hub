import streamlit as st
import os
import sqlite3
import pandas as pd
import requests
import tempfile
import time
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from gtts import gTTS

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="KnowledgeOS V5", 
    layout="wide", 
    page_icon="🎓", 
    initial_sidebar_state="expanded"
)
load_dotenv()

# Database Init
def init_db():
    conn = sqlite3.connect('knowledge_hub.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, tool TEXT, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats 
                 (metric TEXT PRIMARY KEY, value INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# Initialize XP if not exists
c = conn.cursor()
c.execute("INSERT OR IGNORE INTO user_stats (metric, value) VALUES ('xp', 0)")
conn.commit()

# API Init
try:
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except:
    api_key = None

if not api_key:
    st.warning("⚠️ Running in Demo Mode (No API Key). Enter Key in .env to fix.")
    # Stop execution if needed, or handle gracefully
else:
    client = Groq(api_key=api_key)
    MODEL_NAME = "llama-3.3-70b-versatile"

# --- 2. CSS & UI FIXES (HIGH CONTRAST) ---
st.markdown("""
    <style>
    /* 1. Global Text Visibility Fix */
    body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #E0E0E0 !important; /* Off-white text for dark mode */
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 2. Sidebar Fix - Solid Background */
    [data-testid="stSidebar"] {
        background-color: #0E1117 !important; /* Dark Blue-Black */
        border-right: 1px solid #30363D;
    }
    
    /* 3. Main Background */
    .stApp {
        background-color: #161B22; /* Github Dark Theme */
    }
    
    /* 4. Input Fields Visibility */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        color: #FFFFFF !important;
        background-color: #0D1117 !important;
        border: 1px solid #30363D !important;
    }
    
    /* 5. Metrics Cards (High Contrast) */
    .stat-card {
        background-color: #21262D;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stat-value {
        font-size: 2rem; 
        font-weight: bold; 
        color: #58A6FF !important; /* Blue Accent */
    }
    .stat-label {
        font-size: 1rem; 
        color: #8B949E !important;
    }
    
    /* 6. Buttons */
    .stButton>button {
        background-color: #238636; /* Green Action Button */
        color: white !important;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2EA043;
    }
    
    /* 7. Chat Bubbles */
    .user-msg {
        background-color: #1F6FEB;
        color: white !important;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0;
        text-align: right;
        display: inline-block;
        float: right;
        clear: both;
    }
    .bot-msg {
        background-color: #30363D;
        color: white !important;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin: 5px 0;
        text-align: left;
        display: inline-block;
        float: left;
        clear: both;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def add_xp(points):
    """Gamification: Adds XP to user stats"""
    c = conn.cursor()
    c.execute("UPDATE user_stats SET value = value + ? WHERE metric = 'xp'", (points,))
    conn.commit()

def get_xp():
    c = conn.cursor()
    data = c.execute("SELECT value FROM user_stats WHERE metric = 'xp'").fetchone()
    return data[0] if data else 0

def get_level(xp):
    if xp < 100: return "Level 1: Novice"
    if xp < 500: return "Level 2: Apprentice"
    if xp < 1000: return "Level 3: Scholar"
    return "Level 4: Master"

def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_coding = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json")

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. SIDEBAR NAVIGATION ---
# Using Session State to handle navigation from Dashboard buttons
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

with st.sidebar:
    st.title("🎓 KnowledgeOS")
    
    # Navigation Menu
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Chat with Docs", "Lesson Planner", "Video Notes", "Library"],
        icons=["house", "chat", "book", "play-btn", "archive"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#58A6FF", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "color": "#E0E0E0"},
            "nav-link-selected": {"background-color": "#30363D"},
        }
    )
    
    # Sync Sidebar with Session State (if user clicked a button on dashboard)
    if st.session_state.page != selected and st.session_state.page != "Dashboard":
        # If the state changed via button, we respect that, otherwise we follow sidebar
        pass
    else:
        st.session_state.page = selected

    # XP Display Widget
    st.markdown("---")
    curr_xp = get_xp()
    st.caption(f"🏆 {get_level(curr_xp)}")
    st.progress(min((curr_xp % 500) / 500, 1.0))
    st.caption(f"XP: {curr_xp}")

# --- 5. MAIN LOGIC ---

# === DASHBOARD ===
if st.session_state.page == "Dashboard":
    st.markdown("## 🚀 Command Center")
    
    # Stats from DB
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    total_xp = get_xp()

    # 4-Column Layout with CLICKABLE ACTIONS
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{stats.get("Planner", 0)}</div><div class="stat-label">Lesson Plans</div></div>', unsafe_allow_html=True)
        # NAVIGATION BUTTON
        if st.button("📝 Create Plan"):
            st.session_state.page = "Lesson Planner"
            st.rerun()

    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{stats.get("YouTube", 0)}</div><div class="stat-label">Videos</div></div>', unsafe_allow_html=True)
        if st.button("🎥 Analyze Video"):
            st.session_state.page = "Video Notes"
            st.rerun()

    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{stats.get("Chat", 0)}</div><div class="stat-label">Docs</div></div>', unsafe_allow_html=True)
        if st.button("🤖 Chat PDF"):
            st.session_state.page = "Chat with Docs"
            st.rerun()

    with c4:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{total_xp}</div><div class="stat-label">Total XP</div></div>', unsafe_allow_html=True)
        st.button("🏆 View Rewards", disabled=True) # Placeholder

    st.markdown("---")
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.info("💡 **Tip:** Earn 50 XP for every Lesson Plan generated. Level up to unlock 'Master' status.")
    with col_r:
        if lottie_coding: st_lottie(lottie_coding, height=150)

# === CHAT WITH DOCS ===
elif st.session_state.page == "Chat with Docs":
    st.header("🤖 Chat with Documents")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if "doc_chat" not in st.session_state: st.session_state.doc_chat = []

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = "".join([p.extract_text() for p in reader.pages])
        st.success("PDF Ready!")

        # Chat History
        for msg in st.session_state.doc_chat:
            div_class = "user-msg" if msg['role'] == 'user' else "bot-msg"
            st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)

        prompt = st.chat_input("Ask about the PDF...")
        if prompt:
            st.session_state.doc_chat.append({"role": "user", "content": prompt})
            st.markdown(f"<div class='user-msg'>{prompt}</div>", unsafe_allow_html=True)
            
            with st.spinner("AI Thinking..."):
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Context: {text[:20000]}"}, {"role": "user", "content": prompt}],
                    model=MODEL_NAME
                ).choices[0].message.content
                
                st.session_state.doc_chat.append({"role": "assistant", "content": response})
                st.markdown(f"<div class='bot-msg'>{response}</div>", unsafe_allow_html=True)
                
                # Save & Add XP
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Chat", "Q&A", f"Q: {prompt} A: {response}"))
                conn.commit()

# === LESSON PLANNER ===
elif st.session_state.page == "Lesson Planner":
    st.header("📝 Lesson Blueprint")
    
    c1, c2 = st.columns(2)
    topic = c1.text_input("Topic")
    level = c2.select_slider("Level", ["Child", "Teen", "Adult"])
    
    if st.button("Generate Plan (+50 XP)"):
        with st.spinner("Designing..."):
            plan = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Create lesson plan for '{topic}' level '{level}'."}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.session_state['plan_res'] = plan
            
            # Save Logic
            conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", topic, plan))
            add_xp(50) # Gamification
            conn.commit()
            st.toast("Plan Saved! +50 XP", icon="🎉")

    if 'plan_res' in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state['plan_res'])
        st.download_button("📥 Download PDF", data=create_pdf(st.session_state['plan_res']), file_name="plan.pdf", mime='application/pdf')

# === VIDEO NOTES ===
elif st.session_state.page == "Video Notes":
    st.header("🎥 YouTube Analyzer")
    link = st.text_input("YouTube URL")
    
    if st.button("Analyze (+30 XP)"):
        try:
            vid_id = link.split("v=")[1].split("&")[0] if "v=" in link else link.split("/")[-1]
            transcript = " ".join([d['text'] for d in YouTubeTranscriptApi.get_transcript(vid_id)])
            
            with st.spinner("Watching..."):
                summary = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Summarize:\n{transcript[:15000]}"}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                
                st.markdown(summary)
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("YouTube", "Video Summary", summary))
                add_xp(30)
                conn.commit()
                st.toast("Summary Saved! +30 XP", icon="🎉")
        except:
            st.error("Error: Video has no captions or is restricted.")

# === LIBRARY ===
elif st.session_state.page == "Library":
    st.header("🗄️ Your Archive")
    
    # Search
    search = st.text_input("Search...")
    query = "SELECT id, tool, title, timestamp FROM history"
    if search: query += f" WHERE title LIKE '%{search}%'"
    query += " ORDER BY id DESC"
    
    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # View Record
    c1, c2 = st.columns([1,3])
    with c1: oid = st.number_input("Enter ID", min_value=1)
    with c2:
        if st.button("Open Record"):
            data = conn.cursor().execute("SELECT content FROM history WHERE id=?", (oid,)).fetchone()
            if data:
                st.markdown("---")
                st.info("Record Content:")
                st.markdown(data[0])
            else:
                st.error("Not found.")
    
