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

# Animations (Professional & Minimal)
anim_welcome = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_1LhsaB.json")
anim_chat = load_lottieurl("https://lottie.host/embed/9307c844-3253-4809-9139-44520775d718/animation.json")
anim_plan = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_w51pcehl.json")

# --- 4. HIGH CONTRAST CSS (Fixed Readability) ---
st.markdown("""
    <style>
    /* Import Font: Inter (Standard for UI) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #171717; /* Almost Black for readability */
    }

    /* Main Background */
    .stApp {
        background-color: #F4F6F9; /* Soft Blue-Grey - Very Easy on Eyes */
    }

    /* Headers */
    h1, h2, h3 {
        color: #111827 !important;
        font-weight: 700 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }

    /* Cards - White with Soft Shadow */
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #E5E7EB;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #3B82F6;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1F2937;
    }
    .metric-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Chat Bubbles - High Contrast */
    .user-msg {
        background-color: #3B82F6; /* Professional Blue */
        color: white;
        padding: 12px 16px;
        border-radius: 12px 12px 0 12px;
        margin-bottom: 10px;
        font-weight: 500;
    }
    .bot-msg {
        background-color: #FFFFFF;
        color: #1F2937; /* Dark Grey */
        padding: 12px 16px;
        border-radius: 12px 12px 12px 0;
        margin-bottom: 10px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* Buttons */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        height: 45px;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    /* Inputs */
    .stTextInput input {
        background-color: #FFFFFF;
        color: #111827;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
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

# --- 6. SIDEBAR ---
with st.sidebar:
    safe_lottie(anim_welcome, 120, "logo_anim")
    st.markdown("### **KnowledgeOS**")
    st.caption("v7.0 Professional")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["grid-fill", "chat-dots-fill", "journal-text", "play-circle-fill", "folder-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "icon": {"color": #2563EB, "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "color": "#374151", "margin": "5px"},
            "nav-link-selected": {"background-color": "#EFF6FF", "color": "#2563EB", "font-weight": "600"},
        }
    )
    st.markdown("---")

# --- 7. MAIN APPLICATION ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.title("🚀 Command Center")
    st.markdown("Welcome back. Here is your system status.")
    
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Planner", 0)}</div><div class="metric-label">Lesson Plans</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("YouTube", 0)}</div><div class="metric-label">Videos</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Chat", 0)}</div><div class="metric-label">Chat Logs</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-value">PRO</div><div class="metric-label">Status</div></div>', unsafe_allow_html=True)

# === SMART CHAT (HANDWRITTEN CHECK ADDED) ===
elif selected == "Smart Chat":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("🧠 Smart Document Chat")
    with c2: safe_lottie(anim_chat, 100, "chat_anim")
    
    st.info("ℹ️ Note: Works best with digital PDFs. Scanned images/handwriting may not be detected.")
    
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
        
        # HANDWRITTEN/EMPTY CHECK
        if len(text.strip()) < 10:
            st.error("⚠️ No text detected! This seems to be a scanned image or handwritten note.")
            st.warning("Current tech (PyPDF) cannot read pixels. Please convert your image to text using an OCR tool first, or upload a digital PDF.")
        else:
            st.toast("Document Indexed!", icon="✅")
            
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
    with c2: safe_lottie(anim_plan, 100, "plan_anim")
    
    tab1, tab2, tab3 = st.tabs(["📘 Generator", "🗺️ Mind Map", "✉️ Emailer"])
    
    with tab1:
        c1, c2 = st.columns(2)
        topic = c1.text_input("Topic", placeholder="e.g. Gravity")
        level = c2.select_slider("Level", options=["Basic", "Intermediate", "Advanced"])
        
        if st.button("Generate Plan ✨", type="primary"):
            with st.spinner("Drafting..."):
                plan = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create lesson plan for '{topic}' ({level}). Format with clear Markdown."}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.session_state['gen_plan'] = plan
        
        if 'gen_plan' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['gen_plan'])
            c_a, c_b, c_c = st.columns(3)
            with c_a: 
                if st.button("💾 Save to Library"):
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
        st.subheader("Visual Concept Mapper (Graphviz)")
        concept = st.text_input("Concept to Visualize")
        
        if st.button("Visualize 🧠"):
            with st.spinner("Drawing..."):
                prompt = f"Create a Graphviz DOT code for a mindmap about '{concept}'. Return ONLY the code inside ```dot``` blocks."
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME).choices[0].message.content
                clean_code = res.replace("```dot", "").replace("```graphviz", "").replace("```", "").strip()
                try:
                    st.graphviz_chart(clean_code)
                except Exception as e:
                    st.error(f"Error: {e}")

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
                st.markdown(summary)
            except: st.error("No captions found or invalid video.")

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
                if data: st.markdown(f"---\n{data[0]}")
        with c3:
            if st.button("🗑️ Delete", type="primary"):
                conn.cursor().execute("DELETE FROM history WHERE id=?", (oid,))
                conn.commit()
                st.rerun()
    else:
        st.info("No files found.")
