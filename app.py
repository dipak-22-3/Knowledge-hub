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
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="KnowledgeOS Pro", layout="wide", page_icon="⚡", initial_sidebar_state="expanded")
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
    st.error("🚨 Critical Error: API Key missing. Please check .env or Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODEL_NAME = "llama-3.3-70b-versatile"

# --- 3. UI/UX ASSETS ---
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
anim_video = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_khzniYA8.json")

# --- 4. ADVANCED CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    
    .gradient-text {
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4F8BF9, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        padding-bottom: 10px;
    }
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #4F8BF9; }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #2D3748; }
    .metric-label { font-size: 1rem; color: #718096; }
    .user-msg { background: #E3F2FD; padding: 12px 18px; border-radius: 18px 18px 4px 18px; margin-bottom: 12px; }
    .bot-msg { background: #FFFFFF; padding: 12px 18px; border-radius: 18px 18px 18px 4px; margin-bottom: 12px; border: 1px solid #E2E8F0; }
    [data-testid="stSidebar"] { background-color: #FAFAFA; border-right: 1px solid #EEEEEE; }
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
# --- PURANA CODE HATAEIN ---
# def render_mermaid(code):
#     html_code = f"""..."""
#     components.html(html_code...)

# --- NYA CODE LAGAYEIN (Graphviz Engine) ---
import graphviz

def render_mermaid(code):
    """
    Renders diagram using Streamlit's native Graphviz engine.
    Much more stable than injecting JS.
    """
    # Clean the code (remove Mermaid syntax to fit Graphviz if needed, 
    # but simplest is to ask AI for Graphviz DOT format directly)
    try:
        st.graphviz_chart(code)
    except Exception as e:
        st.error(f"Diagram Error: {e}")
        

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

# --- 6. SIDEBAR ---
with st.sidebar:
    safe_lottie(anim_welcome, 120, "logo_anim")
    st.markdown("### **KnowledgeOS**")
    st.caption("v5.2 Fixed Edition")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["grid-1x2", "chat-square-text", "journal-code", "play-circle", "folder2-open"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "icon": {"color": "#4F8BF9", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "margin":"5px"},
            "nav-link-selected": {"background-color": "#4F8BF9"},
        }
    )
    st.markdown("---")
    st.success("✅ System Online")

# --- 7. MAIN APPLICATION ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.markdown('<div class="gradient-text" style="text-align: center;">🚀 Command Center</div>', unsafe_allow_html=True)
    
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Planner", 0)}</div><div class="metric-label">Lesson Plans</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("YouTube", 0)}</div><div class="metric-label">Videos Processed</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Chat", 0)}</div><div class="metric-label">Chat Logs</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-value">PRO</div><div class="metric-label">Account Status</div></div>', unsafe_allow_html=True)

# === SMART CHAT ===
elif selected == "Smart Chat":
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown('<div class="gradient-text">🧠 Smart Chat</div>', unsafe_allow_html=True)
    with c2: safe_lottie(anim_chat, 80, "chat_anim")
    
    uploaded_file = st.file_uploader("Upload PDF / TXT", type=["pdf", "txt"])
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    if uploaded_file:
        text = ""
        if uploaded_file.name.endswith(".pdf"):
            text = "".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
        else:
            text = uploaded_file.read().decode("utf-8")
        st.toast("File Indexed!", icon="📂")
        
        for msg in st.session_state.chat_history:
            st.markdown(f'<div class="{msg["role"]}-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        
        prompt = st.chat_input("Ask about the document...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)
            with st.spinner("Thinking..."):
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
    with c1: st.markdown('<div class="gradient-text">📝 Planner Pro</div>', unsafe_allow_html=True)
    with c2: safe_lottie(anim_plan, 80, "plan_anim")
    
    tab1, tab2, tab3 = st.tabs(["📘 Lesson Generator", "🗺️ Mind Map", "✉️ Parent Comms"])
    
    with tab1:
        col1, col2 = st.columns(2)
        topic = col1.text_input("Topic", placeholder="e.g. Gravity")
        level = col2.select_slider("Level", options=["Basic", "Intermediate", "Advanced"])
        if st.button("Generate Plan ✨", type="primary"):
            with st.spinner("Generating..."):
                plan = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create lesson plan for '{topic}' ({level}). Format nicely."}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.session_state['gen_plan'] = plan
        if 'gen_plan' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['gen_plan'])
            c_a, c_b, c_c = st.columns(3)
            with c_a: 
                if st.button("💾 Save"):
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", topic, st.session_state['gen_plan']))
                    conn.commit()
                    st.toast("Saved!", icon="✅")
            with c_b:
                pdf_bytes = create_pdf(st.session_state['gen_plan'])
                st.download_button("📥 Download PDF", data=pdf_bytes, file_name="plan.pdf", mime='application/pdf')
            with c_c:
                if st.button("🔊 Listen"):
                    st.audio(text_to_speech(st.session_state['gen_plan'][:500]))

   with tab2:
        st.subheader("Visual Concept Mapper (Graphviz Engine)")
        concept = st.text_input("Concept to Visualize", placeholder="e.g. Photosynthesis")
        
        if st.button("Visualize 🧠"):
            with st.spinner("Drawing Chart..."):
                # CHANGE: Asking for DOT format instead of Mermaid
                prompt = f"""
                Create a Graphviz DOT language code for a mindmap about '{concept}'.
                RULES:
                1. Start with 'digraph G {{'.
                2. Use clean node labels.
                3. Do not use markdown backticks (```).
                4. Return ONLY the code.
                """
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME).choices[0].message.content
                
                # Cleanup code
                clean_code = res.replace("```dot", "").replace("```graphviz", "").replace("```", "").strip()
                
                # Render
                st.graphviz_chart(clean_code)
                

    with tab3:
        st.info("Draft professional emails to parents.")
        s_name = st.text_input("Student Name")
        s_msg = st.text_area("Key Points")
        if st.button("Draft Email"):
            email = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Write email for student {s_name}: {s_msg}"}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.code(email, language="markdown")

# === MEDIA STUDIO ===
elif selected == "Media Studio":
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown('<div class="gradient-text">🎥 Media Studio</div>', unsafe_allow_html=True)
    with c2: safe_lottie(anim_video, 80, "vid_anim")
    
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
                st.markdown(summary)
            except: st.error("No captions found for this video.")

# === MY LIBRARY ===
elif selected == "My Library":
    st.markdown('<div class="gradient-text">🗄️ My Library</div>', unsafe_allow_html=True)
    search = st.text_input("🔍 Search...")
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
                if data: st.markdown(f"---\n{data[0]}")
        with c3:
            if st.button("🗑️ Delete", type="primary"):
                conn.cursor().execute("DELETE FROM history WHERE id=?", (oid,))
                conn.commit()
                st.rerun()
    else:
        st.info("Library is empty.")
        
