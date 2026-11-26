import streamlit as st
from sqlalchemy.orm import Session

from features.queries import trending_articles


def render_trending(session: Session, wiki: str = "enwiki"):
    st.markdown("### 🔥 Trending Articles")
    st.caption(
        "Articles getting the most edits right now. "
        "Multiple editors on one article = something newsworthy is happening."
    )
    df = trending_articles(session, minutes=30, limit=10, wiki=wiki)

    if df.empty:
        st.info("No trending articles yet. Needs a few minutes of data.")
        return

    df.index = range(1, len(df) + 1)
    df.index.name = "#"

    st.dataframe(
        df.rename(columns={
            "title": "Article",
            "edit_count": "Edits",
            "unique_editors": "Editors",
            "total_delta": "Bytes Changed",
        }),
        width="stretch",
        hide_index=False,
    )

    if len(df) > 0:
        top = df.iloc[0]
        if top["unique_editors"] >= 3:
            st.success(
                f"**{top['title']}** has {top['edit_count']} edits by "
                f"{top['unique_editors']} different people — likely a current event.",
                icon="📰",
            )
