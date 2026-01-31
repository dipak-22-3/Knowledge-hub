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

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="KnowledgeOS Pro", layout="wide", page_icon="🧠", initial_sidebar_state="expanded")
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
    st.error("🚨 Critical Error: API Key missing. Please check .env or Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODEL_NAME = "llama-3.3-70b-versatile"

# --- 2. ANIMATIONS & ASSETS ---
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# Load Animations (Stored in variables for reuse)
anim_welcome = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_1LhsaB.json") # Robot
anim_chat = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_zprb9hfi.json") # Chat
anim_plan = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_w51pcehl.json") # Documents
anim_video = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_khzniYA8.json") # Video
anim_loading = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_p8bfn5to.json") # Loading

# --- 3. CUSTOM CSS (THE "DOOR OPENING" ANIMATION) ---
st.markdown("""
    <style>
    /* 1. Global Animation: Fade In Up (Like a door opening) */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translate3d(0, 40px, 0); }
        to { opacity: 1; transform: translate3d(0, 0, 0); }
    }
    
    .stMarkdown, .stButton, .stTextInput, .stDataFrame {
        animation-duration: 0.8s;
        animation-fill-mode: both;
        animation-name: fadeInUp;
    }

    /* 2. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }

    /* 3. Card Styling (Glass-like but safe) */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-bottom: 4px solid #4F8BF9;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* 4. Chat Bubbles */
    .user-msg { background-color: #E3F2FD; padding: 10px 15px; border-radius: 15px 15px 0 15px; text-align: right; margin-bottom: 10px; }
    .bot-msg { background-color: #F1F3F4; padding: 10px 15px; border-radius: 15px 15px 15px 0; text-align: left; margin-bottom: 10px; }
    
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---

def render_mermaid(code):
    """Renders Mermaid.js diagrams using HTML injection"""
    html_code = f"""
    <div class="mermaid" style="text-align: center;">
    {code}
    </div>
    <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true }});
    </script>
    """
    components.html(html_code, height=400, scrolling=True)

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
    # Sanitizing text for FPDF (It hates emojis and special chars)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. SIDEBAR ---
with st.sidebar:
    st_lottie(anim_welcome, height=120, key="logo_anim")
    st.title("KnowledgeOS")
    st.caption("Ultimate Teacher's Toolkit")
    
    selected = option_menu(
        menu_title="Navigation",
        options=["Dashboard", "Smart Chat", "Planner Pro", "Media Studio", "My Library"],
        icons=["speedometer", "chat-text", "journal-bookmark", "play-btn", "folder2-open"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "icon": {"color": "#4F8BF9", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#e1e1e1"},
            "nav-link-selected": {"background-color": "#4F8BF9"},
        }
    )
    
    st.markdown("---")
    st.info("System Status: 🟢 Online")

# --- 6. MAIN APP LOGIC ---

# === DASHBOARD ===
if selected == "Dashboard":
    st.markdown("<h1 style='text-align: center;'>🚀 Command Center</h1>", unsafe_allow_html=True)
    
    # Fetch Live Stats
    c = conn.cursor()
    c.execute("SELECT tool, COUNT(*) FROM history GROUP BY tool")
    stats = dict(c.fetchall())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>📚 Plans</h3><h2>{stats.get("Planner", 0)}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>🎥 Videos</h3><h2>{stats.get("YouTube", 0)}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>🧠 Chats</h3><h2>{stats.get("Chat", 0)}</h2></div>', unsafe_allow_html=True)
    with col4:
        # Dynamic "Pro Status" based on usage
        total_usage = sum(stats.values())
        status = "Novice" if total_usage < 5 else "Expert" if total_usage < 20 else "Master"
        st.markdown(f'<div class="metric-card"><h3>🏆 Rank</h3><h2>{status}</h2></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💡 Quick Tips")
        st.info("• **Planner Pro:** Ab aap 'Mind Map' tab mein diagrams dekh sakte hain.\n• **Media Studio:** YouTube link dalo aur notes paao.\n• **Library:** Purani files delete bhi kar sakte ho.")
    with c2:
        st_lottie(anim_loading, height=200, key="dash_anim")

# === SMART CHAT ===
elif selected == "Smart Chat":
    col_a, col_b = st.columns([3,1])
    with col_a: st.header("🧠 Smart Document Chat")
    with col_b: st_lottie(anim_chat, height=80, key="chat_head_anim")
    
    uploaded_file = st.file_uploader("Upload PDF or Text File", type=["pdf", "txt"])
    
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    if uploaded_file:
        text = ""
        if uploaded_file.name.endswith(".pdf"):
            text = "".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
        else:
            text = uploaded_file.read().decode("utf-8")
        
        st.toast("File Read Successfully!", icon="📖")
        
        # Display Chat
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        
        prompt = st.chat_input("Ask something about the document...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)
            
            with st.spinner("Analyzing..."):
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Context: {text[:20000]}"}, {"role": "user", "content": prompt}],
                    model=MODEL_NAME
                ).choices[0].message.content
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.markdown(f'<div class="bot-msg">{response}</div>', unsafe_allow_html=True)
                
                # Save to DB
                conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Chat", "Chat Log", f"Q: {prompt}\nA: {response}"))
                conn.commit()

# === PLANNER PRO ===
elif selected == "Planner Pro":
    col_a, col_b = st.columns([3,1])
    with col_a: st.header("📝 Lesson Planner Suite")
    with col_b: st_lottie(anim_plan, height=80, key="plan_head_anim")
    
    tab1, tab2, tab3 = st.tabs(["📘 Lesson Generator", "🗺️ Mind Map (Fixed)", "✉️ Parent Comms"])
    
    # TAB 1: GENERATOR
    with tab1:
        c1, c2 = st.columns(2)
        topic = c1.text_input("Lesson Topic", placeholder="e.g. Gravity")
        level = c2.select_slider("Class Level", options=["Class 1-5", "Class 6-8", "Class 9-10", "College"])
        
        if st.button("Generate Plan ✨", type="primary"):
            with st.spinner("Thinking..."):
                plan = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Create a structured lesson plan for '{topic}' level '{level}'."}], 
                    model=MODEL_NAME
                ).choices[0].message.content
                st.session_state['gen_plan'] = plan
        
        if 'gen_plan' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['gen_plan'])
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save"):
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("Planner", topic, st.session_state['gen_plan']))
                    conn.commit()
                    st.toast("Saved!", icon="✅")
            with col2:
                pdf_bytes = create_pdf(st.session_state['gen_plan'])
                st.download_button("📥 PDF", data=pdf_bytes, file_name="plan.pdf", mime='application/pdf')
            with col3:
                if st.button("🔊 Listen"):
                    audio_file = text_to_speech(st.session_state['gen_plan'][:500])
                    st.audio(audio_file)

    # TAB 2: MIND MAP (FIXED)
    with tab2:
        st.subheader("Visual Concept Mapper")
        concept = st.text_input("Enter Topic for Mind Map", placeholder="e.g. Solar System")
        if st.button("Visualize 🧠"):
            with st.spinner("Drawing Chart..."):
                prompt = f"Create a Mermaid.js diagram code (graph TD) for '{concept}'. Return ONLY the code inside ```mermaid``` tags."
                response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME).choices[0].message.content
                
                try:
                    # Extracting code cleanly
                    mermaid_code = response.split("```mermaid")[1].split("```")[0].strip()
                    render_mermaid(mermaid_code) # Calling the JS function
                except:
                    st.error("AI couldn't generate a valid chart code. Try a simpler topic.")

    # TAB 3: PARENT COMMS
    with tab3:
        st.subheader("✉️ Parent Communication Tool")
        st.info("Use this to write professional emails to parents about student progress.")
        s_name = st.text_input("Student Name")
        s_issue = st.text_area("What is the update? (e.g. Scored low in Math, Very helpful in class)")
        if st.button("Draft Email"):
            email = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Write a polite, professional email to parents of {s_name} regarding: {s_issue}"}], 
                model=MODEL_NAME
            ).choices[0].message.content
            st.code(email, language="markdown")

# === MEDIA STUDIO ===
elif selected == "Media Studio":
    col_a, col_b = st.columns([3,1])
    with col_a: st.header("🎥 Media & Quiz Studio")
    with col_b: st_lottie(anim_video, height=80, key="vid_head_anim")
    
    st.markdown("### YouTube Summarizer")
    link = st.text_input("Paste YouTube Link (Must have captions)")
    
    if st.button("Summarize 🎬"):
        if "v=" in link or "youtu.be" in link:
            try:
                video_id = link.split("v=")[1].split("&")[0] if "v=" in link else link.split("/")[-1]
                
                # Try to get transcript (Better Logic)
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                except:
                    # Fallback: Try to list available transcripts and pick one
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id).find_generated_transcript(['en']).fetch()
                
                full_text = " ".join([d['text'] for d in transcript_list])
                
                with st.spinner("Summarizing..."):
                    summary = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"Summarize this video content:\n{full_text[:15000]}"}], 
                        model=MODEL_NAME
                    ).choices[0].message.content
                
                st.markdown(summary)
                
                if st.button("💾 Save Summary"):
                    conn.cursor().execute("INSERT INTO history (tool, title, content) VALUES (?,?,?)", ("YouTube", "Video Summary", summary))
                    conn.commit()
                    st.toast("Saved!", icon="✅")
                    
            except Exception as e:
                st.error("Error: Video has no captions enabled by the creator. Please find a video with CC.")
        else:
            st.warning("Invalid Link")

# === MY LIBRARY ===
elif selected == "My Library":
    st.header("🗄️ Your Archives")
    
    # Search & Delete Logic
    search = st.text_input("🔍 Search Files...")
    
    query = "SELECT id, tool, title, timestamp FROM history"
    params = []
    if search:
        query += " WHERE title LIKE ?"
        params.append(f"%{search}%")
    query += " ORDER BY id DESC"
    
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Tool", "Title", "Date"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        c1, c2, c3 = st.columns([1,1,2])
        with c1: oid = st.number_input("Enter ID", min_value=0, step=1)
        with c2: 
            if st.button("📂 Open"):
                data = c.execute("SELECT content FROM history WHERE id=?", (oid,)).fetchone()
                if data:
                    st.markdown("---")
                    st.markdown(data[0])
        with c3:
            if st.button("🗑️ Delete", type="primary"):
                c.execute("DELETE FROM history WHERE id=?", (oid,))
                conn.commit()
                st.warning(f"File {oid} Deleted.")
                st.rerun()
    else:
        st.info("Library empty.")
            
