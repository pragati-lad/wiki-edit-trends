import streamlit as st
from sqlalchemy.orm import Session

from features.queries import recent_alerts


def render_alerts(session: Session):
    st.markdown("### 🚨 ML Alerts")
    st.caption("Vandalism = ML flagged a suspicious edit. Breaking News = sudden edit spike on an article.")
    df = recent_alerts(session, limit=15)

    if df.empty:
        st.markdown(
            "> No alerts yet. Alerts appear once the vandalism model is trained "
            "(`python scripts/train_vandalism.py`) or when an article gets an unusual "
            "burst of edits (breaking news)."
        )
        return

    for _, row in df.iterrows():
        alert_type = row["alert_type"]
        score = f"{row['score']:.2f}" if row["score"] is not None else "N/A"

        if alert_type == "vandalism":
            st.error(
                f"**VANDALISM** — {row['title']} (score: {score})  \n"
                f"{row['description']}",
                icon="🚨",
            )
        else:
            st.warning(
                f"**BREAKING NEWS** — {row['title']} (z-score: {score})  \n"
                f"{row['description']}",
                icon="📰",
            )
