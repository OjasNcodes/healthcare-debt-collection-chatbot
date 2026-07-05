"""
app.py — Streamlit entry point for the Healthcare Collections Chatbot.
"""

import json
import os
import streamlit as st
from dotenv import load_dotenv
from chatbot import ChatSession, State

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MedCare Collections Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — premium dark-theme design
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255,255,255,0.08);
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #e2e8f0 !important;
}

/* ── Input fields ── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(129,140,248,0.2) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.3px !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102,126,234,0.4) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Chat messages ── */
.chat-wrapper {
    max-width: 820px;
    margin: 0 auto;
    padding: 1rem 0 6rem 0;
}

.chat-header {
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1.5rem;
}

.chat-header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}

.chat-header p {
    color: #94a3b8;
    margin: 0.4rem 0 0;
    font-size: 0.9rem;
}

.message-bubble {
    display: flex;
    margin-bottom: 1rem;
    animation: fadeSlideIn 0.3s ease forwards;
}

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.message-bubble.user {
    justify-content: flex-end;
}

.message-bubble.assistant {
    justify-content: flex-start;
}

.bubble-content {
    max-width: 72%;
    padding: 0.85rem 1.1rem;
    border-radius: 18px;
    line-height: 1.6;
    font-size: 0.93rem;
}

.user .bubble-content {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-bottom-right-radius: 4px;
    box-shadow: 0 4px 15px rgba(102,126,234,0.3);
}

.assistant .bubble-content {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0;
    border-bottom-left-radius: 4px;
    backdrop-filter: blur(10px);
}

.avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    margin-top: 2px;
}

.assistant .avatar {
    background: linear-gradient(135deg, #667eea, #764ba2);
    margin-right: 10px;
}

.user .avatar {
    background: rgba(255,255,255,0.1);
    margin-left: 10px;
    order: 1;
}

/* ── Status badge ── */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
}

.status-active   { background: rgba(34,197,94,0.15);  color: #4ade80; border: 1px solid rgba(74,222,128,0.3); }
.status-closed   { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(129,140,248,0.3); }
.status-failed   { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(248,113,113,0.3); }

/* ── Session summary ── */
.summary-container {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 1.5rem;
    backdrop-filter: blur(10px);
}

.summary-container h3 {
    color: #a78bfa !important;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 1rem;
    letter-spacing: 0.3px;
}

.stCodeBlock {
    border-radius: 12px !important;
}

/* ── Input area at bottom ── */
.stChatInput {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
}

/* ── Selectbox / number input labels ── */
label { color: #cbd5e1 !important; }

/* ── Dividers ── */
hr { border-color: rgba(255,255,255,0.08) !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #818cf8 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(129,140,248,0.3); border-radius: 3px; }

/* ── Warning / success boxes ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "chat_session": None,
        "messages_display": [],   # list of {"role", "content"}
        "session_started": False,
        "summary": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Configuration
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏥 MedCare Collections")
    st.markdown("---")
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        placeholder="gsk_...",
        help="Get a free key at https://console.groq.com",
        key="groq_api_key_input",
    )

    st.markdown("---")
    st.markdown("### 👤 Patient Record")

    customer_name = st.text_input(
        "Customer Full Name",
        value="John Smith",
        key="cfg_name",
        help="The name the patient must provide to authenticate.",
    )

    date_of_birth = st.text_input(
        "Date of Birth",
        value="01/15/1985",
        key="cfg_dob",
        help=" format -(DD/MM/YYYY)",
    )

    due_amount = st.number_input(
        "Outstanding Balance ($)",
        min_value=1.0,
        max_value=100_000.0,
        value=850.0,
        step=50.0,
        format="%.2f",
        key="cfg_due",
        help="The total outstanding balance for this session.",
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶ Start Session", use_container_width=True)
    with col2:
        reset_btn = st.button("↺ Reset", use_container_width=True)

    if start_btn:
        if not api_key.strip():
            st.error("Please enter your Groq API key.")
        elif not customer_name.strip():
            st.error("Please enter the customer name.")
        elif not date_of_birth.strip():
            st.error("Please enter the date of birth.")
        else:
            st.session_state.chat_session = ChatSession(
                api_key=api_key.strip(),
                customer_name=customer_name,
                date_of_birth=date_of_birth,
                due_amount=due_amount,
            )
            st.session_state.messages_display = []
            st.session_state.session_started = True
            st.session_state.summary = None

            # Get the initial greeting from the bot
            with st.spinner("Connecting…"):
                greeting = st.session_state.chat_session.greet()
            st.session_state.messages_display.append({
                "role": "assistant",
                "content": greeting,
            })
            st.rerun()

    if reset_btn:
        st.session_state.chat_session = None
        st.session_state.messages_display = []
        st.session_state.session_started = False
        st.session_state.summary = None
        st.rerun()

    # ── Info panel ──
#     st.markdown("---")
#     st.markdown("### 💡 Payment Rules")
#     st.markdown("""
# | Today's Payment | Plan |
# |---|---|
# | < $50 | ❌ Rejected |
# | $50 – $99.99 | ✅ + 12 installments |
# | ≥ $100 | ✅ + 9 installments |
# | Full amount | ✅ Settled |
# """)

#     st.markdown("---")
    st.caption("🤖 Powered by Groq ")


# ─────────────────────────────────────────────────────────────────────────────
# Main chat area
# ─────────────────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="chat-header">
    <h1>🏥 MedCare Collections Assistant</h1>
    <p>AI-powered patient debt resolution · Medical Billing Support</p>
</div>
""", unsafe_allow_html=True)

# ── Status badge ──────────────────────────────────────────────────────────────

session: ChatSession = st.session_state.chat_session

if not st.session_state.session_started:
    st.markdown("""
<div style="text-align:center; padding: 4rem 2rem; color: #64748b;">
    <div style="font-size:4rem; margin-bottom:1rem;">💬</div>
    <h3 style="color:#94a3b8; font-weight:500;">No active session</h3>
    <p style="color:#64748b; max-width:420px; margin:0 auto;">
        Configure patient details in the sidebar and click <strong style="color:#818cf8">▶ Start Session</strong>
        to begin a collections chat.
    </p>
</div>
""", unsafe_allow_html=True)

else:
    # Determine badge
    if session.is_closed:
        if session.state == State.AUTH_FAILED:
            badge_cls, badge_text = "status-failed", "⛔ Authentication Failed"
        elif session.state == State.CLOSED_ACCEPTED:
            badge_cls, badge_text = "status-closed", "✅ Session Closed — Plan Accepted"
        else:
            badge_cls, badge_text = "status-closed", "🔚 Session Closed — Patient Declined"
    else:
        badge_cls, badge_text = "status-active", "🟢 Session Active"

    col_badge, col_ref = st.columns([3, 1])
    with col_badge:
        st.markdown(f'<span class="status-badge {badge_cls}">{badge_text}</span>',
                    unsafe_allow_html=True)
    with col_ref:
        if session:
            st.markdown(
                f'<p style="text-align:right;color:#64748b;font-size:0.8rem;margin-top:4px;">'
                f'REF-{session.ref_number}</p>',
                unsafe_allow_html=True,
            )

    # ── Render message history ────────────────────────────────────────────────

    for msg in st.session_state.messages_display:
        role = msg["role"]
        content = msg["content"]

        if role == "assistant":
            st.markdown(f"""
<div class="message-bubble assistant">
    <div class="avatar">🤖</div>
    <div class="bubble-content">{content.replace(chr(10), '<br>')}</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="message-bubble user">
    <div class="bubble-content">{content.replace(chr(10), '<br>')}</div>
    <div class="avatar">👤</div>
</div>
""", unsafe_allow_html=True)

    # ── Session summary (shown after session closes) ──────────────────────────

    if session.is_closed:
        if st.session_state.summary is None:
            st.session_state.summary = session.generate_summary()

        summary = st.session_state.summary
        outcome = summary["session_metadata"]["outcome"]

        outcome_icons = {
            "PAYMENT_PLAN_AGREED":   ("🎉", "#4ade80", "Payment Plan Agreed"),
            "PATIENT_DECLINED":      ("📋", "#f59e0b", "Patient Declined"),
            "AUTHENTICATION_FAILED": ("🔒", "#f87171", "Authentication Failed"),
        }
        icon, color, label = outcome_icons.get(outcome, ("📄", "#94a3b8", outcome))

        st.markdown(f"""
<div class="summary-container">
    <h3>{icon} Session Summary</h3>
    <p style="color:{color}; font-weight:600; margin-bottom:1rem;">{label}</p>
</div>
""", unsafe_allow_html=True)

        # Payment plan card
        plan = summary.get("payment_plan")
        # if plan and plan.get("status") in ("accepted", "full_payment"):
        if outcome == "PAYMENT_PLAN_AGREED" and plan:
            cols = st.columns(3 if plan["num_installments"] else 2)
            with cols[0]:
                st.metric("💳 Today's Payment", f"${plan['today_payment']:,.2f}")
            if plan["num_installments"]:
                with cols[1]:
                    st.metric("📅 Monthly Installment",
                              f"${plan['monthly_installment']:,.2f}")
                with cols[2]:
                    st.metric("🗓️ # Installments", plan["num_installments"])
            else:
                with cols[1]:
                    st.metric("📊 Balance Remaining", "$0.00")

        else:
         st.info(
        "No payment arrangement was finalized. The session ended without an agreed plan."
    )
        st.markdown("**📄 Full Session Report (JSON)**")
        st.code(json.dumps(summary, indent=2), language="json")

    # ── Chat input (disabled when session closed) ─────────────────────────────

    if not session.is_closed:
        user_input = st.chat_input(
            "Type your message…",
            key="chat_input",
        )
        if user_input and user_input.strip():
            # Add user message to display
            st.session_state.messages_display.append({
                "role": "user",
                "content": user_input.strip(),
            })

            # Get bot response
            with st.spinner("Alex is typing…"):
                reply = session.process(user_input.strip())

            st.session_state.messages_display.append({
                "role": "assistant",
                "content": reply,
            })
            st.rerun()
    else:
        st.markdown(
            '<p style="text-align:center;color:#475569;font-size:0.85rem;margin-top:1rem;">'
            '💬 This session has ended. Click <strong>↺ Reset</strong> in the sidebar to start a new session.'
            "</p>",
            unsafe_allow_html=True,
        )
