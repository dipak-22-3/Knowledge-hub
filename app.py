import streamlit as st
import os
import sqlite3
import pandas as pd
import requests
import base64
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from gtts import gTTS

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="KnowledgeOS", layout="wide", page_icon="🧠", initial_sidebar_state="expanded")
load_dotenv()

# Database Init
def init_db():
    conn = sqlite3.connect('knowledge_hub.db')
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

# --- 2. ADVANCED UI/UX (CSS & ANIMATIONS) ---
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# Load Animations
lottie_coding = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json")
lottie_robot = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_1LhsaB.json")

# Custom CSS for "Beautiful Product" Feel
st.markdown("""
    <style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif; 
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Modern Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4F8BF9;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
        font-weight: 500;
    }
    
    /* Custom Buttons */
    .stButton>button {
        border-radius: 50px;
        background: linear-gradient(90deg, #4F8BF9 0%, #00d2ff 100%);
        color: white;
        border: none;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(79, 139, 249, 0.4);
    }
    
    /* Chat Bubbles */
    .user-msg {
        background-color: #E3F2FD;
        padding: 15px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        text-align: right;
    }
    .bot-msg {
        background-color: #F5F5F5;
        padding: 15px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        border-left: 5px solid #4F8BF9;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    filename = "speech.mp3"
    tts.save(filename)
    return filename

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. NAVIGATION (SIDEBAR V2) ---
with st.sidebar:
    st_lottie(lottie_robot, height=150, key="robot_sidebar")
    selected = option_menu(
        menu_title="KnowledgeOS",
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["speedometer2", "chat-dots-fill", "journal-richtext", "youtube", "archive-fill"],
        menu_icon="cpu",
        default_index=0,
        styles={
            "container": {"padding": "5px!important", "background-color": "#fafafa"},
            "icon": {"color": "#4F8BF9", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#4F8BF9"},
        }
    )
    st.markdown("---")
    st.caption("v3.0.1 Ultimate Edition")

# --- 5. MAIN APPLICATION LOGIC ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.markdown("<h1 style='text-align: center;'>🚀 Welcome Back, Creator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Your AI-powered productivity Operating System</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Stats
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    
    # Dynamic Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Planner", 0)}</div><div class="metric-label">Lesson Plans</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("YouTube", 0)}</div><div class="metric-label">Video Summaries</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{stats.get("Chat", 0)}</div><div class="metric-label">Documents Read</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">Pro</div><div class="metric-label">Plan Status</div></div>', unsafe_allow_html=True)

    st.markdown("### 🔥 Quick Actions")
    col1, col2 = st.columns([2,1])
    with col1:
        st.info("💡 **Did you know?** You can now listen to your lesson plans using the Audio Player in Planner Pro.")
    with col2:
        st_lottie(lottie_coding, height=150)

# === SMART CHAT (RAG V2) ===
elif selected == "Smart Chat":
    st.header("🧠 Smart Document Chat")
    
    with st.expander("📂 Upload Configuration", expanded=True):
        uploaded_file = st.file_uploader("Upload PDF / Text File", type=["pdf", "txt"])
    
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    if uploaded_file:
        text = ""
        if uploaded_file.name.endswith(".pdf"):
            text = "".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
        else:
            text = uploaded_file.read().decode("utf-8")
            
        st.toast("Document Indexed Successfully!", icon="✅")
        
        # Chat Interface
        for msg in st.session_state.chat_history:
            st.markdown(f"<div class='{msg['type']}'>{msg['content']}</div>", unsafe_allow_html=True)
            
        prompt = st.chat_input("Ask anything about the doc...")
        if prompt:
            st.session_state.chat_history.append({"type": "user-msg", "content": prompt})
            st.markdown(f"<div class='user-msg'>{prompt}</div>", unsafe_allow_html=True)
            
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Context: {text[:20000]}"}, {"role": "user", "content": prompt}],
                    model=MODEL_NAME
                ).choices[0].message.content
                
                st.session_state.chat_history.append({"type": "bot-msg", "content": response})
                st.markdown(f"<div class='bot-msg'>{response}</div>", unsafe_allow_html=True)
                
                # Auto-save chat logs
                c = conn.cursor()
                c.execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Chat", "Chat Log", f"Q: {prompt} | A: {response}"))
                conn.commit()

# === PLANNER PRO (Tools Suite) ===
elif selected == "Planner Pro":
    st.header("📝 Planner Pro Suite")
    
    tab1, tab2, tab3 = st.tabs(["📘 Lesson Generator", "🧠 Mind Map", "✉️ Email Parent"])
    
    with tab1:
        c1, c2 = st.columns(2)
        topic = c1.text_input("Lesson Topic", placeholder="e.g. Photosynthesis")
        level = c2.select_slider("Complexity", options=["Easy", "Medium", "Hard", "Expert"])
        
        if st.button("Generate Plan ⚡"):
            with st.spinner("Architecting Lesson..."):
                plan = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create detailed lesson plan for '{topic}' level '{level}'. Use formatting."}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.session_state['gen_plan'] = plan
        
        if 'gen_plan' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['gen_plan'])
            
            # Tools Bar
            c_a, c_b, c_c = st.columns(3)
            with c_a:
                if st.button("🔊 Listen (Audio)"):
                    audio_file = text_to_speech(st.session_state['gen_plan'][:500]) # Limit for speed
                    st.audio(audio_file)
            with c_b:
                pdf_bytes = create_pdf(st.session_state['gen_plan'])
                st.download_button("📥 PDF Export", data=pdf_bytes, file_name="plan.pdf", mime='application/pdf')
            with c_c:
                if st.button("💾 Save to DB"):
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", topic, st.session_state['gen_plan']))
                    conn.commit()
                    st.toast("Saved!", icon="💾")

    with tab2:
        st.subheader("Visual Learning (Mermaid.js)")
        concept = st.text_input("Enter Concept to Visualize")
        if st.button("Generate Map"):
            prompt = f"Create a Mermaid.js flowchart code for '{concept}'. Return ONLY the code inside mermaid tags."
            code = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME).choices[0].message.content
            # Clean response logic would go here, simplified for demo:
            st.info("Copy this into a Mermaid viewer (Integration coming in v3.1)")
            st.code(code, language='mermaid')

    with tab3:
        st.subheader("Auto-Emailer")
        student_name = st.text_input("Student Name")
        feedback = st.text_area("Key Points (e.g. Good at math, talks too much)")
        if st.button("Draft Email"):
            email = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Write a polite email to parents of {student_name} mentioning: {feedback}"}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.text_area("Draft", email, height=200)

# === MEDIA STUDIO ===
elif selected == "Media Studio":
    st.header("🎥 Media & Quiz Studio")
    
    mode = st.radio("Select Mode", ["YouTube Summarizer", "Quiz Generator"], horizontal=True)
    
    if mode == "YouTube Summarizer":
        link = st.text_input("YouTube URL")
        if st.button("Analyze Video"):
            try:
                vid_id = link.split("v=")[1].split("&")[0] if "v=" in link else link.split("/")[-1]
                transcript = " ".join([d['text'] for d in YouTubeTranscriptApi.get_transcript(vid_id)])
                
                with st.spinner("Watching video..."):
                    summary = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"Summarize in bullet points:\n{transcript[:15000]}"}], 
                        model=MODEL_NAME
                    ).choices[0].message.content
                
                st.markdown("### 🎬 Summary")
                st.write(summary)
                
                # Save
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("YouTube", "Video Analysis", summary))
                conn.commit()
                
            except:
                st.error("Could not process video. Check if captions are enabled.")
                
    elif mode == "Quiz Generator":
        q_topic = st.text_input("Quiz Topic")
        if st.button("Create Quiz"):
            quiz = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Create 5 multiple choice questions on {q_topic} with answers at the end."}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.session_state['quiz_content'] = quiz
            
        if 'quiz_content' in st.session_state:
            with st.expander("Show Quiz", expanded=True):
                st.markdown(st.session_state['quiz_content'])
            if st.button("Reveal Answers"):
                st.info("Answers are at the bottom of the generated text above.")

# === MY LIBRARY ===
elif selected == "My Library":
    st.header("🗄️ Digital Archive")
    
    # Search Bar
    search = st.text_input("🔍 Search your history...", "")
    
    query = "SELECT id, tool, title, timestamp FROM history"
    if search:
        query += f" WHERE title LIKE '%{search}%'"
    query += " ORDER BY id DESC"
    
    df = pd.read_sql(query, conn)
    
    # Interactive Table
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date", format="D MMM, YYYY, h:mm a"),
            "tool": st.column_config.TextColumn("Type"),
        }
    )
    
    c1, c2 = st.columns([1, 3])
    with c1:
        oid = st.number_input("Open ID", min_value=1, step=1)
    with c2:
        if st.button("Open File"):
            data = conn.cursor().execute("SELECT content FROM history WHERE id=?", (oid,)).fetchone()
            if data:
                st.markdown("---")
                st.subheader("📄 File Content")
                st.markdown(data[0])
            else:
                st.error("File not found.")
    
