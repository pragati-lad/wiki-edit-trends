import streamlit as st
from sqlalchemy.orm import Session

from features.queries import recent_edits


def render_live_feed(session: Session, wiki: str = "enwiki"):
    st.markdown("### 🔴 Live Edit Feed")
    st.caption("Real-time edits — see what people are changing right now and why")
    df = recent_edits(session, limit=12, wiki=wiki)

    if df.empty:
        st.info("Waiting for edits...")
        return

    for _, row in df.iterrows():
        delta = row["edit_size_delta"]
        if delta > 0:
            delta_str = f"+{delta:,}"
            color = "#00cc66"
        elif delta < 0:
            delta_str = f"{delta:,}"
            color = "#ff4444"
        else:
            delta_str = "0"
            color = "#888"

        tags = []
        if row["is_bot"]:
            tags.append("BOT")
        if row["is_anonymous"]:
            tags.append("ANON")
        if row["is_minor"]:
            tags.append("minor")
        tag_html = ""
        if tags:
            tag_html = " ".join(
                f"<span style='background:#333;padding:1px 6px;border-radius:3px;font-size:0.7rem;color:#aaa'>{t}</span>"
                for t in tags
            )

        comment = row["comment"] or ""
        comment_html = ""
        if comment:
            if len(comment) > 100:
                comment = comment[:100] + "..."
            comment_html = f"<br><span style='color:#888;font-size:0.8rem'>📝 {comment}</span>"

        st.markdown(
            f"<div style='margin-bottom:8px;padding:6px 0;border-bottom:1px solid #1e2530'>"
            f"<b>{row['title']}</b> "
            f"<span style='color:{color};font-weight:600'>{delta_str}B</span> "
            f"{tag_html}<br>"
            f"<span style='color:#666;font-size:0.8rem'>by <code>{row['user']}</code></span>"
            f"{comment_html}"
            f"</div>",
            unsafe_allow_html=True,
        )
