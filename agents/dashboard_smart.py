

"""
AI Dashboard - WITH INTELLIGENT CHATBOT
Real LLM-powered Q&A like ChatGPT
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

from utils import LLMClient, SheetsReader, PrivacyFilter
from agents import SheetClassifierAgent, ColumnInterpreterAgent, DashboardBuilderAgent

# Import the SMART chatbot
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Smart chatbot implementation
class SmartChatbot:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def answer_question(self, question, df, column_mappings, available_dimensions):
        """INTELLIGENT chatbot using LLM"""
        
        # Compute real stats
        stats = self._compute_stats(df, column_mappings)
        
        # Ask LLM to answer
        system_msg = """You are a helpful data analyst assistant. Answer the user's question about their work tasks.

You have access to real statistics from their data. Use these numbers to give accurate, conversational answers.

Be natural and helpful like ChatGPT. Give specific insights."""

        prompt = f"""User's Question: "{question}"

Their Data:
- Total tasks: {stats['total']}
- Pending: {stats['pending']}
- Completed: {stats['completed']}
- Total errors: {stats['errors']}
- Tasks with errors: {stats['error_tasks']}

Status breakdown: {stats['status_breakdown']}

Give a helpful, conversational answer using these exact numbers."""

        try:
            result = self.llm.call_llm(prompt, system_msg)
            
            # Extract text from response
            if isinstance(result, dict):
                answer = result.get('answer') or result.get('response') or result.get('text') or str(result)
            else:
                answer = str(result)
            
            answer = answer.strip()
            
            # If answer is JSON or too short, use fallback
            if answer.startswith('{') or len(answer) < 20:
                return self._fallback(question, stats)
            
            return answer
            
        except Exception as e:
            return self._fallback(question, stats)
    
    def _compute_stats(self, df, col_map):
        """Compute actual statistics"""
        stats = {'total': len(df), 'pending': 0, 'completed': 0, 'errors': 0, 'error_tasks': 0, 'status_breakdown': {}}
        
        status_col = col_map.get('status', 'none')
        if status_col != 'none' and status_col in df.columns:
            stats['status_breakdown'] = df[status_col].value_counts().to_dict()
            stats['pending'] = df[df[status_col].astype(str).str.lower().str.contains('pending|progress|todo|ongoing', na=False, regex=True)].shape[0]
            stats['completed'] = df[df[status_col].astype(str).str.lower().str.contains('completed|done|finished|closed', na=False, regex=True)].shape[0]
        
        errors_col = col_map.get('errors', 'none')
        if errors_col != 'none' and errors_col in df.columns:
            stats['errors'] = int(df[errors_col].sum())
            stats['error_tasks'] = int((df[errors_col] > 0).sum())
        
        return stats
    
    def _fallback(self, question, stats):
        """Fallback answer"""
        q = question.lower()
        
        if 'pending' in q:
            return f"You have **{stats['pending']} pending tasks** out of {stats['total']} total."
        elif 'completed' in q or 'done' in q:
            return f"You have **{stats['completed']} completed tasks** out of {stats['total']} total."
        elif 'error' in q or 'bug' in q:
            return f"You have **{stats['errors']} total errors** across {stats['error_tasks']} tasks."
        elif 'summary' in q:
            s = f"**Summary:**\n• Total: {stats['total']} tasks\n• Pending: {stats['pending']}\n• Completed: {stats['completed']}\n• Errors: {stats['errors']}\n"
            if stats['status_breakdown']:
                s += f"\n**Status breakdown:**\n"
                for status, count in list(stats['status_breakdown'].items())[:5]:
                    s += f"• {status}: {count}\n"
            return s
        else:
            return f"You have **{stats['total']} tasks**. Ask me about pending tasks, completed tasks, errors, or request a summary."

st.set_page_config(page_title="AI Dashboard", page_icon="📊", layout="wide")

# Session state
if 'init' not in st.session_state:
    st.session_state.update({
        'loaded': False, 'sheets': {}, 'user_df': None, 'config': None,
        'col_map': {}, 'sheet': None, 'relevant': {}, 'chat': [],
        'refresh': 0, 'src_type': None, 'src': None, 'user': 'John Doe',
        'auto': False, 'init': True
    })

# CSS
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#667eea,#764ba2)}
.main{background:white;border-radius:20px;padding:20px;margin:20px}
h1{color:#667eea;text-align:center;font-size:3rem}
.metric-card{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:30px;border-radius:15px;text-align:center;margin:10px;box-shadow:0 10px 20px rgba(0,0,0,0.2)}
.metric-value{font-size:48px;font-weight:bold}
.metric-label{font-size:18px;margin-top:10px;text-transform:uppercase}
.chat-msg{background:#f0f9ff;border-left:4px solid #0ea5e9;padding:15px;border-radius:10px;margin:10px 0}
.bot-msg{background:#f0fdf4;border-left:4px solid #10b981}
</style>
""", unsafe_allow_html=True)

def init():
    l = LLMClient()
    chatbot = SmartChatbot(l)
    return l, SheetsReader(), SheetClassifierAgent(l), ColumnInterpreterAgent(l), DashboardBuilderAgent(l), chatbot

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
    st.title("📊 AI Dashboard")
    
    l, sr, c, i, b, chatbot = init()
    
    with st.sidebar:
        st.header("⚙️ Settings")
        st.session_state.user = st.text_input("👤 Name", st.session_state.user)
        st.divider()
        
        if st.session_state.loaded and st.session_state.src_type == "Google Sheets":
            st.session_state.auto = st.toggle("🔄 Auto-refresh (5s)", st.session_state.auto)
            st.success("✅ ON" if st.session_state.auto else "⏸️ OFF")
        else:
            st.info("🔄 Auto-refresh: Use Google Sheets")
        
        st.divider()
        st.subheader("📥 Data")
        st.info("💡 **Use Excel files** (ultra_complex_workbook.xlsx)")
        
        stype = st.radio("Source:", ["Excel File", "Google Sheets"])
        
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
                    else:
                        st.error("No work sheets found")
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.session_state.loaded and st.button("♻️ Refresh", use_container_width=True):
            try:
                sd = load(sr, st.session_state.src_type, st.session_state.src)
                rel = analyze(sd, c)
                st.session_state.sheets = sd
                st.session_state.relevant = rel
                st.session_state.refresh += 1
                st.success("Refreshed")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.divider()
        if st.session_state.loaded:
            st.success("✅ Loaded")
            st.metric("Refreshes", st.session_state.refresh)
    
    if st.session_state.loaded:
        if st.session_state.auto:
            st.info("🔄 Auto-refresh active")
        
        sh = st.selectbox("📋 Select Sheet:", list(st.session_state.relevant.keys()))
        
        try:
            ud, cm, cfg = process(sh, st.session_state.sheets, st.session_state.user, i, b, st.session_state.relevant)
            st.session_state.update({'user_df': ud, 'col_map': cm, 'config': cfg, 'sheet': sh})
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
        
        st.info(f"📊 {len(ud)} rows for **{st.session_state.user}**")
        
        with st.expander("🔍 AI Mapping"):
            st.json(cm)
        
        st.markdown("---")
        st.subheader("📈 Metrics")
        
        if 'metrics' in cfg:
            m = b.compute_metrics(ud, cfg['metrics'], cm)
            cs = st.columns(min(len(m), 4))
            for idx, mt in enumerate(m):
                with cs[idx % 4]:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{mt["value"]}</div><div class="metric-label">{mt["label"]}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📊 Charts")
        
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
        st.subheader("💬 Smart AI Assistant")
        st.caption("🤖 Powered by LLM - Ask anything about your data!")
        
        if st.session_state.chat:
            with st.expander("📜 Conversation History", expanded=False):
                for ch in st.session_state.chat[-5:]:
                    st.markdown(f'<div class="chat-msg">**You:** {ch["q"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="chat-msg bot-msg">**AI:** {ch["a"]}</div>', unsafe_allow_html=True)
        
        # Question input
        qu = st.text_area("Ask me anything:", placeholder="What's the breakdown of my tasks by status?", height=80)
        
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if st.button("💬 Ask AI", type="primary", use_container_width=True):
                if qu:
                    with st.spinner("🤖 AI is thinking..."):
                        ans = chatbot.answer_question(qu, ud, cm, list(cm.keys()))
                        st.session_state.chat.append({'q': qu, 'a': ans, 't': datetime.now().strftime("%H:%M")})
                        st.rerun()
        
        with col2:
            if st.button("📊 Get Summary", use_container_width=True):
                with st.spinner("🤖 Generating summary..."):
                    ans = chatbot.answer_question("Give me a complete summary of my tasks", ud, cm, list(cm.keys()))
                    st.session_state.chat.append({'q': "Summary", 'a': ans, 't': datetime.now().strftime("%H:%M")})
                    st.rerun()
        
        with col3:
            if st.button("🔄 Clear Chat", use_container_width=True):
                st.session_state.chat = []
                st.rerun()
        
        # Show latest answer
        if st.session_state.chat:
            latest = st.session_state.chat[-1]
            st.markdown("---")
            st.markdown(f'<div class="chat-msg">**You:** {latest["q"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-msg bot-msg">**AI:** {latest["a"]}</div>', unsafe_allow_html=True)
        
        # Example questions
        st.caption("**Try asking:**")
        ex_cols = st.columns(3)
        examples = [
            "What percentage of my tasks are completed?",
            "Which status has the most tasks?",
            "How many high priority items do I have?"
        ]
        for idx, ex in enumerate(examples):
            with ex_cols[idx]:
                if st.button(f"💡 {ex[:30]}...", key=f"ex{idx}", use_container_width=True):
                    with st.spinner("🤖 AI thinking..."):
                        ans = chatbot.answer_question(ex, ud, cm, list(cm.keys()))
                        st.session_state.chat.append({'q': ex, 'a': ans, 't': datetime.now().strftime("%H:%M")})
                        st.rerun()
        
        # Auto-refresh
        if st.session_state.auto and st.session_state.src_type == "Google Sheets":
            time.sleep(1000)
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
        st.markdown("### 👋 Welcome!")
        st.info("👈 Upload **ultra_complex_workbook.xlsx** to get started")
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**🔒 Privacy**\nZero storage")
        with cols[1]:
            st.markdown("**🤖 Smart AI**\nLLM-powered chatbot")
        with cols[2]:
            st.markdown("**📊 Live Data**\nAuto-refresh")

if __name__ == "__main__":
    main()