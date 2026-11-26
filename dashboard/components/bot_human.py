import plotly.graph_objects as go
import streamlit as st
from sqlalchemy.orm import Session

from features.queries import bot_human_counts


def render_bot_human(session: Session):
    st.markdown("### 🤖 Bot vs Human")
    st.caption("Bots auto-revert vandalism, fix formatting, update links — they make up a huge chunk of edits")
    counts = bot_human_counts(session, minutes=60)
    total = counts["bot"] + counts["human"]

    if total == 0:
        st.info("No data yet.")
        return

    bot_pct = round(100 * counts["bot"] / total, 1)
    human_pct = round(100 * counts["human"] / total, 1)

    fig = go.Figure(go.Pie(
        labels=["Human", "Bot"],
        values=[counts["human"], counts["bot"]],
        marker=dict(colors=["#EF553B", "#636EFA"]),
        hole=0.55,
        textinfo="percent",
        textfont_size=14,
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=220,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Last hour: **{counts['human']:,}** human ({human_pct}%) · **{counts['bot']:,}** bot ({bot_pct}%)")
