"""
TaskFlow AI - Elite AI-Powered Dashboard
With ChatGPT-Level Intelligent Chatbot
"""


# 🔥 REMOVE Streamlit-injected proxies BEFORE imports
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import sys
import os

import os




# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from utils import LLMClient, SheetsReader, PrivacyFilter
from agents import SheetClassifierAgent, ColumnInterpreterAgent, DashboardBuilderAgent
from elite_chatbot import EliteChatbot

st.set_page_config(page_title="TaskFlow AI", page_icon="🚀", layout="wide")

# Session state
if 'init' not in st.session_state:
    st.session_state.update({
        'loaded': False, 'sheets': {}, 'user_df': None, 'config': None,
        'col_map': {}, 'sheet': None, 'relevant': {}, 'chat': [],
        'refresh': 0, 'src_type': None, 'src': None, 'user': 'John Doe',
        'auto': False, 'init': True, 'chatbot': None
    })

# CSS
st.markdown("""
<style>
/* App background */
.stApp {
    background: linear-gradient(135deg, #667eea, #764ba2);
}

/* Main container */
.main {
    background: white;
    color: #1f2937; /* force dark text */
    border-radius: 20px;
    padding: 20px;
    margin: 20px;
}

/* Headings */
.main h1,
.main h2,
.main h3,
.main h4,
.main h5,
.main h6,
.main p,
.main span,
.main label {
    color: #1f2937 !important;
}

/* Title */
h1 {
    color: #667eea !important;
    text-align: center;
    font-size: 3.5rem;
    font-weight: 900;
}

.subtitle {
    text-align: center;
    color: #6b7280 !important;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white !important;
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    margin: 10px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    transition: transform 0.3s;
}

.metric-card:hover {
    transform: translateY(-5px);
}

.metric-value {
    font-size: 48px;
    font-weight: bold;
}

.metric-label {
    font-size: 18px;
    margin-top: 10px;
    text-transform: uppercase;
}

/* Chat bubbles */
.chat-container {
    background: #f8f9fa;
    color: #1f2937;
    border-radius: 15px;
    padding: 20px;
    margin: 20px 0;
}

.user-bubble {
    background: #e0e7ff;
    color: #1f2937;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 4px solid #667eea;
}

.ai-bubble {
    background: #f0fdf4;
    color: #065f46;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 4px solid #10b981;
}

/* Badge */
.elite-badge {
    background: #fbbf24;
    color: #78350f;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY")

def init():
    try:
        l = LLMClient()
        chatbot = EliteChatbot()
        return l, SheetsReader(), SheetClassifierAgent(l), ColumnInterpreterAgent(l), DashboardBuilderAgent(l), chatbot
    except Exception as e:
        st.exception(e)   # 👈 shows full traceback
        st.stop()


def load(sr, st_type, s):
    if st_type == "Google Sheets":
        return sr.read_google_sheet(s)
    return sr.read_excel_file(s)

def analyze(sd, c):
    cl = {}
    for n, d in sd.items():
        cl[n] = c.classify_sheet(n, d)
    return {n: d for n, d in cl.items() if d.get('relevant', False)}

def process(sn, sd, u, i, b, r):
    d = sd[sn]
    cm = i.interpret_columns(d, sn)
    a = cm.get('assignee', 'none')
    ud = PrivacyFilter.filter_for_user(d, u, a) if a != 'none' else d
    cfg = b.build_dashboard_config(r[sn]['sheet_type'], cm, len(ud), sn)
    return ud, cm, cfg

def main():
    st.markdown('<h1>🚀 TaskFlow AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Work Intelligence • Elite Chatbot • Real-Time Insights</p>', unsafe_allow_html=True)
    
    l, sr, c, i, b, chatbot = init()
    st.session_state.chatbot = chatbot
    
    with st.sidebar:
        st.header("⚙️ Settings")
        st.session_state.user = st.text_input("👤 Your Name", st.session_state.user)
        st.divider()
        
        if st.session_state.loaded and st.session_state.src_type == "Google Sheets":
            st.session_state.auto = st.toggle("🔄 Auto-refresh (20 mins)", st.session_state.auto)
            st.success("✅ ON" if st.session_state.auto else "⏸️ OFF")
        
        st.divider()
        st.subheader("📥 Data Source")
        st.info("💡 Upload **ultra_complex_workbook.xlsx**")
        
        stype = st.radio("Type:", ["Excel File", "Google Sheets"])
        
        if stype == "Google Sheets":
            src = st.text_input("URL:")
            ok = bool(src)
        else:
            src = st.file_uploader("Upload:", type=['xlsx', 'xls'])
            ok = src is not None
        
        if st.button("🚀 LOAD", type="primary", disabled=not ok, use_container_width=True):
            try:
                with st.spinner("Loading..."):
                    sd = load(sr, stype, src)
                    rel = analyze(sd, c)
                    if rel:
                        st.session_state.update({'sheets': sd, 'relevant': rel, 'loaded': True, 'src_type': stype, 'src': src, 'refresh': 0})
                        st.success(f"✅ {len(rel)} sheets")
                        time.sleep(1)
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.session_state.loaded and st.button("♻️ Refresh", use_container_width=True):
            try:
                sd = load(sr, st.session_state.src_type, st.session_state.src)
                rel = analyze(sd, c)
                st.session_state.sheets = sd
                st.session_state.relevant = rel
                st.session_state.refresh += 1
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        
        st.divider()
        if st.session_state.loaded:
            st.success("✅ Loaded")
            st.metric("Refreshes", st.session_state.refresh)
        
        st.divider()
        st.markdown("### 🌟 Features")
        st.markdown("✅ Elite AI Chatbot\n✅ Smart Analysis\n✅ Auto-refresh\n✅ Privacy-first")
    
    if st.session_state.loaded:
        sh = st.selectbox("📋 Select Sheet:", list(st.session_state.relevant.keys()))
        
        try:
            ud, cm, cfg = process(sh, st.session_state.sheets, st.session_state.user, i, b, st.session_state.relevant)
            st.session_state.update({'user_df': ud, 'col_map': cm, 'config': cfg, 'sheet': sh})
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
        
        st.info(f"📊 Showing {len(ud)} rows for **{st.session_state.user}**")
        
        with st.expander("🔍 AI Mapping"):
            st.json(cm)
        
        st.markdown("---")
        st.subheader("📈 Key Metrics")
        
        if 'metrics' in cfg:
            m = b.compute_metrics(ud, cfg['metrics'], cm)
            cs = st.columns(min(len(m), 4))
            for idx, mt in enumerate(m):
                with cs[idx % 4]:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{mt["value"]}</div><div class="metric-label">{mt["label"]}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📊 Visualizations")
        
        if 'charts' in cfg and cfg['charts']:
            cs = st.columns(2)
            for idx, ch in enumerate(cfg['charts'][:2]):
                cn = cm.get(ch.get('dimension', 'status'), 'none')
                if cn != 'none' and cn in ud.columns:
                    with cs[idx % 2]:
                        vc = ud[cn].value_counts()
                        fig = px.pie(values=vc.values, names=vc.index, hole=0.4) if ch.get('type') == 'pie' else px.bar(x=vc.index, y=vc.values)
                        if ch.get('type') != 'pie':
                            fig.update_traces(marker_color='#667eea')
                        fig.update_layout(title=cn, height=350)
                        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 Your Tasks")
        st.dataframe(ud, use_container_width=True, height=400)
        
        st.markdown("---")
        
        # ELITE CHATBOT
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("💬 Elite AI Assistant")
        with col2:
            st.markdown('<span class="elite-badge">⚡ POWERED BY GPT-LEVEL AI</span>', unsafe_allow_html=True)
        
        st.caption("Ask me anything about your data - I understand context, filter tasks, and provide insights!")
        
        # Chat history
        if st.session_state.chat:
            with st.expander("📜 Conversation History", expanded=False):
                for chat in st.session_state.chat[-10:]:
                    st.markdown(f'<div class="user-bubble">**You:** {chat["q"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="ai-bubble">**AI:** {chat["a"]}</div>', unsafe_allow_html=True)
        
        # Question input
        question = st.text_area(
            "Ask me anything:", 
            placeholder="e.g., 'Show me all frontend tasks' or 'What's the status of backend work?'",
            height=100
        )
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            ask_btn = st.button("🤖 Ask Elite AI", type="primary", use_container_width=True)
        with col2:
            summary_btn = st.button("📊 Get Smart Summary", use_container_width=True)
        with col3:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_btn:
            st.session_state.chat = []
            chatbot.clear_history()
            st.rerun()
        
        if ask_btn and question:
            with st.spinner("🧠 Elite AI is analyzing your data..."):
                try:
                    answer = chatbot.answer(question, ud, cm)
                    st.session_state.chat.append({'q': question, 'a': answer})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if summary_btn:
            with st.spinner("🧠 Generating intelligent summary..."):
                try:
                    answer = chatbot.answer("Give me a comprehensive summary of all my tasks with insights", ud, cm)
                    st.session_state.chat.append({'q': "Comprehensive Summary", 'a': answer})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Show latest response
        if st.session_state.chat:
            latest = st.session_state.chat[-1]
            st.markdown("### Latest Response:")
            st.markdown(f'<div class="user-bubble">**You:** {latest["q"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-bubble">**AI:** {latest["a"]}</div>', unsafe_allow_html=True)
        
        # Example questions
        st.markdown("**💡 Try asking:**")
        ex = st.columns(4)
        examples = [
            "Show me frontend tasks",
            "What's in review?",
            "High priority items",
            "Tasks with errors"
        ]
        for idx, eq in enumerate(examples):
            with ex[idx]:
                if st.button(eq, key=f"ex{idx}"):
                    with st.spinner("🧠 AI thinking..."):
                        try:
                            answer = chatbot.answer(eq, ud, cm)
                            st.session_state.chat.append({'q': eq, 'a': answer})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-refresh
        if st.session_state.auto and st.session_state.src_type == "Google Sheets":
            time.sleep(1200)
            try:
                sd = load(sr, st.session_state.src_type, st.session_state.src)
                rel = analyze(sd, c)
                st.session_state.sheets = sd
                st.session_state.relevant = rel
                st.session_state.refresh += 1
            except:
                pass
            st.rerun()
    
    else:
        st.markdown("### 👋 Welcome to TaskFlow AI!")
        st.info("👈 Upload your data to unlock elite AI-powered insights")
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**🤖 Elite AI**\n\nChatGPT-level intelligence")
        with cols[1]:
            st.markdown("**🔍 Smart Search**\n\nUnderstanding")
        with cols[2]:
            st.markdown("**⚡ Real-time**\n\nLive insights")

if __name__ == "__main__":
    main()