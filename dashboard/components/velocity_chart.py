import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from features.queries import edits_per_minute


def render_velocity_chart(session: Session):
    st.markdown("### 📈 Edit Velocity")
    st.caption("Number of edits per minute across all wikis — shows how active Wikipedia is right now")
    df = edits_per_minute(session, minutes=30)

    if df.empty:
        st.info("Collecting data... Chart appears after ~2 minutes of streaming.")
        return

    fig = px.area(
        df,
        x="minute",
        y="count",
        labels={"minute": "", "count": "Edits"},
    )
    fig.update_traces(
        fill="tozeroy",
        line_color="#636EFA",
        fillcolor="rgba(99,110,250,0.2)",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=280,
        xaxis_title=None,
        yaxis_title="Edits / min",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")
