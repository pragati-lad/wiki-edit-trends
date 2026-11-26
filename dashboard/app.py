import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL
from db.models import Base, Edit

st.set_page_config(
    page_title="Wiki Edit Trends",
    page_icon="📡",
    layout="wide",
)

# --- Custom CSS for cleaner look ---
st.markdown("""
<style>
    [data-testid="stMetric"] {
        background: #0e1117;
        border: 1px solid #1e2530;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #8899aa;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    eng = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
    Base.metadata.create_all(bind=eng)
    return eng


engine = get_engine()
Session = sessionmaker(bind=engine)

# --- Header + Wiki Selector ---
header_col, selector_col = st.columns([3, 1])

with header_col:
    st.markdown("# 📡 Wikipedia Edit Trends")
    st.markdown("Real-time monitoring of Wikipedia edits — with ML-powered vandalism and breaking news detection")

with selector_col:
    st.markdown("")
    st.markdown("")
    # Get available wikis from the database
    session = Session()
    try:
        wikis = (
            session.query(Edit.wiki)
            .group_by(Edit.wiki)
            .order_by(func.count().desc())
            .limit(50)
            .all()
        )
        wiki_options = [w[0] for w in wikis] if wikis else ["enwiki"]
        # Ensure enwiki is first (default)
        if "enwiki" in wiki_options:
            wiki_options.remove("enwiki")
            wiki_options.insert(0, "enwiki")
    finally:
        session.close()

    selected_wiki = st.selectbox("Select Wiki", wiki_options, index=0)

st.markdown("---")

# ============================================================
# ROW 1: KPI Metrics (auto-refresh)
# ============================================================
@st.fragment(run_every="10s")
def kpi_row():
    from features.queries import kpi_stats, total_edit_count, top_wikis_summary

    session = Session()
    try:
        total = total_edit_count(session)
        stats = kpi_stats(session, minutes=10)
        top_wikis = top_wikis_summary(session, minutes=10, limit=3)

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Total Edits Stored", f"{total:,}")
        k2.metric("Edits/min (10m)", f"{stats['edits_per_min']}")
        k3.metric("Unique Articles", f"{stats['unique_articles']:,}")
        k4.metric("Active Wikis", f"{stats['unique_wikis']}")
        k5.metric("Anonymous %", f"{stats['anon_pct']}%")
        k6.metric("Avg Edit Size", f"{stats['avg_edit_size']:,} B")

        if top_wikis:
            wiki_str = " · ".join(f"**{w}** ({c})" for w, c in top_wikis)
            st.caption(f"Top wikis (10m): {wiki_str}")
    finally:
        session.close()


kpi_row()

st.markdown("")

# ============================================================
# ROW 2: Velocity chart + Bot/Human
# ============================================================
col_chart, col_side = st.columns([2, 1])

with col_chart:
    @st.fragment(run_every="10s")
    def velocity_section():
        from dashboard.components.velocity_chart import render_velocity_chart

        session = Session()
        try:
            render_velocity_chart(session)
        finally:
            session.close()

    velocity_section()

with col_side:
    @st.fragment(run_every="10s")
    def side_section():
        from dashboard.components.bot_human import render_bot_human

        session = Session()
        try:
            render_bot_human(session)
        finally:
            session.close()

    side_section()

# ============================================================
# ROW 3: Trending Articles + Edit Size Distribution
# ============================================================
col_trending, col_dist = st.columns([1, 1])

with col_trending:
    @st.fragment(run_every="10s")
    def trending_section():
        from dashboard.components.trending import render_trending

        session = Session()
        try:
            render_trending(session, wiki=selected_wiki)
        finally:
            session.close()

    trending_section()

with col_dist:
    @st.fragment(run_every="10s")
    def dist_section():
        from dashboard.components.edit_size import render_edit_size

        session = Session()
        try:
            render_edit_size(session)
        finally:
            session.close()

    dist_section()

# ============================================================
# ROW 4: Live Feed + Alerts side by side
# ============================================================
st.markdown("---")

col_feed, col_alerts = st.columns([1, 1])

with col_feed:
    @st.fragment(run_every="8s")
    def feed_section():
        from dashboard.components.live_feed import render_live_feed

        session = Session()
        try:
            render_live_feed(session, wiki=selected_wiki)
        finally:
            session.close()

    feed_section()

with col_alerts:
    @st.fragment(run_every="15s")
    def alerts_section():
        from dashboard.components.alerts import render_alerts

        session = Session()
        try:
            render_alerts(session)
        finally:
            session.close()

    alerts_section()
