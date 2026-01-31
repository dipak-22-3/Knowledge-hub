import streamlit as st
import os
import sqlite3
import pandas as pd
import requests
import base64
import tempfile
import streamlit.components.v1 as components
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from gtts import gTTS

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="KnowledgeOS Ultra", layout="wide", page_icon="🌌", initial_sidebar_state="expanded")
load_dotenv()

# Database Init
def init_db():
    conn = sqlite3.connect('knowledge_hub.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, tool TEXT, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

# API Init
try:
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except:
    api_key = None

if not api_key:
    st.error("🚨 Critical Error: API Key missing.")
    st.stop()

client = Groq(api_key=api_key)
MODEL_NAME = "llama-3.3-70b-versatile"

# --- 2. JAVASCRIPT INJECTIONS (ANIMATIONS) ---

def js_confetti_success():
    """Injects JS to trigger a confetti explosion"""
    components.html("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script>
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 }
        });
    </script>
    """, height=0, width=0)

# --- 3. ADVANCED CSS (COLORFUL & GLASSMORPHISM) ---
st.markdown("""
    <style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif; 
    }

    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Hide default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
        color: white;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.4);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #FFFFFF;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .metric-label {
        font-size: 1rem;
        color: #EEE;
        font-weight: 500;
    }
    
    /* Neon Buttons */
    .stButton>button {
        border-radius: 50px;
        background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%);
        color: white;
        border: none;
        font-weight: 600;
        padding: 0.5rem 2rem;
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(255, 75, 43, 0.6);
        color: white;
    }
    
    /* Modern Chat Bubbles */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        text-align: right;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .bot-msg {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        color: #333;
        padding: 15px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        border-left: 5px solid #764ba2;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Titles */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    p, label, span {
        color: #f0f0f0 !important;
    }
    /* Fix input text color */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        color: #333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS (BUG FIXES INCLUDED) ---
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# Load Lottie animations
lottie_robot = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_1LhsaB.json")
lottie_success = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_lk80fpsm.json")

def text_to_speech(text):
    # FIX: Use tempfile to avoid file conflicts and cleanup issues
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts = gTTS(text=text, lang='en')
    tts.save(tfile.name)
    return tfile.name

def create_pdf(text):
    # FIX: Basic error handling for encoding issues in FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    try:
        # Attempt latin-1 encoding, replace errors if necessary
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
    except Exception as e:
        pdf.multi_cell(0, 10, f"Error rendering text due to unsupported characters: {e}")
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 5. NAVIGATION SIDEBAR ---
with st.sidebar:
    st_lottie(lottie_robot, height=180, key="robot_sidebar")
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["speedometer2", "chat-dots-fill", "journal-richtext", "youtube", "archive-fill"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "white", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "color": "white", "--hover-color": "rgba(255,255,255,0.2)"},
            "nav-link-selected": {"background-color": "rgba(255,255,255,0.3)", "backdrop-filter": "blur(10px)"},
        }
    )
    st.markdown("---")
    st.caption("🌌 KnowledgeOS Ultra v4.0")

# --- 6. MAIN APPLICATION LOGIC ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.markdown("<h1 style='text-align: center; font-size: 4rem;'>🌌 KnowledgeOS Ultra</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Your Intelligent Command Center</p>", unsafe_allow_html=True)
    
    # Stats fetch
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    
    st.markdown("### 📊 System Metrics")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Planner", 0)}</div><div class="metric-label">Blueprints Created</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("YouTube", 0)}</div><div class="metric-label">Data Streams Analyzed</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Chat", 0)}</div><div class="metric-label">Neural Interactions</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">ONLINE</div><div class="metric-label">AI Status</div></div>', unsafe_allow_html=True)

# === SMART CHAT ===
elif selected == "Smart Chat":
    st.header("🧠 Neural Document Link")
    
    with st.expander("📂 Index New Document", expanded=True):
        uploaded_file = st.file_uploader("Drop PDF/TXT Data Source", type=["pdf", "txt"])
    
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    if uploaded_file:
        text = ""
        if uploaded_file.name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            text = "".join([p.extract_text() for p in reader.pages])
        else:
            text = uploaded_file.read().decode("utf-8")
        st.toast("Data Source Indexed.", icon="💠")
        
        # Chat Display
        for msg in st.session_state.chat_history:
            st.markdown(f"<div class='{msg['type']}'>{msg['content']}</div>", unsafe_allow_html=True)
            
        prompt = st.chat_input("Query the data source...")
        if prompt:
            st.session_state.chat_history.append({"type": "user-msg", "content": prompt})
            st.markdown(f"<div class='user-msg'>{prompt}</div>", unsafe_allow_html=True)
            
            with st.spinner("Processing Query..."):
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Context: {text[:25000]}"}, {"role": "user", "content": prompt}],
                    model=MODEL_NAME
                ).choices[0].message.content
                
                st.session_state.chat_history.append({"type": "bot-msg", "content": response})
                st.markdown(f"<div class='bot-msg'>{response}</div>", unsafe_allow_html=True)
                
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Chat", "Chat Log", f"Q: {prompt} | A: {response}"))
                conn.commit()

# === PLANNER PRO ===
elif selected == "Planner Pro":
    st.header("📝 Instructional Design Suite")
    
    tab1, tab2, tab3 = st.tabs(["📘 Blueprint Gen", "🧠 Concept Map", "✉️ Comms Link"])
    
    with tab1:
        c1, c2 = st.columns(2)
        topic = c1.text_input("Subject Vector", placeholder="e.g. Quantum Physics")
        level = c2.select_slider("Cognitive Load", options=["Novice", "Apprentice", "Practitioner", "Expert"])
        
        if st.button("Initiate Sequence ⚡"):
            with st.spinner("Architecting Blueprint..."):
                plan = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create detailed lesson plan for '{topic}' level '{level}'. Use clear headings and markdown formatting."}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.session_state['gen_plan'] = plan
        
        if 'gen_plan' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['gen_plan'])
            
            c_a, c_b, c_c = st.columns(3)
            with c_a:
                if st.button("🔊 Audio Synthesis"):
                    audio_file = text_to_speech(st.session_state['gen_plan'][:600])
                    st.audio(audio_file, format="audio/mp3")
            with c_b:
                pdf_bytes = create_pdf(st.session_state['gen_plan'])
                st.download_button("📥 Export PDF Data", data=pdf_bytes, file_name="blueprint.pdf", mime='application/pdf')
            with c_c:
                if st.button("💾 Commit to Database"):
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", topic, st.session_state['gen_plan']))
                    conn.commit()
                    # INJECT JS CONFETTI ON SAVE
                    js_confetti_success()
                    st.toast("Blueprint Committed!", icon="💠")

    with tab2:
        st.subheader("Visual Cortex (Mermaid.js)")
        concept = st.text_input("Enter concept vector for visualization")
        if st.button("Render Map 🗺️"):
            with st.spinner("Rendering..."):
                # FIX: Request specific simple markdown format for Mermaid
                prompt = f"Create a simple Mermaid JS mindmap for '{concept}'. Surround the code ONLY with ```mermaid and ``` tags."
                response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME).choices[0].message.content
                
                # Extract code between tags
                try:
                    mermaid_code = response.split("```mermaid")[1].split("```")[0].strip()
                    st.markdown(f"```mermaid\n{mermaid_code}\n```", unsafe_allow_html=True)
                except:
                    st.error("AI generation failed to produce valid Mermaid code. Try a simpler concept.")

    with tab3:
        st.subheader("External Comms Link")
        student_name = st.text_input("Target Recipient")
        feedback = st.text_area("Key Data Points")
        if st.button("Draft Transmission"):
            email = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Write professional email regarding student {student_name}. Points: {feedback}"}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.markdown("### Draft Transmission")
            st.code(email, language='plaintext')

# === MEDIA STUDIO ===
elif selected == "Media Studio":
    st.header("🎥 Media Analysis Processor")
    link = st.text_input("Input YouTube Data Stream URL")
    if st.button("Analyze Stream 🎬"):
        try:
            vid_id = link.split("v=")[1].split("&")[0] if "v=" in link else link.split("/")[-1]
            transcript = " ".join([d['text'] for d in YouTubeTranscriptApi.get_transcript(vid_id)])
            
            with st.spinner("Processing data stream..."):
                summary = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create structured summary with key takeaways:\n{transcript[:20000]}"}], 
                    model=MODEL_NAME
                ).choices[0].message.content
            
            st.markdown("### 💠 Analysis Output")
            st.markdown(summary)
            
            if st.button("💾 Commit Analysis"):
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("YouTube", "Video Analysis", summary))
                conn.commit()
                js_confetti_success()
                st.toast("Analysis Committed.", icon="✅")
                
        except Exception as e:
            st.error(f"Data Stream Error. Ensure captions exist. ({e})")

# === MY LIBRARY ===
elif selected == "My Library":
    st.header("🗄️ Deep Storage Archive")
    search = st.text_input("🔍 Query Archive Index...", "")
    query = "SELECT id, tool, title, timestamp FROM history"
    if search: query += f" WHERE title LIKE '%{search}%'"
    query += " ORDER BY id DESC"
    
    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"timestamp": st.column_config.DatetimeColumn("Time Log", format="D MMM YYYY, h:mm a")})
    
    c1, c2 = st.columns([1, 3])
    with c1: oid = st.number_input("Select Data ID", min_value=1, step=1)
    with c2:
        if st.button("Retrieve Data Record"):
            data = conn.cursor().execute("SELECT content FROM history WHERE id=?", (oid,)).fetchone()
            if data:
                st.markdown("---")
                st.markdown(data[0])
            else:
                st.error("Record not found in Deep Storage.")
                
