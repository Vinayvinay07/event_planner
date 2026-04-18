import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit.components.v1 as components
import os
from datetime import date
from groq import Groq

pio.templates.default = "plotly_white"

st.set_page_config(page_title="EventVista AI", page_icon="🎉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a1a2e, #16213e, #0f3460) !important;
}
section[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
section[data-testid="stSidebar"] hr { border-color: #334155 !important; }

.main .block-container { padding: 2rem 2.5rem !important; background: #f1f5f9 !important; }

.kpi { background:#fff; border-radius:14px; padding:20px 22px; border-left:5px solid; box-shadow:0 1px 8px rgba(0,0,0,0.07); }
.kpi .v { font-size:26px; font-weight:700; margin:0; }
.kpi .l { font-size:11px; color:#64748b; margin-top:4px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; }

.sec { font-size:22px; font-weight:700; color:#1e293b; margin-bottom:18px; border-bottom:2px solid #e2e8f0; padding-bottom:10px; }

div.stButton > button {
    border-radius:8px !important; font-weight:600 !important;
    font-size:13px !important; border:none !important;
    transition:all .15s !important;
}
div.stButton > button:hover { filter:brightness(1.08); transform:translateY(-1px); }

#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") or st.secreats.get("GROQ_API_KEY")
COLORS = ["#6c63ff","#f472b6","#38bdf8","#34d399","#fb923c","#facc15","#a78bfa"]

# ── Chart renderer (pure HTML — immune to Streamlit theme) ────────────────────
def chart(fig, h=360):
    fig.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Inter", color="#334155", size=12),
        margin=dict(t=44, b=32, l=48, r=16),
        title=dict(font=dict(size=14, color="#1e293b"), x=0),
        legend=dict(bgcolor="#ffffff", font=dict(color="#334155")),
        xaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(color="#64748b")),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(color="#64748b")),
    )
    html = fig.to_html(full_html=True, include_plotlyjs="cdn", config={"displayModeBar": False})
    components.html(html, height=h, scrolling=False)

# ── AI ────────────────────────────────────────────────────────────────────────
def ai(prompt):
    try:
        r = Groq(api_key=GROQ_API_KEY).chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=1024
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠️ {e}"

# ── DB ────────────────────────────────────────────────────────────────────────
def db():
    return sqlite3.connect("eventvista.db", check_same_thread=False)

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT, event_date TEXT, event_time TEXT,
            budget INTEGER, num_guests INTEGER, location TEXT,
            description TEXT, reminder_date TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER, task_name TEXT,
            due_date TEXT, completed INTEGER DEFAULT 0)""")
        for col, typ in [("description","TEXT"),("reminder_date","TEXT")]:
            try: c.execute(f"ALTER TABLE events ADD COLUMN {col} {typ}")
            except: pass

init_db()

def get_events(): return pd.read_sql("SELECT * FROM events ORDER BY event_date", db())
def get_tasks(eid=None):
    q = "SELECT * FROM tasks" + (f" WHERE event_id={eid}" if eid else "")
    return pd.read_sql(q, db())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding:8px 0 4px'><span style='font-size:22px'>🎉</span> <b style='font-size:17px;color:#fff'>EventVista AI</b></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:11px;color:#94a3b8;margin-bottom:12px'>Smart Event Planning</p>", unsafe_allow_html=True)
    st.divider()
    page = st.radio("", ["🏠 Dashboard","➕ Add Event","📋 My Events","✅ Tasks","📅 Calendar","🤖 AI Assistant"], label_visibility="collapsed")
    st.divider()
    ev = get_events(); tk = get_tasks()
    p = int((tk['completed']==0).sum()) if not tk.empty else 0
    st.markdown(f"<p style='font-size:11px;color:#94a3b8'>📊 {len(ev)} events &nbsp;·&nbsp; ⏳ {p} pending</p>", unsafe_allow_html=True)

# ── Dashboard ─────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown("<div class='sec'>🏠 Dashboard</div>", unsafe_allow_html=True)
    df = get_events(); tk = get_tasks()
    budget = int(df['budget'].sum()) if not df.empty else 0
    guests = int(df['num_guests'].sum()) if not df.empty else 0
    pending = int((tk['completed']==0).sum()) if not tk.empty else 0
    done    = int(tk['completed'].sum()) if not tk.empty else 0

    c1,c2,c3,c4 = st.columns(4)
    for col,val,lbl,color in [
        (c1, len(df),          "Total Events",  "#6c63ff"),
        (c2, f"₹{budget:,}",  "Total Budget",  "#f472b6"),
        (c3, guests,           "Total Guests",  "#38bdf8"),
        (c4, pending,          "Pending Tasks", "#fb923c"),
    ]:
        col.markdown(f"<div class='kpi' style='border-color:{color}'><div class='v' style='color:{color}'>{val}</div><div class='l'>{lbl}</div></div>", unsafe_allow_html=True)

    if not df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df, x="event_type", y="budget", color="event_type",
                         color_discrete_sequence=COLORS, title="💰 Budget by Event Type",
                         labels={"event_type":"","budget":"Budget (₹)"})
            fig.update_traces(marker_line_width=0)
            chart(fig)
        with col2:
            fig2 = px.pie(df, names="event_type", hole=0.5,
                          color_discrete_sequence=COLORS, title="🎯 Events by Type")
            fig2.update_traces(marker_line_color="#fff", marker_line_width=2)
            chart(fig2)

        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.bar(df, x="event_type", y="num_guests", color="event_type",
                          color_discrete_sequence=COLORS, title="👥 Guests by Event Type",
                          labels={"event_type":"","num_guests":"Guests"})
            fig3.update_traces(marker_line_width=0)
            chart(fig3)
        with col4:
            td = pd.DataFrame({"Status":["Completed","Pending"],"Count":[done,pending]})
            fig4 = px.pie(td, names="Status", values="Count", hole=0.5,
                          color_discrete_sequence=["#34d399","#fb923c"], title="✅ Task Completion")
            fig4.update_traces(marker_line_color="#fff", marker_line_width=2)
            chart(fig4)

        st.markdown("### 📅 Upcoming Events")
        today = str(date.today())
        up = df[df["event_date"] >= today].head(5)
        if not up.empty:
            st.dataframe(up[["event_type","event_date","event_time","location","num_guests","budget"]].rename(columns={
                "event_type":"Type","event_date":"Date","event_time":"Time",
                "location":"Location","num_guests":"Guests","budget":"Budget (₹)"}),
                use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming events.")
    else:
        st.info("No events yet — go to ➕ Add Event to get started!")

# ── Add Event ─────────────────────────────────────────────────────────────────
elif page == "➕ Add Event":
    st.markdown("<div class='sec'>➕ Add New Event</div>", unsafe_allow_html=True)
    TYPES = ["Wedding","Birthday","Corporate","Conference","Party","Concert","Festival","Other"]
    with st.form("add_event", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            etype    = st.selectbox("Event Type", TYPES)
            edate    = st.date_input("Date", min_value=date.today())
            etime    = st.time_input("Time")
            location = st.text_input("📍 Location", placeholder="Venue or city")
        with c2:
            budget   = st.number_input("💰 Budget (₹)", min_value=0, step=1000)
            guests   = st.number_input("👥 Guests", min_value=1, step=1)
            reminder = st.date_input("🔔 Reminder", min_value=date.today())
            desc     = st.text_area("📝 Notes", placeholder="Optional details...", height=108)
        ai_on = st.checkbox("🤖 Get AI suggestions after saving")
        if st.form_submit_button("🎉 Save Event", use_container_width=True):
            with db() as c:
                c.execute("INSERT INTO events(event_type,event_date,event_time,budget,num_guests,location,description,reminder_date) VALUES(?,?,?,?,?,?,?,?)",
                          (etype,str(edate),str(etime),budget,guests,location,desc,str(reminder)))
            st.success(f"✅ {etype} saved for {edate}!")
            if ai_on:
                with st.spinner("🤖 Generating suggestions..."):
                    st.markdown("### 🤖 AI Suggestions")
                    st.markdown(ai(f"Plan a {etype} on {edate} at {location} for {guests} guests, budget ₹{budget}. Give top 5 tips, task checklist, and budget breakdown."))

# ── My Events ─────────────────────────────────────────────────────────────────
elif page == "📋 My Events":
    st.markdown("<div class='sec'>📋 My Events</div>", unsafe_allow_html=True)
    df = get_events()
    if df.empty:
        st.info("No events yet.")
    else:
        q = st.text_input("🔍 Search", placeholder="Type, location...")
        if q: df = df[df.apply(lambda r: q.lower() in str(r).lower(), axis=1)]
        for _, row in df.iterrows():
            with st.expander(f"🎯 **{row['event_type']}** — {row['event_date']} · 📍 {row['location']}"):
                a,b,c = st.columns(3)
                a.metric("Time", row['event_time'])
                b.metric("Guests", int(row['num_guests']))
                c.metric("Budget", f"₹{int(row['budget']):,}")
                if row.get('description'):
                    st.caption(f"📝 {row['description']}")
                st.divider()
                b1,b2,b3 = st.columns(3)
                if b1.button("🤖 AI Tips", key=f"ai{row['id']}", use_container_width=True):
                    with st.spinner("Thinking..."):
                        st.markdown(ai(f"5 professional tips for a {row['event_type']} for {row['num_guests']} guests at {row['location']}, budget ₹{row['budget']}."))
                if b2.button("➕ Task", key=f"tk{row['id']}", use_container_width=True):
                    st.session_state[f"t{row['id']}"] = True
                if b3.button("🗑️ Delete", key=f"dl{row['id']}", use_container_width=True):
                    with db() as c:
                        c.execute("DELETE FROM events WHERE id=?", (row['id'],))
                        c.execute("DELETE FROM tasks WHERE event_id=?", (row['id'],))
                    st.rerun()
                if st.session_state.get(f"t{row['id']}"):
                    with st.form(f"tf{row['id']}"):
                        ta, tb = st.columns(2)
                        tn = ta.text_input("Task")
                        td = tb.date_input("Due")
                        if st.form_submit_button("Add", use_container_width=True):
                            with db() as c:
                                c.execute("INSERT INTO tasks(event_id,task_name,due_date) VALUES(?,?,?)", (row['id'],tn,str(td)))
                            st.session_state[f"t{row['id']}"] = False
                            st.rerun()

# ── Tasks ─────────────────────────────────────────────────────────────────────
elif page == "✅ Tasks":
    st.markdown("<div class='sec'>✅ Task Manager</div>", unsafe_allow_html=True)
    tk = get_tasks(); ev = get_events()
    if tk.empty:
        st.info("No tasks yet. Add from My Events.")
    else:
        done = int(tk['completed'].sum()); total = len(tk)
        st.markdown(f"**{done}/{total} completed**")
        st.progress(done/total if total else 0)
        st.markdown("<br>", unsafe_allow_html=True)
        mg = tk.merge(ev[['id','event_type']], left_on='event_id', right_on='id', suffixes=('','_e'))
        t1, t2 = st.tabs(["⏳ Pending", "✅ Completed"])
        with t1:
            pnd = mg[mg['completed']==0]
            if pnd.empty: st.success("All done! 🎉")
            for _, r in pnd.iterrows():
                a,b,c = st.columns([4,2,1])
                a.markdown(f"⏳ **{r['task_name']}** <span style='color:#94a3b8;font-size:12px'>({r['event_type']})</span>", unsafe_allow_html=True)
                b.caption(f"📅 {r['due_date']}")
                if c.button("✓", key=f"dn{r['id']}", use_container_width=True):
                    with db() as cx: cx.execute("UPDATE tasks SET completed=1 WHERE id=?", (r['id'],))
                    st.rerun()
        with t2:
            cmp = mg[mg['completed']==1]
            if cmp.empty: st.info("No completed tasks yet.")
            for _, r in cmp.iterrows():
                st.markdown(f"✅ ~~{r['task_name']}~~ <span style='color:#94a3b8;font-size:12px'>({r['event_type']})</span>", unsafe_allow_html=True)

# ── Calendar ──────────────────────────────────────────────────────────────────
elif page == "📅 Calendar":
    st.markdown("<div class='sec'>📅 Event Calendar</div>", unsafe_allow_html=True)
    df = get_events()
    if df.empty:
        st.info("No events to display.")
    else:
        df['event_date'] = pd.to_datetime(df['event_date'])
        df['end_date']   = df['event_date'] + pd.Timedelta(hours=3)
        df['label']      = df['event_type'] + " @ " + df['location'].fillna("")
        fig = px.timeline(df, x_start="event_date", x_end="end_date", y="label",
                          color="event_type", color_discrete_sequence=COLORS,
                          hover_data=["location","num_guests","budget"], title="📅 Event Timeline")
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig.update_traces(opacity=0.88, marker_line_width=0)
        chart(fig, h=440)

        df['month'] = df['event_date'].dt.strftime('%B %Y')
        for month, grp in df.groupby('month'):
            st.markdown(f"**📅 {month}**")
            st.dataframe(grp[['event_type','event_date','location','num_guests','budget']].rename(columns={
                'event_type':'Type','event_date':'Date','location':'Location',
                'num_guests':'Guests','budget':'Budget (₹)'}),
                use_container_width=True, hide_index=True)

# ── AI Assistant ──────────────────────────────────────────────────────────────
elif page == "🤖 AI Assistant":
    st.markdown("<div class='sec'>🤖 AI Event Assistant</div>", unsafe_allow_html=True)
    if "chat" not in st.session_state: st.session_state.chat = []

    QUICK = ["Wedding checklist","Budget tips","Venue ideas","Guest management","Catering suggestions","Decoration ideas"]
    cols = st.columns(3)
    for i, qp in enumerate(QUICK):
        if cols[i%3].button(qp, key=f"q{i}", use_container_width=True):
            st.session_state.chat.append({"role":"user","content":qp})
            st.session_state.chat.append({"role":"assistant","content":ai(f"You are an expert event planner. {qp}")})
            st.rerun()

    st.divider()
    for m in st.session_state.chat:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if inp := st.chat_input("Ask anything about event planning..."):
        st.session_state.chat.append({"role":"user","content":inp})
        with st.chat_message("user"): st.markdown(inp)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                rep = ai(f"You are an expert event planner. {inp}")
                st.markdown(rep)
        st.session_state.chat.append({"role":"assistant","content":rep})

    if st.session_state.chat:
        if st.button("🗑️ Clear Chat"): st.session_state.chat = []; st.rerun()
