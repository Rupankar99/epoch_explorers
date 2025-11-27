import streamlit as st
import pandas as pd
import altair as alt
import json
from database.models.chunk_embedding_data import ChunkEmbeddingDataModel
from database.db.connection import get_connection

# --- Main App ---
def show():
    st.title("🧩 Chunk Embedding Dashboard")

    # --- Load Data ---
    conn = get_connection()
    chunk_model = ChunkEmbeddingDataModel(conn)
    df = chunk_model.get_all_chunks()  # returns pandas DataFrame

    # --- Filters ---
    st.subheader("Filters")
    model_filter = st.multiselect("Embedding Model", df.embedding_model.unique(), df.embedding_model.unique())
    version_filter = st.multiselect("Embedding Version", df.embedding_version.dropna().unique(), df.embedding_version.dropna().unique())

    if model_filter:
        df = df[df.embedding_model.isin(model_filter)]
    if version_filter:
        df = df[df.embedding_version.isin(version_filter)]

    # --- 1️⃣ Chunk Count by Embedding Model ---
    st.subheader("📊 Chunk Count by Embedding Model")
    chart_model = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="embedding_model:N",
            y="count():Q",
            color="embedding_model:N",
            tooltip=["embedding_model", "count()"]
        )
    )
    st.altair_chart(chart_model, use_container_width=True)

    # --- 2️⃣ Quality Score Distribution ---
    st.subheader("⭐ Quality Score Distribution")
    quality_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("quality_score:Q", bin=alt.Bin(maxbins=20)),
            y="count():Q",
            tooltip=["count()"]
        )
    )
    st.altair_chart(quality_chart, use_container_width=True)

    # --- 3️⃣ Reindex Count Distribution ---
    st.subheader("🔄 Reindex Count Distribution")
    reindex_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("reindex_count:Q", bin=alt.Bin(maxbins=20)),
            y="count():Q",
            tooltip=["count()"]
        )
    )
    st.altair_chart(reindex_chart, use_container_width=True)

    # --- 4️⃣ Recently Created / Healed Chunks ---
    st.subheader("🕒 Recent Chunk Activity")
    recent_df = df.sort_values("created_at", ascending=False).head(10)
    st.table(recent_df[["chunk_id", "doc_id", "embedding_model", "created_at", "last_healed"]])

    # --- 5️⃣ Healing Suggestions JSON ---
    st.subheader("🛠 Healing Suggestions")
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
