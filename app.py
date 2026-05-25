import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from pathlib import Path
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyFlow AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_FILE = Path("data/student_data.json")
DATA_FILE.parent.mkdir(exist_ok=True)

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "tasks": [],
        "sessions": [],
        "goals": [],
        "daily_logs": {},
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def calculate_productivity_score(data):
    today = str(date.today())
    tasks = data.get("tasks", [])
    sessions = data.get("sessions", [])

    today_tasks = [t for t in tasks if t.get("date") == today]
    completed = [t for t in today_tasks if t.get("done")]
    completion_rate = (len(completed) / len(today_tasks) * 40) if today_tasks else 0

    today_sessions = [s for s in sessions if s.get("date") == today]
    total_minutes = sum(s.get("duration", 0) for s in today_sessions)
    focus_score = min(total_minutes / 120 * 40, 40)

    goals = data.get("goals", [])
    active_goals = [g for g in goals if not g.get("done")]
    goal_score = max(0, 20 - len(active_goals) * 2) if goals else 0

    return round(completion_rate + focus_score + goal_score)

def get_week_data(data):
    today = date.today()
    week = []
    for i in range(6, -1, -1):
        d = str(today - timedelta(days=i))
        tasks = [t for t in data["tasks"] if t.get("date") == d]
        done = [t for t in tasks if t.get("done")]
        sessions = [s for s in data["sessions"] if s.get("date") == d]
        minutes = sum(s.get("duration", 0) for s in sessions)
        week.append({
            "date": d,
            "day": (today - timedelta(days=i)).strftime("%a"),
            "tasks_total": len(tasks),
            "tasks_done": len(done),
            "focus_minutes": minutes,
        })
    return pd.DataFrame(week)

# ── Gemini setup ──────────────────────────────────────────────────────────────
def get_ai_suggestions(data, api_key):
    try:
        client = genai.Client(api_key=api_key)

        today = str(date.today())
        tasks = data.get("tasks", [])
        sessions = data.get("sessions", [])
        goals = data.get("goals", [])

        today_tasks = [t for t in tasks if t.get("date") == today]
        done_tasks = [t for t in today_tasks if t.get("done")]
        pending_tasks = [t for t in today_tasks if not t.get("done")]
        today_sessions = [s for s in sessions if s.get("date") == today]
        total_focus = sum(s.get("duration", 0) for s in today_sessions)
        score = calculate_productivity_score(data)

        prompt = f"""You are a friendly AI study coach for a student. Analyze their productivity and give concise, actionable advice.

Student's data today ({today}):
- Productivity Score: {score}/100
- Tasks completed: {len(done_tasks)}/{len(today_tasks)}
- Completed tasks: {[t['title'] for t in done_tasks]}
- Pending tasks: {[t['title'] for t in pending_tasks]}
- Focus time logged: {total_focus} minutes
- Active goals: {[g['title'] for g in goals if not g.get('done')]}

Provide exactly 4 personalized suggestions in this JSON format (respond ONLY with valid JSON, no markdown):
{{
  "overall_feedback": "One encouraging sentence about their progress",
  "suggestions": [
    {{"icon": "⚡", "title": "Short title", "detail": "Actionable 1-2 sentence tip"}},
    {{"icon": "📚", "title": "Short title", "detail": "Actionable 1-2 sentence tip"}},
    {{"icon": "🎯", "title": "Short title", "detail": "Actionable 1-2 sentence tip"}},
    {{"icon": "💡", "title": "Short title", "detail": "Actionable 1-2 sentence tip"}}
  ]
}}"""

        response = model.generate_content(prompt)
        text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Global ── */
  [data-testid="stAppViewContainer"] { background: #0f1117; }
  [data-testid="stSidebar"] { background: #161b27 !important; border-right: 1px solid #2a2f3e; }

  /* ── Cards ── */
  .metric-card {
    background: linear-gradient(135deg, #1e2535 0%, #252d40 100%);
    border: 1px solid #2e3650;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform .2s;
  }
  .metric-card:hover { transform: translateY(-2px); }
  .metric-value { font-size: 2.4rem; font-weight: 800; color: #c084fc; line-height: 1; }
  .metric-label { font-size: .8rem; color: #8892b0; margin-top: 6px; letter-spacing: .05em; text-transform: uppercase; }

  /* ── Score ring ── */
  .score-ring {
    background: conic-gradient(#c084fc VAR_DEG, #1e2535 0);
    border-radius: 50%;
    width: 130px; height: 130px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto;
    box-shadow: 0 0 30px #c084fc44;
  }
  .score-inner {
    background: #161b27;
    border-radius: 50%;
    width: 96px; height: 96px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
  }
  .score-num { font-size: 1.8rem; font-weight: 800; color: #c084fc; }
  .score-sub { font-size: .65rem; color: #8892b0; }

  /* ── Task items ── */
  .task-item {
    background: #1e2535;
    border: 1px solid #2e3650;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .task-done { opacity: .5; text-decoration: line-through; }
  .badge {
    font-size: .7rem;
    padding: 2px 8px;
    border-radius: 99px;
    font-weight: 600;
    letter-spacing: .03em;
  }
  .badge-high { background: #ff4d6d22; color: #ff4d6d; border: 1px solid #ff4d6d44; }
  .badge-medium { background: #fbbf2422; color: #fbbf24; border: 1px solid #fbbf2444; }
  .badge-low { background: #34d39922; color: #34d399; border: 1px solid #34d39944; }

  /* ── AI card ── */
  .ai-card {
    background: linear-gradient(135deg, #1e1b3a 0%, #251e45 100%);
    border: 1px solid #4f46e544;
    border-radius: 14px;
    padding: 16px 20px;
    margin: 8px 0;
  }
  .ai-card-title { font-weight: 700; color: #a78bfa; font-size: .95rem; }
  .ai-card-body  { color: #c4cde0; font-size: .85rem; margin-top: 4px; line-height: 1.5; }

  /* ── Section headers ── */
  .section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 8px 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Sidebar nav ── */
  .nav-item {
    padding: 10px 14px;
    border-radius: 10px;
    cursor: pointer;
    color: #8892b0;
    margin: 2px 0;
    font-size: .9rem;
    transition: background .15s;
  }
  .nav-item:hover { background: #252d40; color: #e2e8f0; }
  .nav-active { background: #c084fc22 !important; color: #c084fc !important; border-left: 3px solid #c084fc; }

  /* hide streamlit branding */
  #MainMenu, footer { visibility: hidden; }
  [data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "session_name" not in st.session_state:
    st.session_state.session_name = ""

data = st.session_state.data

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 StudyFlow AI")
    st.markdown("---")

    pages = [
        ("📊", "Dashboard"),
        ("✅", "Tasks"),
        ("⏱️", "Focus Timer"),
        ("🏆", "Goals"),
        ("🤖", "AI Coach"),
    ]
    for icon, name in pages:
        active = "nav-active" if st.session_state.page == name else ""
        if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password",
                             placeholder="AIza...",
                             help="Get your key at aistudio.google.com")
    st.session_state.api_key = api_key

    score = calculate_productivity_score(data)
    deg = int(score * 3.6)
    st.markdown("---")
    st.markdown('<div class="section-header">Today\'s Score</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="score-ring" style="background: conic-gradient(#c084fc {deg}deg, #1e2535 0);">
      <div class="score-inner">
        <span class="score-num">{score}</span>
        <span class="score-sub">/ 100</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Helper: badge html ─────────────────────────────────────────────────────────
def priority_badge(p):
    cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(p, "badge-low")
    return f'<span class="badge {cls}">{p}</span>'

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Dashboard":
    st.markdown("## 📊 Dashboard")
    today = str(date.today())

    # ── Metrics row ───────────────────────────────────────────────────────────
    tasks = data["tasks"]
    today_tasks = [t for t in tasks if t.get("date") == today]
    done_today = [t for t in today_tasks if t.get("done")]
    sessions_today = [s for s in data["sessions"] if s.get("date") == today]
    focus_mins = sum(s.get("duration", 0) for s in sessions_today)

    total_done_all = len([t for t in tasks if t.get("done")])

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, len(done_today), "Tasks Done Today"),
        (c2, len(today_tasks) - len(done_today), "Tasks Pending"),
        (c3, f"{focus_mins}m", "Focus Time Today"),
        (c4, total_done_all, "All-Time Tasks Done"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{val}</div>
          <div class="metric-label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    week_df = get_week_data(data)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-header">📅 Weekly Task Completion</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_bar(x=week_df["day"], y=week_df["tasks_total"],
                    name="Total", marker_color="#2e3650")
        fig.add_bar(x=week_df["day"], y=week_df["tasks_done"],
                    name="Completed", marker_color="#c084fc")
        fig.update_layout(
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8892b0",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#2e3650"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-header">⏱️ Weekly Focus Minutes</div>', unsafe_allow_html=True)
        fig2 = px.area(week_df, x="day", y="focus_minutes",
                       color_discrete_sequence=["#c084fc"])
        fig2.update_traces(fill="tozeroy", fillcolor="#c084fc22", line_width=2)
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8892b0",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#2e3650"),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Today's pending tasks quick-view ──────────────────────────────────────
    st.markdown('<div class="section-header">📋 Today\'s Pending Tasks</div>', unsafe_allow_html=True)
    pending = [t for t in today_tasks if not t.get("done")]
    if pending:
        for t in pending[:5]:
            st.markdown(f"""<div class="task-item">
              <span>🔲</span>
              <span style="flex:1;color:#e2e8f0">{t['title']}</span>
              {priority_badge(t.get('priority','Low'))}
              <span style="color:#8892b0;font-size:.8rem">{t.get('subject','')}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.success("🎉 All tasks for today are done!")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TASKS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Tasks":
    st.markdown("## ✅ Task Manager")

    # Add task form
    with st.expander("➕ Add New Task", expanded=False):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            title = st.text_input("Task title", placeholder="e.g. Complete Math Assignment")
        with col2:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        with col3:
            subject = st.text_input("Subject", placeholder="e.g. Math")

        col4, col5 = st.columns([2, 1])
        with col4:
            due = st.date_input("Due date", value=date.today())
        with col5:
            notes = st.text_input("Notes (optional)")

        if st.button("Add Task ✨", use_container_width=True, type="primary"):
            if title.strip():
                data["tasks"].append({
                    "id": str(time.time()),
                    "title": title.strip(),
                    "priority": priority,
                    "subject": subject,
                    "notes": notes,
                    "date": str(due),
                    "done": False,
                    "created": str(datetime.now()),
                })
                save_data(data)
                st.success(f"Added: {title}")
                st.rerun()

    st.markdown("---")

    # Filter
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_date = st.date_input("Filter by date", value=date.today())
    with col_f2:
        filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"],
                                          default=["High", "Medium", "Low"])
    with col_f3:
        filter_status = st.radio("Status", ["All", "Pending", "Done"], horizontal=True)

    filtered = [
        t for t in data["tasks"]
        if t.get("date") == str(filter_date)
        and t.get("priority", "Low") in filter_priority
        and (filter_status == "All"
             or (filter_status == "Done" and t.get("done"))
             or (filter_status == "Pending" and not t.get("done")))
    ]

    st.markdown(f'<div class="section-header">{len(filtered)} task(s) found</div>', unsafe_allow_html=True)

    for t in filtered:
        done_cls = "task-done" if t.get("done") else ""
        col_a, col_b = st.columns([10, 1])
        with col_a:
            st.markdown(f"""<div class="task-item">
              <span>{"✅" if t.get("done") else "🔲"}</span>
              <span class="{done_cls}" style="flex:1;color:#e2e8f0">{t['title']}</span>
              {priority_badge(t.get('priority','Low'))}
              <span style="color:#8892b0;font-size:.8rem">{t.get('subject','')}</span>
              {f'<span style="color:#6b7280;font-size:.75rem">📝 {t["notes"]}</span>' if t.get('notes') else ''}
            </div>""", unsafe_allow_html=True)
        with col_b:
            action = "Undo" if t.get("done") else "Done"
            if st.button(action, key=f"toggle_{t['id']}"):
                t["done"] = not t.get("done")
                save_data(data)
                st.rerun()
            if st.button("🗑️", key=f"del_{t['id']}"):
                data["tasks"].remove(t)
                save_data(data)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FOCUS TIMER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Focus Timer":
    st.markdown("## ⏱️ Focus Timer")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header">🍅 Pomodoro Session</div>', unsafe_allow_html=True)

        session_label = st.text_input("What are you studying?",
                                       placeholder="e.g. Chapter 5 – Calculus",
                                       key="sess_label")
        duration_choice = st.select_slider("Session length",
                                            options=[15, 25, 30, 45, 60, 90],
                                            value=25)

        if not st.session_state.timer_running:
            if st.button("▶️  Start Focus Session", use_container_width=True, type="primary"):
                st.session_state.timer_running = True
                st.session_state.timer_start = datetime.now()
                st.session_state.timer_duration = duration_choice * 60
                st.session_state.session_name = session_label or "Focus Session"
                st.rerun()
        else:
            elapsed = (datetime.now() - st.session_state.timer_start).seconds
            remaining = max(st.session_state.timer_duration - elapsed, 0)
            mins, secs = divmod(remaining, 60)

            progress = elapsed / st.session_state.timer_duration
            st.markdown(f"""
            <div style="text-align:center; padding: 20px 0;">
              <div style="font-size:3.5rem; font-weight:800; color:#c084fc; font-variant-numeric: tabular-nums;">
                {mins:02d}:{secs:02d}
              </div>
              <div style="color:#8892b0; font-size:.9rem; margin-top:6px;">
                📖 {st.session_state.session_name}
              </div>
            </div>""", unsafe_allow_html=True)
            st.progress(min(progress, 1.0))

            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("⏹️  End Session", use_container_width=True):
                    mins_done = elapsed // 60
                    if mins_done > 0:
                        data["sessions"].append({
                            "id": str(time.time()),
                            "label": st.session_state.session_name,
                            "duration": mins_done,
                            "date": str(date.today()),
                            "time": str(datetime.now().strftime("%H:%M")),
                        })
                        save_data(data)
                        st.success(f"✅ Logged {mins_done} min session!")
                    st.session_state.timer_running = False
                    st.session_state.timer_start = None
                    st.rerun()

            if remaining == 0:
                st.balloons()
                st.success("🎉 Session complete!")

            if remaining > 0:
                time.sleep(1)
                st.rerun()

    with col2:
        st.markdown('<div class="section-header">📈 Session History</div>', unsafe_allow_html=True)
        sessions = data.get("sessions", [])
        if sessions:
            recent = sorted(sessions, key=lambda x: x.get("date",""), reverse=True)[:8]
            for s in recent:
                st.markdown(f"""<div class="task-item">
                  <span>⏱️</span>
                  <span style="flex:1;color:#e2e8f0">{s['label']}</span>
                  <span style="color:#c084fc;font-weight:700">{s['duration']}m</span>
                  <span style="color:#8892b0;font-size:.8rem">{s['date']}</span>
                </div>""", unsafe_allow_html=True)

            total = sum(s.get("duration", 0) for s in sessions)
            st.markdown(f"<br><b style='color:#c084fc'>Total focus time: {total} minutes ({total//60}h {total%60}m)</b>",
                        unsafe_allow_html=True)
        else:
            st.info("No sessions yet. Start your first focus session!")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: GOALS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Goals":
    st.markdown("## 🏆 Goals Tracker")

    with st.expander("➕ Add New Goal", expanded=False):
        g_title = st.text_input("Goal", placeholder="e.g. Score 90%+ in Physics final")
        g_deadline = st.date_input("Target date", value=date.today() + timedelta(days=30))
        g_category = st.selectbox("Category", ["Academic", "Study Habit", "Wellness", "Extracurricular", "Other"])

        if st.button("Add Goal 🎯", use_container_width=True, type="primary"):
            if g_title.strip():
                data["goals"].append({
                    "id": str(time.time()),
                    "title": g_title.strip(),
                    "deadline": str(g_deadline),
                    "category": g_category,
                    "done": False,
                    "created": str(datetime.now()),
                })
                save_data(data)
                st.success(f"Goal added: {g_title}")
                st.rerun()

    st.markdown("---")

    active = [g for g in data["goals"] if not g.get("done")]
    achieved = [g for g in data["goals"] if g.get("done")]

    tab1, tab2 = st.tabs([f"🔥 Active ({len(active)})", f"🏅 Achieved ({len(achieved)})"])

    with tab1:
        if active:
            for g in active:
                deadline = date.fromisoformat(g["deadline"])
                days_left = (deadline - date.today()).days
                urgency_color = "#ff4d6d" if days_left <= 3 else "#fbbf24" if days_left <= 7 else "#34d399"

                col_a, col_b = st.columns([10, 1])
                with col_a:
                    st.markdown(f"""<div class="task-item">
                      <span>🎯</span>
                      <span style="flex:1;color:#e2e8f0">{g['title']}</span>
                      <span class="badge badge-medium">{g['category']}</span>
                      <span style="color:{urgency_color};font-size:.8rem">
                        {"⚠️ " if days_left <= 3 else ""}{days_left}d left
                      </span>
                    </div>""", unsafe_allow_html=True)
                with col_b:
                    if st.button("✅", key=f"goal_done_{g['id']}"):
                        g["done"] = True
                        save_data(data)
                        st.balloons()
                        st.rerun()
                    if st.button("🗑️", key=f"goal_del_{g['id']}"):
                        data["goals"].remove(g)
                        save_data(data)
                        st.rerun()
        else:
            st.info("No active goals. Add one above!")

    with tab2:
        if achieved:
            for g in achieved:
                st.markdown(f"""<div class="task-item" style="opacity:.7">
                  <span>🏅</span>
                  <span style="flex:1;color:#e2e8f0;text-decoration:line-through">{g['title']}</span>
                  <span class="badge badge-low">Done</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Complete your first goal to see it here!")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI COACH
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "AI Coach":
    st.markdown("## 🤖 AI Study Coach")
    st.markdown("<p style='color:#8892b0'>Powered by Gemini 2.0 Flash — Get personalized advice based on your productivity data.</p>", unsafe_allow_html=True)

    api_key = st.session_state.get("api_key", "")

    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar to use the AI Coach.")
        st.markdown("""
        **How to get a free API key:**
        1. Visit [aistudio.google.com](https://aistudio.google.com)
        2. Sign in with your Google account
        3. Click **Get API Key** → Create API key
        4. Paste it in the sidebar
        """)
    else:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Get AI Suggestions", use_container_width=True, type="primary"):
                with st.spinner("Analyzing your data..."):
                    result = get_ai_suggestions(data, api_key)
                    st.session_state.ai_result = result

        result = st.session_state.get("ai_result")

        if result:
            if "error" in result:
                st.error(f"API Error: {result['error']}")
            else:
                st.markdown(f"""
                <div class="ai-card" style="background:linear-gradient(135deg,#1a2744,#1e1b3a);border:1px solid #6366f144;margin-bottom:16px;">
                  <div style="color:#a78bfa;font-size:1rem;font-weight:700">🤖 Coach Summary</div>
                  <div style="color:#e2e8f0;margin-top:8px;line-height:1.6">{result.get('overall_feedback','')}</div>
                </div>""", unsafe_allow_html=True)

                st.markdown('<div class="section-header">💡 Personalized Suggestions</div>', unsafe_allow_html=True)
                for s in result.get("suggestions", []):
                    st.markdown(f"""
                    <div class="ai-card">
                      <div class="ai-card-title">{s['icon']} {s['title']}</div>
                      <div class="ai-card-body">{s['detail']}</div>
                    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-header">💬 Ask the Coach</div>', unsafe_allow_html=True)

    user_q = st.text_area("Ask anything about studying, productivity, or time management:",
                           placeholder="e.g. How should I balance studying for 3 exams in one week?",
                           height=100)

    if st.button("Ask Coach 🚀", type="primary") and user_q and api_key:
        with st.spinner("Thinking..."):
            try:
                client = genai.Client(api_key=api_key)
                resp = client.models.generate_content(model="gemini-2.0-flash", contents=
                    f"You are a concise, practical student study coach. Answer this student's question in 3-5 sentences with specific, actionable advice:\n\n{user_q}"
                )
                st.markdown(f"""
                <div class="ai-card">
                  <div class="ai-card-title">🤖 Coach Response</div>
                  <div class="ai-card-body">{resp.text}</div>
                </div>""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
    elif st.button("Ask Coach 🚀") and not api_key:
        st.warning("Add your Gemini API key in the sidebar first.")
