import streamlit as st
import pandas as pd
import altair as alt
import json
from epoch_explorer.database.models.chunk_embedding_data_model import ChunkEmbeddingDataModel
from epoch_explorer.database.db.connection import get_connection

def show():
    st.title("🧩 Chunk Embedding Dashboard")

    # -------------------------
    # 🔘 Compact Mode Toggle
    # -------------------------
    compact_mode = st.toggle("🧩 Compact Mode", value=True)

    # --- Load Data ---
    conn = get_connection()
    chunk_model = ChunkEmbeddingDataModel(conn)
    df = chunk_model.get_all_chunks()

    # --- Filters ---
    st.subheader("Filters")
    model_filter = st.multiselect(
        "Embedding Model",
        df.embedding_model.unique(),
        df.embedding_model.unique()
    )

    version_filter = st.multiselect(
        "Embedding Version",
        df.embedding_version.dropna().unique(),
        df.embedding_version.dropna().unique()
    )

    if model_filter:
        df = df[df.embedding_model.isin(model_filter)]
    if version_filter:
        df = df[df.embedding_version.isin(version_filter)]

    # -------------------------
    # 📌 Prepare Chart Objects
    # -------------------------

    # 1️⃣ Chunk Count by Embedding Model
    chart_model = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="embedding_model:N",
            y="count():Q",
            color="embedding_model:N",
            tooltip=["embedding_model", "count()"]
        )
        .properties(title="Chunk Count by Embedding Model")
    )

    # 2️⃣ Quality Score Distribution
    quality_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("quality_score:Q", bin=alt.Bin(maxbins=20)),
            y="count():Q",
            tooltip=["count()"]
        )
        .properties(title="Quality Score Distribution")
    )

    # 3️⃣ Reindex Count Distribution
    reindex_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("reindex_count:Q", bin=alt.Bin(maxbins=20)),
            y="count():Q",
            tooltip=["count()"]
        )
        .properties(title="Reindex Count Distribution")
    )

    charts = [chart_model, quality_chart, reindex_chart]

    # -------------------------
    # 🧩 Render Charts
    # -------------------------
    if compact_mode:
        st.markdown("### 🧩 Compact Mode Enabled")

        # Show charts in 2-column layout
        for i in range(0, len(charts), 2):
            col1, col2 = st.columns(2)
            with col1:
                st.altair_chart(charts[i], use_container_width=True)
            if i + 1 < len(charts):
                with col2:
                    st.altair_chart(charts[i + 1], use_container_width=True)

    else:
        st.markdown("### 📊 Standard View")
        for chart in charts:
            st.altair_chart(chart, use_container_width=True)

    # -------------------------
    # 🕒 Recent Activity Table
    # -------------------------
    st.subheader("🕒 Recent Chunk Activity")
    recent_df = df.sort_values("created_at", ascending=False).head(10)
    st.table(recent_df[["chunk_id", "doc_id", "embedding_model", "created_at", "last_healed"]])

    # -------------------------
    # 🛠 Healing Suggestions
    # -------------------------
    st.subheader("🛠 Healing Suggestions")

    if len(df) > 0:
        selected_chunk = st.selectbox("Select Chunk", df.chunk_id)
        suggestions_str = df[df.chunk_id == selected_chunk]["healing_suggestions"].values[0]

        if suggestions_str:
            try:
                suggestions_json = json.loads(suggestions_str)
                st.json(suggestions_json)
            except Exception as e:
                st.warning(f"Invalid JSON: {e}")
        else:
            st.info("No healing suggestions for this chunk.")
    else:
        st.info("No records available.")
