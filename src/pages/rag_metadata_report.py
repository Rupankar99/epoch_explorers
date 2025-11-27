import streamlit as st
import altair as alt
import pandas as pd
from database.models.document_metadata_model import DocumentMetadataModel
from database.db.connection import get_connection
import json

# --- Main App ---
def show():
    st.title("📄 Document Metadata Dashboard")

    # Load data
    conn = get_connection()
    doc_model = DocumentMetadataModel(conn)
    df = doc_model.get_all_documents()  # Should return a pandas DataFrame

    # --- Filters ---
    st.subheader("Filters")
    rbac_filter = st.multiselect("RBAC Namespace", df.rbac_namespace.unique(), df.rbac_namespace.unique())
    chunk_filter = st.multiselect("Chunk Strategy", df.chunk_strategy.unique(), df.chunk_strategy.unique())

    if rbac_filter:
        df = df[df.rbac_namespace.isin(rbac_filter)]
    if chunk_filter:
        df = df[df.chunk_strategy.isin(chunk_filter)]

    # --- 1️⃣ Document Count by RBAC Namespace ---
    st.subheader("📂 Document Count by RBAC Namespace")
    chart_rbac = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="rbac_namespace:N",
            y="count():Q",
            color="rbac_namespace:N",
            tooltip=["rbac_namespace", "count()"]
        )
    )
    st.altair_chart(chart_rbac, use_container_width=True)

    # --- 2️⃣ Chunking Strategy Distribution ---
    st.subheader("🔹 Chunking Strategy Distribution")
    chart_chunk = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="chunk_strategy:N",
            y="count():Q",
            color="chunk_strategy:N",
            tooltip=["chunk_strategy", "count()"]
        )
    )
    st.altair_chart(chart_chunk, use_container_width=True)

    # --- 3️⃣ Chunk Size / Overlap Metrics ---
    st.subheader("📏 Chunk Size vs Overlap")
    chunk_chart = (
        alt.Chart(df)
        .mark_circle(size=100)
        .encode(
            x="chunk_size_char:Q",
            y="overlap_char:Q",
            color="chunk_strategy:N",
            tooltip=["title", "chunk_size_char", "overlap_char", "chunk_strategy"]
        )
    )
    st.altair_chart(chunk_chart, use_container_width=True)

    # --- 4️⃣ Recently Ingested Documents ---
    st.subheader("🕒 Recently Ingested Documents")
    recent_df = df.sort_values("last_ingested", ascending=False).head(10)
    st.table(recent_df[["doc_id", "title", "author", "source", "last_ingested"]])

    # --- 5️⃣ JSON Metadata Inspection ---
    st.subheader("📝 Metadata JSON Insights")
    selected_doc = st.selectbox("Select Document", df.title)
    metadata_json_str = df[df.title == selected_doc]["metadata_json"].values[0]
    if metadata_json_str:
        try:
            metadata = json.loads(metadata_json_str)
            st.json(metadata)
        except Exception as e:
            st.warning(f"Invalid JSON: {e}")
    else:
        st.info("No metadata available for this document.")
