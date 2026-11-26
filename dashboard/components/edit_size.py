import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from features.queries import edit_size_distribution


def render_edit_size(session: Session):
    st.markdown("### 📊 Edit Size Distribution")
    st.caption("How big are edits? Most are small fixes. Large deletions (left tail) can indicate vandalism.")
    df = edit_size_distribution(session, minutes=60)

    if df.empty:
        st.info("No edit size data yet.")
        return

    fig = px.histogram(
        df,
        x="edit_size_delta",
        nbins=60,
        labels={"edit_size_delta": "Bytes Changed"},
        color_discrete_sequence=["#AB63FA"],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=280,
        xaxis_title="Bytes Changed",
        yaxis_title="Count",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.05,
    )
    st.plotly_chart(fig, width="stretch")
