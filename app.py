"""
app.py - AI-Based Grievance Redressal and Escalation System
Roles: employee | hr_admin | senior_admin
"""

import streamlit as st
import hashlib
import uuid
from datetime import datetime, timezone
from collections import Counter
import plotly.graph_objects as go
import pandas as pd
from supabase_client import get_client
from classifier import classify

# ── Auto-Escalation Config ────────────────────────────────────────────────────
# Change to 0.01 (~36 seconds) for testing. Set back to 24 for production.
# ── Auto-Escalation Config ───────────────────────────────────────────────────
# Set to 0.01 (~36 seconds) for testing. Change back to 24 for production.
ESCALATION_HOURS = 24

st.set_page_config(
    page_title="Grievance Redressal System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Sidebar overrides ── */
[data-testid="stSidebar"] {
    background: #0b0f1a !important;
    border-right: 1px solid #1e2d45;
}
[data-testid="stSidebar"] * { color: #cbd5e1; }

/* ── Main background ── */
.stApp { background: #060b14; }
[data-testid="stAppViewContainer"] { background: #060b14; }
[data-testid="block-container"] { padding-top: 2rem; }

/* ── Sidebar logo block ── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0 16px 0;
    border-bottom: 1px solid #1e2d45;
    margin-bottom: 16px;
}
.sidebar-logo .logo-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.sidebar-logo .logo-text { font-size: 15px; font-weight: 700; color: #f1f5f9 !important; line-height: 1.2; }
.sidebar-logo .logo-sub  { font-size: 11px; color: #64748b !important; }

/* ── Sidebar user card ── */
.sidebar-user {
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 12px;
}
.sidebar-user .user-name  { font-size: 14px; font-weight: 700; color: #f1f5f9 !important; }
.sidebar-user .user-role  { font-size: 11px; color: #94a3b8 !important; margin-top: 2px; }
.sidebar-user .user-email { font-size: 11px; color: #475569 !important; margin-top: 1px; }

/* ── Sidebar info cards ── */
.sidebar-info {
    background: #0f172a;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 12px;
    color: #94a3b8 !important;
}
.sidebar-info .info-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #475569 !important;
    margin-bottom: 6px;
}
.sidebar-info .info-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 0;
    color: #94a3b8 !important;
    font-size: 12px;
}

/* ── Auth page ── */
.auth-header {
    text-align: center;
    margin-bottom: 32px;
}
.auth-header h1 {
    font-size: 28px;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.5px;
}
.auth-header p { font-size: 14px; color: #64748b; margin-top: 4px; }

/* ── Page header ── */
.page-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #1e2d45;
}
.page-header h2 {
    font-size: 22px;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.3px;
    margin: 0;
}
.page-header p { font-size: 13px; color: #64748b; margin: 4px 0 0 0; }

/* ── Metric cards ── */
.metric-card {
    background: #0f172a;
    border: 1px solid #1e2d45;
    border-radius: 14px;
    padding: 18px 16px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #3b82f6; }
.metric-num { font-size: 30px; font-weight: 800; color: #60a5fa; letter-spacing: -1px; }
.metric-lbl { font-size: 11px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Grievance cards ── */
.grievance-card {
    background: #0f172a;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.grievance-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f620;
}
.grievance-id   { font-size: 11px; color: #475569; font-family: monospace; }
.grievance-text { font-size: 14px; color: #e2e8f0; margin: 8px 0; font-weight: 500; line-height: 1.5; }
.grievance-meta { font-size: 12px; color: #64748b; margin-top: 6px; }

/* ── Admin note ── */
.admin-note {
    background: #0c1a2e;
    border-left: 3px solid #3b82f6;
    padding: 8px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    color: #93c5fd;
    margin-top: 10px;
}

/* ── Tags ── */
.tag { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; margin:2px; letter-spacing:0.3px; }
.tag-high     { background:#450a0a; color:#fca5a5; border:1px solid #7f1d1d; }
.tag-medium   { background:#451a03; color:#fcd34d; border:1px solid #78350f; }
.tag-low      { background:#052e16; color:#86efac; border:1px solid #14532d; }
.tag-category { background:#0c1a2e; color:#93c5fd; border:1px solid #1e3a5f; }
.tag-pending  { background:#1e1b4b; color:#a5b4fc; border:1px solid #312e81; }

/* ── Pills ── */
.pill { display:inline-block; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:0.5px; }
.pill-pending   { background:#1e1b4b; color:#a5b4fc; }
.pill-progress  { background:#042f2e; color:#6ee7b7; }
.pill-resolved  { background:#052e16; color:#86efac; }
.pill-escalated { background:#450a0a; color:#fca5a5; }
.pill-closed    { background:#0f172a; color:#64748b; border:1px solid #1e2d45; }

/* ── Banners ── */
.level1-banner {
    background: linear-gradient(135deg, #0c1a2e 0%, #0f172a 100%);
    border: 1px solid #1d4ed8;
    border-left: 4px solid #3b82f6;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 20px;
    color: #93c5fd;
    font-size: 13px;
}
.level2-banner {
    background: linear-gradient(135deg, #1a0505 0%, #0f172a 100%);
    border: 1px solid #991b1b;
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 20px;
    color: #fca5a5;
    font-size: 13px;
}

/* ── Chat bubbles ── */
.chat-container { display:flex; flex-direction:column; gap:12px; padding:16px 0; max-height:440px; overflow-y:auto; }
.bubble-user {
    align-self: flex-end;
    background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    color: white;
    padding: 11px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 72%;
    font-size: 14px;
    line-height: 1.5;
    box-shadow: 0 2px 8px #3b82f620;
}
.bubble-bot {
    align-self: flex-start;
    background: #0f172a;
    color: #e2e8f0;
    padding: 11px 16px;
    border-radius: 18px 18px 18px 4px;
    max-width: 72%;
    font-size: 14px;
    line-height: 1.5;
    border: 1px solid #1e2d45;
}
.bubble-bot strong { color: #60a5fa; }

/* ── Flowchart ── */
.flow-container { display:flex; align-items:center; justify-content:center; gap:0; flex-wrap:wrap; margin:24px 0; }
.flow-node {
    background: #0f172a;
    border: 2px solid #1e2d45;
    border-radius: 14px;
    padding: 18px 22px;
    text-align: center;
    min-width: 130px;
    transition: all 0.2s;
}
.flow-node .icon    { font-size: 26px; }
.flow-node .label   { font-size: 13px; font-weight: 700; color: #e2e8f0; margin-top: 6px; }
.flow-node .sublabel{ font-size: 11px; color: #64748b; margin-top: 3px; }
.flow-arrow         { font-size: 20px; color: #334155; padding: 0 8px; }
.flow-node-pending  { border-color: #6366f1; }
.flow-node-progress { border-color: #06b6d4; }
.flow-node-escalated{ border-color: #ef4444; }
.flow-node-resolved { border-color: #22c55e; }
.flow-node-closed   { border-color: #475569; }
.flow-node-auto     { border-color: #f97316; background: #140c02; }

/* ── Streamlit input overrides ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #0f172a !important;
    border: 1px solid #1e2d45 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px #3b82f620 !important;
}
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    border: none !important;
    box-shadow: 0 2px 8px #3b82f640 !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 16px #3b82f660 !important;
    transform: translateY(-1px) !important;
}
/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1e2d45;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #0f172a !important;
    color: #60a5fa !important;
    border-bottom: 2px solid #3b82f6 !important;
}
/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0f172a !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def db(): return get_client()
def now_iso(): return datetime.now(timezone.utc).isoformat()

ROLE_LABELS = {"employee":"👤 Employee","hr_admin":"🟦 HR Manager","senior_admin":"🟥 Department Head"}

def priority_tag(p):
    cls = {"High":"tag-high","Medium":"tag-medium","Low":"tag-low"}.get(p,"tag-low")
    icon = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(p,"")
    return f'<span class="tag {cls}">{icon} {p}</span>'

def status_pill(s):
    cls = {"Pending":"pill-pending","In Progress":"pill-progress","Resolved":"pill-resolved",
           "Escalated":"pill-escalated","Closed":"pill-closed"}.get(s,"pill-pending")
    icon = {"Pending":"⏳","In Progress":"🔧","Resolved":"✅","Escalated":"🚨","Closed":"🔒"}.get(s,"")
    return f'<span class="pill {cls}">{icon} {s}</span>'

def chart_bg():
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), margin=dict(t=20,b=20,l=20,r=20))

# ── Auto-Escalation Engine ────────────────────────────────────────────────────
def run_auto_escalation():
    """
    Runs on every page load.
    Escalates Level 1 grievances that are Pending/In Progress
    and older than ESCALATION_HOURS.
    """
    all_g = get_all_grievances()
    now   = datetime.now(timezone.utc)
    count = 0

    for g in all_g:
        if g["escalation_level"] != 1:
            continue
        if g["status"] not in ("Pending", "In Progress"):
            continue

        raw = g.get("created_at", "")
        if not raw:
            continue

        try:
            # Supabase may return: "2026-03-04T03:40:00+00:00"
            #                   or "2026-03-04T03:40:00"
            #                   or "2026-03-04 03:40:00"  (space instead of T)
            # Normalise: replace space separator with T
            raw_clean = raw.replace(" ", "T")
            # Remove microseconds if present (e.g. .123456)
            if "." in raw_clean:
                raw_clean = raw_clean[:raw_clean.index(".")] + raw_clean[raw_clean.index(".")+7:]
            created = datetime.fromisoformat(raw_clean)
            # If no timezone info, assume UTC
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        except Exception:
            # Last resort: parse just the date+time part
            try:
                created = datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                try:
                    created = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except Exception:
                    continue

        age_hours = (now - created).total_seconds() / 3600

        if age_hours >= ESCALATION_HOURS:
            existing  = g.get("admin_notes") or ""
            note      = f"⚡ Auto-escalated: No action within {ESCALATION_HOURS}h. Forwarded to Department Head."
            final     = f"{existing}\n{note}".strip() if existing else note
            db().table("grievances").update({
                "status":           "Escalated",
                "escalation_level": 2,
                "admin_notes":      final,
            }).eq("id", g["id"]).execute()
            count += 1

    return count

# ── Auth ──────────────────────────────────────────────────────────────────────
def register(name, email, password, role):
    if db().table("users").select("id").eq("email",email).execute().data:
        return False,"Email already registered."
    db().table("users").insert({"id":str(uuid.uuid4()),"name":name,"email":email,
        "password_hash":hash_pw(password),"role":role,"created_at":now_iso()}).execute()
    return True,"Account created! Please log in."

def login(email, password):
    res = db().table("users").select("*").eq("email",email).execute()
    if not res.data: return None,"No account found."
    u = res.data[0]
    if u["password_hash"] != hash_pw(password): return None,"Incorrect password."
    return u,"Welcome back!"

# ── DB ops ────────────────────────────────────────────────────────────────────
def save_grievance(owner_email, text, result):
    db().table("grievances").insert({"id":str(uuid.uuid4()),"owner_email":owner_email,
        "text":text,"category":result["category"],"priority":result["priority"],
        "status":"Pending","escalation_level":1,"admin_notes":None,"created_at":now_iso()}).execute()

def get_my_grievances(email):
    return db().table("grievances").select("*").eq("owner_email",email)\
               .order("created_at",desc=True).execute().data or []

def get_all_grievances():
    return db().table("grievances").select("*").order("created_at",desc=True).execute().data or []

def update_grievance(gid, status, notes=None):
    data = {"status":status}
    if status == "Escalated": data["escalation_level"] = 2
    if notes is not None: data["admin_notes"] = notes
    db().table("grievances").update(data).eq("id",gid).execute()

# ── Auth Pages ────────────────────────────────────────────────────────────────
def page_login():
    st.markdown("""
    <div class="auth-header">
        <h1>Welcome Back</h1>
        <p>Sign in to your Grievance Redressal account</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("lf"):
        email = st.text_input("Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password")
        sub = st.form_submit_button("Login", use_container_width=True)
    if sub:
        if not email or not password:
            st.warning("Please fill in all fields."); return
        u, msg = login(email, password)
        if u:
            st.session_state.user = u
            st.session_state.chat_history = []
            st.success(msg); st.rerun()
        else:
            st.error(msg)

def page_register():
    st.markdown("""
    <div class="auth-header">
        <h1>Create Account</h1>
        <p>Register to submit and track your grievances</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("rf"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role",["employee","hr_admin","senior_admin"],
            format_func=lambda x:{"employee":"👤 Employee","hr_admin":"🟦 HR Manager (Level 1)",
                "senior_admin":"🟥 Department Head (Level 2 — Final Authority)"}[x])
        sub = st.form_submit_button("Register", use_container_width=True)
    if sub:
        if not all([name,email,password,confirm]):
            st.warning("All fields are required."); return
        if password != confirm:
            st.error("Passwords do not match."); return
        if len(password) < 6:
            st.error("Password must be at least 6 characters."); return
        ok, msg = register(name,email,password,role)
        if ok: st.success(msg)
        else: st.error(msg)

# ── Chatbot ───────────────────────────────────────────────────────────────────
def page_chatbot():
    user = st.session_state.user
    st.markdown("## 💬 Submit Grievance")
    st.caption("Describe your issue in natural language. Our AI will classify it automatically.")
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "pending_result" not in st.session_state: st.session_state.pending_result = None
    if "pending_text" not in st.session_state: st.session_state.pending_text = None

    chat_html = ('<div class="chat-container"><div class="bubble-bot">👋 Hello! I\'m your grievance assistant.<br>'
                 'Please describe your issue and I\'ll classify and file it for you.</div>')
    for msg in st.session_state.chat_history:
        tag = "bubble-user" if msg["role"]=="user" else "bubble-bot"
        chat_html += f'<div class="{tag}">{msg["text"]}</div>'
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    if st.session_state.pending_result:
        res = st.session_state.pending_result
        col1,col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm & Submit", use_container_width=True, type="primary"):
                save_grievance(user["email"], st.session_state.pending_text, res)
                st.session_state.chat_history.append({"role":"bot","text":(
                    "✅ <strong>Grievance filed successfully!</strong><br>"
                    f"Category: <span class='tag tag-category'>📁 {res['category']}</span> &nbsp;"
                    f"Priority: {priority_tag(res['priority'])}<br>"
                    "<span class='tag tag-pending'>⏳ Status: Pending</span> &nbsp;"
                    "🟦 <em>Assigned to HR Manager — Level 1</em>")})
                st.session_state.pending_result = None; st.session_state.pending_text = None
                st.rerun()
        with col2:
            if st.button("✏️ Edit / Retype", use_container_width=True):
                st.session_state.chat_history.append({"role":"bot","text":"No problem! Please retype your grievance below."})
                st.session_state.pending_result = None; st.session_state.pending_text = None
                st.rerun()
        return

    with st.form("chat_form", clear_on_submit=True):
        ci,cb = st.columns([5,1])
        with ci: user_input = st.text_input("Message",label_visibility="collapsed",placeholder="Type your grievance here...")
        with cb: sent = st.form_submit_button("Send", use_container_width=True)

    if sent and user_input.strip():
        text = user_input.strip()
        if len(text) < 15:
            st.warning("Please describe your grievance in more detail."); return
        st.session_state.chat_history.append({"role":"user","text":text})
        res = classify(text)
        conf_pct = int(res["confidence"]*100)
        conf_bar = "▓"*(conf_pct//10)+"░"*(10-conf_pct//10)
        bot_reply = (f"🔍 <strong>I've analysed your grievance.</strong><br><br>"
            f"📁 <strong>Category:</strong> <span class='tag tag-category'>{res['category']}</span><br>"
            f"🎯 <strong>Priority:</strong> {priority_tag(res['priority'])}<br>"
            f"📊 <strong>NLP Confidence:</strong> {conf_bar} {conf_pct}%<br><br>"
            "Does this look correct? Confirm to submit or edit.")
        st.session_state.chat_history.append({"role":"bot","text":bot_reply})
        st.session_state.pending_result = res; st.session_state.pending_text = text
        st.rerun()

# ── Grievance Lifecycle Flowchart ─────────────────────────────────────────────
def render_flowchart(current_status=None, is_auto=False):
    ORDER = ["Pending", "In Progress", "Escalated", "Resolved", "Closed"]
    active_idx = ORDER.index(current_status) if current_status in ORDER else -1

    def node(icon, label, sublabel, node_class, step_name):
        if active_idx == -1:
            style = icon_style = lbl_style = ""
        else:
            idx = ORDER.index(step_name) if step_name in ORDER else 99
            if idx < active_idx:
                style = "opacity:0.5; filter:saturate(0.5);"
                icon_style = lbl_style = ""
            elif idx == active_idx:
                GLOW = {
                    "Pending":     "0 0 14px #6366f1, 0 0 2px #6366f1",
                    "In Progress": "0 0 14px #22d3ee, 0 0 2px #22d3ee",
                    "Escalated":   "0 0 14px #ef4444, 0 0 2px #ef4444",
                    "Resolved":    "0 0 14px #22c55e, 0 0 2px #22c55e",
                    "Closed":      "0 0 14px #64748b, 0 0 2px #64748b",
                }
                glow = GLOW.get(step_name, "0 0 14px #60a5fa")
                style = f"box-shadow:{glow}; transform:scale(1.1); z-index:2; position:relative;"
                icon_style = "font-size:28px;"
                lbl_style = "font-weight:700; font-size:14px;"
            else:
                style = "opacity:0.18; filter:grayscale(1);"
                icon_style = lbl_style = ""
        return (
            f'<div class="flow-node {node_class}" style="{style}">'
            f'<div class="icon" style="{icon_style}">{icon}</div>'
            f'<div class="label" style="{lbl_style}">{label}</div>'
            f'<div class="sublabel">{sublabel}</div></div>'
        )

    def arrow(label="", step_name=None):
        future = (active_idx != -1 and step_name in ORDER and ORDER.index(step_name) > active_idx)
        color = "#1e293b" if future else "#475569"
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;padding:0 4px;">'
            f'<div class="flow-arrow" style="color:{color}">→</div>'
            f'<div style="font-size:10px;color:{color};">{label}</div></div>'
        )

    nodes = {
        "Pending":     ("⏳","Pending",    "Submitted",          "flow-node-pending"),
        "In Progress": ("🔧","In Progress","HR Reviewing",       "flow-node-progress"),
        "Escalated":   ("🚨","Escalated",  "Dept Head",          "flow-node-escalated"),
        "Resolved":    ("✅","Resolved",   "Closed by Authority","flow-node-resolved"),
        "Closed":      ("🔒","Closed",     "Finalised",          "flow-node-closed"),
    }

    html = '<div class="flow-container">'
    html += node(*nodes["Pending"],     step_name="Pending")
    html += arrow("HR assigned",        step_name="In Progress")
    html += node(*nodes["In Progress"], step_name="In Progress")

    # Escalation arrow
    esc_future = active_idx != -1 and ORDER.index("Escalated") > active_idx
    ac = "#1e293b" if esc_future else ("#f97316" if is_auto else "#475569")
    lc = "#1e293b" if esc_future else ("#f97316" if is_auto else "#475569")
    albl = "⚡ Auto (24h)" if (is_auto and not esc_future) else "HR escalates"
    html += (
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;padding:0 4px;">'
        f'<div class="flow-arrow" style="color:{ac}">→</div>'
        f'<div style="font-size:10px;color:{lc};font-weight:{"600" if is_auto else "400"};">{albl}</div></div>'
    )

    if is_auto and current_status == "Escalated":
        html += (
            f'<div class="flow-node flow-node-auto" style="border:2px solid #f97316;'
            f'box-shadow:0 0 14px #f97316;transform:scale(1.1);z-index:2;position:relative;">'
            f'<div class="icon">⚡</div>'
            f'<div class="label" style="color:#fb923c;font-weight:700;">Auto-Escalated</div>'
            f'<div class="sublabel">No action in {ESCALATION_HOURS}h</div></div>'
        )
    else:
        html += node(*nodes["Escalated"], step_name="Escalated")

    html += arrow("Dept Head", step_name="Resolved")
    html += node(*nodes["Resolved"],    step_name="Resolved")
    html += arrow("",                   step_name="Closed")
    html += node(*nodes["Closed"],      step_name="Closed")
    html += '</div>'
    return html

# ── Grievance Tracking Page ───────────────────────────────────────────────────
def page_tracking(grievances, is_admin=False):
    st.markdown("### 🔍 Grievance Tracking")
    st.caption("Track status, priority distribution, lifecycle and history of grievances.")

    if not grievances:
        st.info("No grievances to track yet.")
        return

    from collections import Counter

    # ── Section 1: Pie Charts ─────────────────────────────────────────────────
    st.markdown("#### Distribution Overview")
    pc1, pc2 = st.columns(2)

    with pc1:
        st.markdown("**Status Breakdown**")
        sc = Counter(g["status"] for g in grievances)
        sd = {k:v for k,v in sc.items() if v>0}
        fig1 = go.Figure(go.Pie(
            labels=list(sd.keys()), values=list(sd.values()), hole=0.48,
            marker=dict(colors=["#6366f1","#22d3ee","#ef4444","#22c55e","#64748b"]),
            textinfo="label+value+percent", textfont=dict(size=12,color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"))
        fig1.update_layout(**chart_bg(), height=300, showlegend=False,
            annotations=[dict(text=f"<b>{len(grievances)}</b>",x=0.5,y=0.5,
                              font=dict(size=18,color="white"),showarrow=False)])
        st.plotly_chart(fig1, use_container_width=True)

    with pc2:
        st.markdown("**Priority Breakdown**")
        pc = Counter(g["priority"] for g in grievances)
        pd2 = {k:v for k,v in pc.items() if v>0}
        fig2 = go.Figure(go.Pie(
            labels=list(pd2.keys()), values=list(pd2.values()), hole=0.48,
            marker=dict(colors=["#ef4444","#f59e0b","#22c55e"]),
            textinfo="label+value+percent", textfont=dict(size=12,color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"))
        fig2.update_layout(**chart_bg(), height=300, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Section 3: Timeline ───────────────────────────────────────────────────
    st.markdown("#### Grievance Timeline")
    st.caption("Visual history of when each grievance was submitted, ordered by time.")

    # Sort by created_at ascending for timeline
    sorted_g = sorted(grievances, key=lambda x: x["created_at"])

    STATUS_COLORS = {
        "Pending":     "#6366f1",
        "In Progress": "#22d3ee",
        "Escalated":   "#ef4444",
        "Resolved":    "#22c55e",
        "Closed":      "#64748b",
    }
    PRI_SYMBOLS = {"High": "star", "Medium": "circle", "Low": "circle-open"}

    x_dates, y_labels, colors, symbols, hover_texts, sizes = [], [], [], [], [], []

    for i, g in enumerate(sorted_g):
        x_dates.append(g["created_at"][:16])
        short = g["text"][:35] + ("..." if len(g["text"]) > 35 else "")
        y_labels.append(f"#{g['id'][:6].upper()}")
        colors.append(STATUS_COLORS.get(g["status"], "#64748b"))
        symbols.append(PRI_SYMBOLS.get(g["priority"], "circle"))
        is_auto = g.get("admin_notes") and "Auto-escalated" in g.get("admin_notes","")
        hover_texts.append(
            f"<b>{short}</b><br>"
            f"Status: {g['status']}<br>"
            f"Priority: {g['priority']}<br>"
            f"Category: {g['category']}<br>"
            f"Level: {'L2 ⚡ Auto' if is_auto else ('L' + str(g['escalation_level']))}<br>"
            f"Date: {g['created_at'][:16]}"
        )
        sizes.append(16 if g["priority"] == "High" else 12)

    fig_tl = go.Figure()

    # Draw connecting line
    fig_tl.add_trace(go.Scatter(
        x=x_dates, y=y_labels,
        mode="lines",
        line=dict(color="rgba(100,116,139,0.3)", width=2, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))

    # Draw points per status (for legend grouping)
    for status, color in STATUS_COLORS.items():
        idxs = [i for i,g in enumerate(sorted_g) if g["status"]==status]
        if not idxs: continue
        fig_tl.add_trace(go.Scatter(
            x=[x_dates[i] for i in idxs],
            y=[y_labels[i] for i in idxs],
            mode="markers",
            name=status,
            marker=dict(
                color=color, size=[sizes[i] for i in idxs],
                symbol=[symbols[i] for i in idxs],
                line=dict(color="white", width=1.5),
            ),
            hovertemplate=[hover_texts[i] + "<extra></extra>" for i in idxs],
        ))

    fig_tl.update_layout(
        **chart_bg(),
        height=max(280, len(sorted_g) * 38),
        xaxis=dict(
            title="Submission Date",
            tickfont=dict(color="#94a3b8", size=11),
            gridcolor="rgba(255,255,255,0.05)",
            showgrid=True,
        ),
        yaxis=dict(
            tickfont=dict(color="#94a3b8", size=11),
            gridcolor="rgba(255,255,255,0.05)",
        ),
        legend=dict(
            font=dict(color="white", size=11),
            bgcolor="rgba(30,41,59,0.8)",
            bordercolor="#334155",
            borderwidth=1,
            title=dict(text="Status", font=dict(color="#94a3b8")),
        ),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12, font_color="white"),
    )

    # Legend for priority shape
    st.plotly_chart(fig_tl, use_container_width=True)
    st.caption("⭐ Star = High priority &nbsp;&nbsp; ● Filled = Medium &nbsp;&nbsp; ○ Outline = Low")

    st.divider()

    # ── Section 4: Individual Grievance Tracker ───────────────────────────────
    st.markdown("#### Individual Grievance Tracker")
    st.caption("Select a grievance to see its exact position in the lifecycle.")

    options = {f"#{g['id'][:8].upper()} — {g['text'][:50]}": g for g in grievances}
    selected_key = st.selectbox("Select Grievance", list(options.keys()), key="track_sel")

    if selected_key:
        g = options[selected_key]
        is_auto = g.get("admin_notes") and "Auto-escalated" in g.get("admin_notes","")

        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f'''<div class="metric-card"><div class="metric-num" style="font-size:15px;">{g["category"]}</div><div class="metric-lbl">Category</div></div>''', unsafe_allow_html=True)
        c2.markdown(f'''<div class="metric-card"><div class="metric-num" style="font-size:15px;">{priority_tag(g["priority"])}</div><div class="metric-lbl">Priority</div></div>''', unsafe_allow_html=True)
        c3.markdown(f'''<div class="metric-card"><div class="metric-num" style="font-size:15px;">{status_pill(g["status"])}</div><div class="metric-lbl">Current Status</div></div>''', unsafe_allow_html=True)
        lvl_label = f"Level {g['escalation_level']} ⚡" if is_auto else f"Level {g['escalation_level']}"
        c4.markdown(f'''<div class="metric-card"><div class="metric-num" style="font-size:15px;">{lvl_label}</div><div class="metric-lbl">Escalation Level</div></div>''', unsafe_allow_html=True)

        st.markdown(render_flowchart(current_status=g["status"], is_auto=bool(is_auto)), unsafe_allow_html=True)

        if g.get("admin_notes"):
            st.markdown(f'''<div class="admin-note">📝 <strong>Admin Note:</strong> {g["admin_notes"]}</div>''', unsafe_allow_html=True)


# ── Employee Page ─────────────────────────────────────────────────────────────
def page_employee():
    user = st.session_state.user
    grievances = get_my_grievances(user["email"])

    tab1, tab2, tab3 = st.tabs(["📋 My Grievances", "🔍 Track Grievances", "💬 Submit New"])

    with tab1:
        st.markdown(f"""
        <div class="page-header">
            <h2>My Grievances</h2>
            <p>Welcome back, <strong>{user['name'].strip()}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        total=len(grievances); pending=sum(1 for g in grievances if g["status"]=="Pending")
        resolved=sum(1 for g in grievances if g["status"]=="Resolved")
        escalated=sum(1 for g in grievances if g["status"]=="Escalated")
        for col,num,label in zip(st.columns(4),[total,pending,resolved,escalated],
                                               ["Total","Pending","Resolved","Escalated"]):
            col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div>'
                        f'<div class="metric-lbl">{label}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not grievances:
            st.info("You haven't submitted any grievances yet. Use the Submit New tab.")
        else:
            for g in grievances:
                is_auto = g.get("admin_notes") and "Auto-escalated" in g.get("admin_notes","")
                if g["escalation_level"] == 2:
                    lvl = ("&nbsp;<span style='font-size:11px;color:#fb923c;'>⚡ Auto-Escalated → Dept Head (Level 2)</span>"
                           if is_auto else
                           "&nbsp;<span style='font-size:11px;color:#f87171;'>🟥 With Dept Head (Level 2)</span>")
                else:
                    lvl = "&nbsp;<span style='font-size:11px;color:#93c5fd;'>🟦 With HR Manager (Level 1)</span>"
                note = (f'<div class="admin-note">📝 <strong>Admin Note:</strong> {g["admin_notes"]}</div>'
                        if g.get("admin_notes") else "")
                st.markdown(f"""<div class="grievance-card">
                    <div class="grievance-id">#{g['id'][:8].upper()} &nbsp;·&nbsp; {g['created_at'][:16]}</div>
                    <div class="grievance-text">{g['text']}</div>
                    <div class="grievance-meta"><span class="tag tag-category">📁 {g['category']}</span>
                    &nbsp;{priority_tag(g['priority'])} &nbsp;{status_pill(g['status'])}{lvl}</div>
                    {note}</div>""", unsafe_allow_html=True)

    with tab2:
        page_tracking(grievances, is_admin=False)

    with tab3:
        page_chatbot()

# ── Analytics Dashboard ───────────────────────────────────────────────────────
def page_dashboard():
    st.markdown("### 📊 Analytics Dashboard")
    all_g = get_all_grievances()
    if not all_g:
        st.info("No grievance data available yet."); return

    total=len(all_g); pending=sum(1 for g in all_g if g["status"]=="Pending")
    progress=sum(1 for g in all_g if g["status"]=="In Progress")
    escalated=sum(1 for g in all_g if g["status"]=="Escalated")
    resolved=sum(1 for g in all_g if g["status"]=="Resolved")
    closed=sum(1 for g in all_g if g["status"]=="Closed")
    high_p=sum(1 for g in all_g if g["priority"]=="High")
    lvl2=sum(1 for g in all_g if g["escalation_level"]==2); lvl1=total-lvl2

    for col,num,label,color in zip(st.columns(6),
        [total,pending,progress,escalated,resolved,high_p],
        ["Total","Pending","In Progress","Escalated","Resolved","High Priority"],
        ["#60a5fa","#a5b4fc","#6ee7b7","#fca5a5","#86efac","#f87171"]):
        col.markdown(f'<div class="metric-card"><div class="metric-num" style="color:{color}">{num}</div>'
                    f'<div class="metric-lbl">{label}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1,col2 = st.columns(2)
    with col1:
        st.markdown("#### Status Distribution")
        sd={k:v for k,v in {"Pending":pending,"In Progress":progress,"Escalated":escalated,"Resolved":resolved,"Closed":closed}.items() if v>0}
        fig1=go.Figure(go.Pie(labels=list(sd.keys()),values=list(sd.values()),hole=0.52,
            marker=dict(colors=["#6366f1","#22d3ee","#f59e0b","#22c55e","#64748b"]),
            textinfo="label+percent",textfont=dict(size=12,color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"))
        fig1.update_layout(**chart_bg(),height=320,showlegend=True,
            legend=dict(font=dict(color="white"),bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text=f"<b>{total}</b><br>Total",x=0.5,y=0.5,font=dict(size=15,color="white"),showarrow=False)])
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("#### Priority Breakdown")
        hi=sum(1 for g in all_g if g["priority"]=="High")
        me=sum(1 for g in all_g if g["priority"]=="Medium")
        lo=sum(1 for g in all_g if g["priority"]=="Low")
        pd2={k:v for k,v in {"High":hi,"Medium":me,"Low":lo}.items() if v>0}
        fig2=go.Figure(go.Pie(labels=list(pd2.keys()),values=list(pd2.values()),hole=0.52,
            marker=dict(colors=["#ef4444","#f59e0b","#22c55e"]),
            textinfo="label+percent",textfont=dict(size=12,color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"))
        fig2.update_layout(**chart_bg(),height=320,showlegend=True,
            legend=dict(font=dict(color="white"),bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Grievances by Category")
    cat_counts=Counter(g["category"] for g in all_g)
    cats=list(cat_counts.keys()); cnts=list(cat_counts.values())
    COLORS=["#3b82f6","#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b"]
    fig3=go.Figure(go.Bar(x=cats,y=cnts,
        marker=dict(color=COLORS[:len(cats)],line=dict(color="rgba(255,255,255,0.1)",width=1)),
        text=cnts,textposition="outside",textfont=dict(color="white",size=13),
        hovertemplate="<b>%{x}</b><br>Grievances: %{y}<extra></extra>"))
    fig3.update_layout(**chart_bg(),height=320,
        xaxis=dict(tickfont=dict(color="white"),gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(tickfont=dict(color="white"),gridcolor="rgba(255,255,255,0.08)"))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Escalation Level Split")
    fig5=go.Figure(go.Bar(x=["🟦 Level 1\n(HR Manager)","🟥 Level 2\n(Dept Head)"],y=[lvl1,lvl2],
        marker=dict(color=["#3b82f6","#ef4444"]),text=[lvl1,lvl2],textposition="outside",
        textfont=dict(color="white",size=16),hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"))
    fig5.update_layout(**chart_bg(),height=300,
        xaxis=dict(tickfont=dict(color="white",size=12)),
        yaxis=dict(tickfont=dict(color="white"),gridcolor="rgba(255,255,255,0.08)"))
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("#### Resolution & Escalation Rates")
    res_rate=round((resolved+closed)/total*100,1) if total else 0
    esc_rate=round(lvl2/total*100,1) if total else 0
    pen_rate=round((pending+progress)/total*100,1) if total else 0
    for col,val,label,color in zip(st.columns(3),
        [res_rate,esc_rate,pen_rate],
        ["Resolution Rate %","Escalation Rate %","Pending Rate %"],
        ["#22c55e","#ef4444","#f59e0b"]):
        fg=go.Figure(go.Indicator(mode="gauge+number",value=val,
            number=dict(suffix="%",font=dict(color="white",size=28)),
            gauge=dict(axis=dict(range=[0,100],tickfont=dict(color="white")),bar=dict(color=color),
                bgcolor="rgba(255,255,255,0.05)",bordercolor="rgba(255,255,255,0.1)",
                steps=[dict(range=[0,33],color="rgba(255,255,255,0.03)"),
                       dict(range=[33,66],color="rgba(255,255,255,0.05)"),
                       dict(range=[66,100],color="rgba(255,255,255,0.07)")]),
            title=dict(text=label,font=dict(color="#94a3b8",size=13))))
        fg.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="white"),
                         margin=dict(t=50,b=10,l=20,r=20),height=230)
        col.plotly_chart(fg, use_container_width=True)

# ── HR Manager Panel ──────────────────────────────────────────────────────────
# ── Analytics & Insights (Admin shared) ──────────────────────────────────────

def page_admin_analytics(all_g, role="hr"):
    """
    Merged Analytics + Grievance Table for HR Manager and Department Head.
    role = "hr"  → shows Level 1 stats + all-org charts
    role = "senior" → shows Level 2 stats + all-org charts
    """
    from collections import Counter

    if not all_g:
        st.info("No grievance data available yet.")
        return

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    total     = len(all_g)
    pending   = sum(1 for g in all_g if g["status"] == "Pending")
    progress  = sum(1 for g in all_g if g["status"] == "In Progress")
    escalated = sum(1 for g in all_g if g["status"] == "Escalated")
    resolved  = sum(1 for g in all_g if g["status"] == "Resolved")
    closed    = sum(1 for g in all_g if g["status"] == "Closed")
    high_p    = sum(1 for g in all_g if g["priority"] == "High")
    lvl2      = sum(1 for g in all_g if g["escalation_level"] == 2)
    lvl1      = total - lvl2
    auto_esc  = sum(1 for g in all_g if g.get("admin_notes") and "Auto-escalated" in g.get("admin_notes",""))

    st.markdown("#### Organisation-wide Overview")
    for col, num, label, color in zip(
        st.columns(6),
        [total, pending, progress, escalated, resolved, high_p],
        ["Total", "Pending", "In Progress", "Escalated", "Resolved", "High Priority"],
        ["#60a5fa","#a5b4fc","#6ee7b7","#fca5a5","#86efac","#f87171"],
    ):
        col.markdown(
            f'<div class="metric-card"><div class="metric-num" style="color:{color}">{num}</div>'
            f'<div class="metric-lbl">{label}</div></div>',
            unsafe_allow_html=True,
        )

    # Auto-escalation callout
    if auto_esc > 0:
        st.warning(f"⚡ **{auto_esc}** grievance(s) were auto-escalated due to no action within {ESCALATION_HOURS} hour(s).")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 1: Status donut + Priority donut ────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Status Distribution")
        sd = {k:v for k,v in {"Pending":pending,"In Progress":progress,
              "Escalated":escalated,"Resolved":resolved,"Closed":closed}.items() if v>0}
        fig1 = go.Figure(go.Pie(
            labels=list(sd.keys()), values=list(sd.values()), hole=0.52,
            marker=dict(colors=["#6366f1","#22d3ee","#f59e0b","#22c55e","#64748b"]),
            textinfo="label+percent", textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        ))
        fig1.update_layout(**chart_bg(), height=300, showlegend=True,
            legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text=f"<b>{total}</b><br>Total", x=0.5, y=0.5,
                               font=dict(size=15, color="white"), showarrow=False)])
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown("#### Priority Breakdown")
        hi = sum(1 for g in all_g if g["priority"]=="High")
        me = sum(1 for g in all_g if g["priority"]=="Medium")
        lo = sum(1 for g in all_g if g["priority"]=="Low")
        pd2 = {k:v for k,v in {"High":hi,"Medium":me,"Low":lo}.items() if v>0}
        fig2 = go.Figure(go.Pie(
            labels=list(pd2.keys()), values=list(pd2.values()), hole=0.52,
            marker=dict(colors=["#ef4444","#f59e0b","#22c55e"]),
            textinfo="label+percent", textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        ))
        fig2.update_layout(**chart_bg(), height=300, showlegend=True,
            legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Charts Row 2: Category bar ─────────────────────────────────────────────
    st.markdown("#### Grievances by Category")
    cat_counts = Counter(g["category"] for g in all_g)
    cats = list(cat_counts.keys()); cnts = list(cat_counts.values())
    COLORS = ["#3b82f6","#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b"]
    fig3 = go.Figure(go.Bar(
        x=cats, y=cnts,
        marker=dict(color=COLORS[:len(cats)], line=dict(color="rgba(255,255,255,0.1)", width=1)),
        text=cnts, textposition="outside", textfont=dict(color="white", size=13),
        hovertemplate="<b>%{x}</b><br>Grievances: %{y}<extra></extra>",
    ))
    fig3.update_layout(**chart_bg(), height=300,
        xaxis=dict(tickfont=dict(color="white"), gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(tickfont=dict(color="white"), gridcolor="rgba(255,255,255,0.08)"))
    st.plotly_chart(fig3, use_container_width=True)

    # ── Charts Row 3: Level split + Gauges ────────────────────────────────────
    c3, c4 = st.columns([1, 2])
    with c3:
        st.markdown("#### Escalation Level Split")
        fig4 = go.Figure(go.Bar(
            x=["🟦 L1 (HR)", "🟥 L2 (Dept Head)"],
            y=[lvl1, lvl2],
            marker=dict(color=["#3b82f6","#ef4444"]),
            text=[lvl1, lvl2], textposition="outside",
            textfont=dict(color="white", size=15),
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        ))
        fig4.update_layout(**chart_bg(), height=300,
            xaxis=dict(tickfont=dict(color="white")),
            yaxis=dict(tickfont=dict(color="white"), gridcolor="rgba(255,255,255,0.08)"))
        st.plotly_chart(fig4, use_container_width=True)

    with c4:
        st.markdown("#### Resolution & Escalation Rates")
        res_rate = round((resolved+closed)/total*100,1) if total else 0
        esc_rate = round(lvl2/total*100,1) if total else 0
        pen_rate = round((pending+progress)/total*100,1) if total else 0
        for col, val, label, color in zip(
            st.columns(3),
            [res_rate, esc_rate, pen_rate],
            ["Resolved %", "Escalated %", "Pending %"],
            ["#22c55e","#ef4444","#f59e0b"],
        ):
            fg = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                number=dict(suffix="%", font=dict(color="white", size=26)),
                gauge=dict(
                    axis=dict(range=[0,100], tickfont=dict(color="white")),
                    bar=dict(color=color),
                    bgcolor="rgba(255,255,255,0.05)",
                    bordercolor="rgba(255,255,255,0.1)",
                    steps=[
                        dict(range=[0,33],  color="rgba(255,255,255,0.03)"),
                        dict(range=[33,66], color="rgba(255,255,255,0.05)"),
                        dict(range=[66,100],color="rgba(255,255,255,0.07)"),
                    ],
                ),
                title=dict(text=label, font=dict(color="#94a3b8", size=12)),
            ))
            fg.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                             margin=dict(t=50,b=10,l=10,r=10), height=220)
            col.plotly_chart(fg, use_container_width=True)

    st.divider()

    # ── Grievance Table ────────────────────────────────────────────────────────
    st.markdown("#### Grievance Table")
    st.caption("Filter, search and inspect all grievances in one place.")

    tf1, tf2, tf3 = st.columns(3)
    key_sfx = role  # unique selectbox keys per role
    with tf1: sf = st.selectbox("Status",   ["All","Pending","In Progress","Escalated","Resolved","Closed"], key=f"ai_sf_{key_sfx}")
    with tf2: pf = st.selectbox("Priority", ["All","High","Medium","Low"], key=f"ai_pf_{key_sfx}")
    with tf3: lf = st.selectbox("Level",    ["All","Level 1 (HR)","Level 2 (Dept Head)"], key=f"ai_lf_{key_sfx}")

    filtered = all_g
    if sf != "All": filtered = [g for g in filtered if g["status"]   == sf]
    if pf != "All": filtered = [g for g in filtered if g["priority"] == pf]
    if lf == "Level 1 (HR)":         filtered = [g for g in filtered if g["escalation_level"] == 1]
    if lf == "Level 2 (Dept Head)":  filtered = [g for g in filtered if g["escalation_level"] == 2]

    st.caption(f"Showing **{len(filtered)}** of **{len(all_g)}** grievance(s)")

    if not filtered:
        st.info("No grievances match the selected filters.")
        return

    rows = []
    for g in filtered:
        is_auto = g.get("admin_notes") and "Auto-escalated" in g.get("admin_notes","")
        rows.append({
            "ID":        f"#{g['id'][:8].upper()}",
            "Date":      g["created_at"][:16],
            "Employee":  g["owner_email"],
            "Grievance": g["text"][:55] + ("..." if len(g["text"])>55 else ""),
            "Category":  g["category"],
            "Priority":  g["priority"],
            "Status":    g["status"],
            "Level":     f"L{g['escalation_level']} {'⚡' if is_auto else ''}",
        })

    import pandas as pd
    df = pd.DataFrame(rows)

    def color_status(val):
        return {"Pending":"background-color:#312e81;color:#a5b4fc",
                "In Progress":"background-color:#1c3a2a;color:#6ee7b7",
                "Escalated":"background-color:#7f1d1d;color:#fca5a5",
                "Resolved":"background-color:#14532d;color:#86efac",
                "Closed":"background-color:#1e293b;color:#64748b"}.get(val,"")

    def color_priority(val):
        return {"High":"background-color:#7f1d1d;color:#fca5a5",
                "Medium":"background-color:#78350f;color:#fcd34d",
                "Low":"background-color:#14532d;color:#86efac"}.get(val,"")

    styled = df.style.applymap(color_status, subset=["Status"])                     .applymap(color_priority, subset=["Priority"])
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ── HR Manager Panel ──────────────────────────────────────────────────────────

def page_hr_admin():
    st.markdown("""
    <div class="page-header">
        <h2>🟦 HR Manager Panel</h2>
        <p>Review, manage and escalate employee grievances — Level 1</p>
    </div>
    """, unsafe_allow_html=True)
    tab_manage, tab_analytics = st.tabs(["📋 Manage Grievances", "📊 Analytics & Insights"])

    with tab_analytics:
        page_admin_analytics(get_all_grievances(), role="hr")

    with tab_manage:
        st.markdown("""
        <div class="level1-banner">
            <strong>Level 1 — HR Manager</strong> &nbsp;|&nbsp;
            🟢 <strong>Low / Medium</strong> priority: You can resolve directly.<br>
            🔴 <strong>High</strong> priority: Must be escalated to Department Head (Level 2).
        </div>
        """, unsafe_allow_html=True)

        all_g = get_all_grievances()
        grievances = [g for g in all_g if g["escalation_level"] == 1]

        total=len(grievances); pending=sum(1 for g in grievances if g["status"]=="Pending")
        progress=sum(1 for g in grievances if g["status"]=="In Progress")
        escalated=sum(1 for g in grievances if g["status"]=="Escalated")
        for col,num,label in zip(st.columns(4),
            [total,pending,progress,escalated],
            ["Total Assigned","Pending","In Progress","Escalated to L2"]):
            col.markdown(
                f'<div class="metric-card"><div class="metric-num">{num}</div>'
                f'<div class="metric-lbl">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        fc1,fc2 = st.columns(2)
        with fc1: sf = st.selectbox("Filter by Status", ["All","Pending","In Progress","Escalated"])
        with fc2: pf = st.selectbox("Filter by Priority", ["All","High","Medium","Low"])
        if sf != "All": grievances = [g for g in grievances if g["status"]   == sf]
        if pf != "All": grievances = [g for g in grievances if g["priority"] == pf]
        st.caption(f"Showing {len(grievances)} grievance(s)"); st.divider()

        if not grievances:
            st.info("No grievances match the selected filters."); return

        for g in grievances:
            if g["priority"] == "High":
                ALLOWED = ["Pending","In Progress","Escalated"]
                rule = "🔴 High priority — must escalate to Department Head."
            else:
                ALLOWED = ["Pending","In Progress","Resolved","Escalated"]
                rule = f"🟢 {g['priority']} priority — you may resolve this directly."
            with st.container():
                st.markdown(f"""<div class="grievance-card">
                    <div class="grievance-id">#{g['id'][:8].upper()} &nbsp;·&nbsp; {g['owner_email']} &nbsp;·&nbsp; {g['created_at'][:16]}</div>
                    <div class="grievance-text">{g['text']}</div>
                    <div class="grievance-meta"><span class="tag tag-category">📁 {g['category']}</span>
                    &nbsp;{priority_tag(g['priority'])} &nbsp;{status_pill(g['status'])}</div>
                </div>""", unsafe_allow_html=True)
                with st.expander("⚙️ Update this grievance"):
                    st.caption(rule)
                    cs,cn = st.columns([1,2])
                    with cs:
                        idx = ALLOWED.index(g["status"]) if g["status"] in ALLOWED else 0
                        ns  = st.selectbox("Set Status", ALLOWED, index=idx, key=f"hs_{g['id']}")
                        if ns == "Escalated":
                            st.warning("⬆ Will forward to Department Head (Level 2).")
                    with cn:
                        nn = st.text_area("Notes for employee", value=g.get("admin_notes") or "",
                                          key=f"hn_{g['id']}", height=80)
                    if st.button("💾 Save Changes", key=f"hsv_{g['id']}", type="primary"):
                        if ns == "Resolved" and g["priority"] == "High":
                            st.error("❌ High priority must be escalated to Department Head.")
                        else:
                            update_grievance(g["id"], ns, nn); st.success("✅ Updated!"); st.rerun()


# ── Department Head Panel ─────────────────────────────────────────────────────

def page_senior_admin():
    st.markdown("""
    <div class="page-header">
        <h2>🟥 Department Head Panel</h2>
        <p>Final authority on escalated grievances — Level 2</p>
    </div>
    """, unsafe_allow_html=True)
    tab_manage, tab_analytics = st.tabs(["📋 Final Decisions", "📊 Analytics & Insights"])

    with tab_analytics:
        page_admin_analytics(get_all_grievances(), role="senior")

    with tab_manage:
        st.markdown("""
        <div class="level2-banner">
            <strong>Level 2 — Final Authority</strong> &nbsp;|&nbsp;
            You see only grievances escalated by HR Manager.<br>
            Your decision is <strong>final</strong>. Resolve or Close. No further escalation.
        </div>
        """, unsafe_allow_html=True)

        all_g = get_all_grievances()
        grievances = [g for g in all_g if g["escalation_level"] == 2]

        total=len(grievances); awaiting=sum(1 for g in grievances if g["status"]=="Escalated")
        resolved=sum(1 for g in grievances if g["status"]=="Resolved")
        closed=sum(1 for g in grievances if g["status"]=="Closed")
        for col,num,label in zip(st.columns(4),
            [total,awaiting,resolved,closed],
            ["Total Escalated","Awaiting Decision","Resolved","Closed"]):
            col.markdown(
                f'<div class="metric-card"><div class="metric-num">{num}</div>'
                f'<div class="metric-lbl">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not grievances:
            st.info("✅ No escalated grievances at this time."); return

        pf = st.selectbox("Filter by Priority", ["All","High","Medium","Low"])
        if pf != "All": grievances = [g for g in grievances if g["priority"] == pf]
        st.caption(f"Showing {len(grievances)} escalated grievance(s)"); st.divider()

        SENIOR_STATUSES = ["Escalated","Resolved","Closed"]
        for g in grievances:
            with st.container():
                st.markdown(f"""<div class="grievance-card" style="border-left:3px solid #ef4444;">
                    <div class="grievance-id">#{g['id'][:8].upper()} &nbsp;·&nbsp; {g['owner_email']} &nbsp;·&nbsp; {g['created_at'][:16]}
                    &nbsp;<span style="color:#f87171;font-size:11px;">⬆ Escalated</span></div>
                    <div class="grievance-text">{g['text']}</div>
                    <div class="grievance-meta"><span class="tag tag-category">📁 {g['category']}</span>
                    &nbsp;{priority_tag(g['priority'])} &nbsp;{status_pill(g['status'])}</div>
                </div>""", unsafe_allow_html=True)
                with st.expander("⚙️ Give Final Decision"):
                    cs,cn = st.columns([1,2])
                    with cs:
                        idx = SENIOR_STATUSES.index(g["status"]) if g["status"] in SENIOR_STATUSES else 0
                        ns  = st.selectbox("Final Status", SENIOR_STATUSES, index=idx, key=f"ss_{g['id']}")
                        st.caption("No further escalation at Level 2.")
                    with cn:
                        nn = st.text_area("Resolution note", value=g.get("admin_notes") or "",
                                          key=f"sn_{g['id']}", height=80)
                    if st.button("✅ Submit Final Decision", key=f"ssv_{g['id']}", type="primary"):
                        update_grievance(g["id"], ns, nn); st.success("✅ Decision recorded!"); st.rerun()

def sidebar():
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown("""
        <div class="sidebar-logo">
            <div class="logo-icon">⚖️</div>
            <div>
                <div class="logo-text">GrievanceIQ</div>
                <div class="logo-sub">AI-Powered Redressal System</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Not logged in ─────────────────────────────────────────────────────
        if "user" not in st.session_state:
            page = st.radio("", ["🔐 Login", "📝 Register"], label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="sidebar-info">
                <div class="info-label">Escalation Structure</div>
                <div class="info-row">🟦 <span>Level 1 — HR Manager</span></div>
                <div class="info-row">🟥 <span>Level 2 — Department Head</span></div>
            </div>
            <div class="sidebar-info">
                <div class="info-label">Auto-Escalation</div>
                <div class="info-row">⚡ <span>Unresolved after 24h → auto-forwarded to Dept Head</span></div>
            </div>
            """, unsafe_allow_html=True)
            return page

        # ── Logged in: user card ───────────────────────────────────────────────
        u = st.session_state.user
        role_icon = {"employee":"👤","hr_admin":"🟦","senior_admin":"🟥"}.get(u["role"],"👤")
        role_name = {"employee":"Employee","hr_admin":"HR Manager — Level 1","senior_admin":"Department Head — Level 2"}.get(u["role"],u["role"])

        st.markdown(f"""
        <div class="sidebar-user">
            <div class="user-name">{u["name"].strip()}</div>
            <div class="user-role">{role_icon} {role_name}</div>
            <div class="user-email">{u["email"]}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Sign Out", use_container_width=True):
            for k in ["user","chat_history","pending_result","pending_text"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Info cards ─────────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="sidebar-info">
            <div class="info-label">Priority Levels</div>
            <div class="info-row">🔴 <span>High — Immediate action</span></div>
            <div class="info-row">🟡 <span>Medium — Within 48h</span></div>
            <div class="info-row">🟢 <span>Low — Standard queue</span></div>
        </div>
        <div class="sidebar-info">
            <div class="info-label">Auto-Escalation Policy</div>
            <div class="info-row">⚡ <span>No HR action in <strong>{ESCALATION_HOURS}h</strong> → auto-forwarded to Department Head</span></div>
        </div>
        """, unsafe_allow_html=True)

        return None

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    page = sidebar()
    if "user" in st.session_state:
        count = run_auto_escalation()
        if count > 0:
            st.toast(f"⚡ {count} grievance(s) auto-escalated after {ESCALATION_HOURS}h with no action.", icon="🚨")
    if "user" not in st.session_state:
        if page=="🔐 Login": page_login()
        else: page_register()
    else:
        role=st.session_state.user["role"]
        if role=="hr_admin": page_hr_admin()
        elif role=="senior_admin": page_senior_admin()
        else: page_employee()

if __name__=="__main__":
    main()