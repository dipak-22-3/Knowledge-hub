import streamlit as st
import os
import sqlite3
import pandas as pd
import requests
import base64
import streamlit.components.v1 as components
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from gtts import gTTS
import graphviz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="KnowledgeOS Pro", layout="wide", page_icon="🎓", initial_sidebar_state="expanded")
load_dotenv()

# --- 2. DATABASE & API ---
def init_db():
    conn = sqlite3.connect('knowledge_hub.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, tool TEXT, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

try:
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except:
    api_key = None

if not api_key:
    st.error("🚨 Critical Error: API Key missing. Check .env or Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODEL_NAME = "llama-3.3-70b-versatile"

# --- 3. UI ASSETS ---
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code != 200: return None
        return r.json()
    except: return None

def safe_lottie(anim_data, height, key):
    if anim_data:
        st_lottie(anim_data, height=height, key=key)
    else:
        st.write("")

# Animations
anim_welcome = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_1LhsaB.json")
anim_chat = load_lottieurl("https://lottie.host/embed/9307c844-3253-4809-9139-44520775d718/animation.json")
anim_plan = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_w51pcehl.json")

# --- 4. CUSTOM CSS (BLUE THEME + WHITE BOARD + BIG BLACK FONT) ---
st.markdown("""
    <style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* 1. SIDEBAR - Deep Royal Blue */
    [data-testid="stSidebar"] {
        background-color: #0A2647 !important; /* Deep Blue */
        border-right: 2px solid #000000;
    }
    
    /* Sidebar Text - White for Visibility */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }

    /* 2. MAIN APP - White Board Look */
    .stApp {
        background-color: #FFFFFF !important; /* Pure White */
        color: #000000 !important;
    }

    /* 3. GENERATED TEXT - Black, Bold, Size 22px (AS REQUESTED) */
    .stMarkdown p, .stMarkdown li, .bot-msg {
        font-size: 22px !important;
        font-weight: 700 !important; /* Bold */
        color: #000000 !important; /* Pure Black */
        line-height: 1.6 !important;
    }

    /* Headers (Titles) - Blue */
    h1, h2, h3 {
        color: #144272 !important; /* Medium Blue */
        font-weight: 900 !important;
    }

    /* 4. CARDS */
    .metric-card {
        background: #F1F6F9; /* Very Light Blue Grey */
        border: 2px solid #144272;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 5px 5px 0px rgba(20, 66, 114, 0.2);
    }
    .metric-value {
        font-size: 3rem !important;
        color: #144272 !important;
        font-weight: bold;
    }

    /* 5. INPUT FIELDS - High Visibility */
    .stTextInput input, .stTextArea textarea {
        background-color: #F8F9FA !important;
        color: #000000 !important;
        border: 2px solid #144272 !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }

    /* 6. BUTTONS */
    .stButton>button {
        background-color: #2C74B3 !important; /* Blue Button */
        color: white !important;
        font-size: 20px !important;
        border-radius: 10px;
        height: 50px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #205295 !important; /* Darker Blue on Hover */
    }

    /* 7. CHAT BUBBLES */
    .user-msg {
        background-color: #2C74B3;
        color: white !important;
        padding: 15px;
        border-radius: 15px;
        font-size: 20px !important;
        margin-bottom: 15px;
    }
    .bot-msg {
        background-color: #F1F6F9;
        color: #000000 !important;
        padding: 15px;
        border: 2px solid #144272;
        border-radius: 15px;
        font-size: 22px !important; /* Size 22 for AI response */
        font-weight: 700 !important;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def text_to_speech(text):
    import tempfile
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

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    safe_lottie(anim_welcome, 150, "logo_anim")
    st.markdown("<h1 style='text-align: center; color: white;'>KnowledgeOS</h1>", unsafe_allow_html=True)
    
    # Option Menu with Custom Styles for Dark Sidebar
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["grid-fill", "chat-dots-fill", "journal-text", "play-circle-fill", "folder-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "icon": {"color": "#ffffff", "font-size": "20px"}, 
            "nav-link": {"font-size": "18px", "color": "#ffffff", "margin": "10px", "text-align": "left"},
            "nav-link-selected": {"background-color": "#2C74B3", "color": "white", "font-weight": "bold"},
        }
    )
    st.markdown("---")

# --- 7. MAIN APPLICATION ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.title("🚀 Command Center")
    
    
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Planner", 0)}</div><div class="metric-label">Lesson Plans</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("YouTube", 0)}</div><div class="metric-label">Videos</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Chat", 0)}</div><div class="metric-label">Chat Logs</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-value">PRO</div><div class="metric-label">Status</div></div>', unsafe_allow_html=True)

# === SMART CHAT ===
elif selected == "Smart Chat":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("🧠 Smart Chat")
    with c2: safe_lottie(anim_chat, 120, "chat_anim")
    
    uploaded_file = st.file_uploader("Upload PDF / TXT", type=["pdf", "txt"])
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    if uploaded_file:
        text = ""
        if uploaded_file.name.endswith(".pdf"):
            try:
                text = "".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
            except: text = ""
        else:
            text = uploaded_file.read().decode("utf-8")
        
        if len(text.strip()) < 10:
            st.error("⚠️ No text detected! This looks like an image or handwritten note.")
        else:
            st.success("Document Ready!")
            
            for msg in st.session_state.chat_history:
                role_class = "user-msg" if msg["role"] == "user" else "bot-msg"
                st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
            
            prompt = st.chat_input("Ask a question...")
            if prompt:
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)
                
                with st.spinner("Analyzing..."):
                    response = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Context: {text[:20000]}"}, {"role": "user", "content": prompt}],
                        model=MODEL_NAME
                    ).choices[0].message.content
                    
                    st.session_state.chat_history.append({"role": "bot", "content": response})
                    st.markdown(f'<div class="bot-msg">{response}</div>', unsafe_allow_html=True)
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Chat", "Chat Log", f"Q: {prompt}\nA: {response}"))
                    conn.commit()

# === PLANNER PRO ===
elif selected == "Planner Pro":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("📝 Planner Pro")
    with c2: safe_lottie(anim_plan, 120, "plan_anim")
    
    tab1, tab2, tab3 = st.tabs(["📘 Generator", "🗺️ Mind Map", "✉️ Emailer"])
    
    with tab1:
        c1, c2 = st.columns(2)
        topic = c1.text_input("Topic", placeholder="e.g. Gravity")
        level = c2.select_slider("Level", options=["Basic", "Intermediate", "Advanced"])
        
        if st.button("Generate Plan ✨", type="primary"):
            with st.spinner("Drafting..."):
                plan = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create lesson plan for '{topic}' ({level}). Format nicely."}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.session_state['gen_plan'] = plan
        
        if 'gen_plan' in st.session_state:
            st.markdown("---")
            # Applying specific class for size 22
            st.markdown(f'<div class="bot-msg">{st.session_state["gen_plan"]}</div>', unsafe_allow_html=True)
            
            c_a, c_b, c_c = st.columns(3)
            with c_a: 
                if st.button("💾 Save"):
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", topic, st.session_state['gen_plan']))
                    conn.commit()
                    st.success("Saved!")
            with c_b:
                pdf_bytes = create_pdf(st.session_state['gen_plan'])
                st.download_button("📥 Download PDF", data=pdf_bytes, file_name="plan.pdf", mime='application/pdf')
            with c_c:
                if st.button("🔊 Listen"):
                    st.audio(text_to_speech(st.session_state['gen_plan'][:500]))

    with tab2:
        st.subheader("Visual Concept Mapper")
        
        concept = st.text_input("Concept to Visualize")
        
        if st.button("Visualize 🧠"):
            with st.spinner("Drawing..."):
                prompt = f"Create a Graphviz DOT code for a mindmap about '{concept}'. Return ONLY code in ```dot```."
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME).choices[0].message.content
                clean_code = res.replace("```dot", "").replace("```graphviz", "").replace("```", "").strip()
                try:
                    st.graphviz_chart(clean_code)
                except: st.error("Error creating chart.")

    with tab3:
        st.subheader("Parent Communication")
        s_name = st.text_input("Student Name")
        s_msg = st.text_area("Observation")
        if st.button("Draft Email"):
            email = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Write email for student {s_name}: {s_msg}"}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.code(email, language="markdown")

# === MEDIA STUDIO ===
elif selected == "Media Studio":
    st.title("🎥 Media Studio")
    link = st.text_input("YouTube URL")
    
    if st.button("Summarize"):
        if "v=" in link or "youtu.be" in link:
            try:
                vid_id = link.split("v=")[1].split("&")[0] if "v=" in link else link.split("/")[-1]
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(vid_id)
                except:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(vid_id).find_generated_transcript(['en']).fetch()
                
                text = " ".join([d['text'] for d in transcript_list])
                summary = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Summarize:\n{text[:15000]}"}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.markdown(f'<div class="bot-msg">{summary}</div>', unsafe_allow_html=True)
            except: st.error("No captions found.")

# === MY LIBRARY ===
elif selected == "My Library":
    st.title("🗄️ My Library")
    search = st.text_input("🔍 Search Files...")
    
    query = "SELECT id, tool, title, timestamp FROM history"
    if search: query += f" WHERE title LIKE '%{search}%'"
    query += " ORDER BY id DESC"
    
    df = pd.read_sql(query, conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns([1,1,2])
        with c1: oid = st.number_input("ID", min_value=0)
        with c2: 
            if st.button("📂 Open"):
                data = conn.cursor().execute("SELECT content FROM history WHERE id=?", (oid,)).fetchone()
                if data: st.markdown(f'<div class="bot-msg">{data[0]}</div>', unsafe_allow_html=True)
        with c3:
            if st.button("🗑️ Delete", type="primary"):
                conn.cursor().execute("DELETE FROM history WHERE id=?", (oid,))
                conn.commit()
                st.experimental_rerun()
    else:
        st.info("No files found.")
    
