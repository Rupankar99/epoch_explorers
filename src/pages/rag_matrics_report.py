import streamlit as st
import altair as alt
from database.models.rag_history_model import RAGHistoryModel
from database.db.connection import get_connection

# --- Main App ---
def show():
    st.title("📊 RAG Observability Dashboard")

    conn = get_connection()
    rag_history= RAGHistoryModel(conn)
    df = rag_history.get_metrix()

    # Filters
    event_filter = st.multiselect("Event Type", df.event_type.unique())
    if event_filter:
        df = df[df.event_type.isin(event_filter)]

    # --- 1️⃣ Event Distribution ---
    st.subheader("Event Type Distribution")
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(x="event_type", y="count()", color="event_type")
    )
    st.altair_chart(chart, use_container_width=True)

    # --- 2️⃣ Accuracy (QUERY & SYNTHETIC_TEST) ---
    st.subheader("Accuracy Over Time")
    acc_df = df[df.event_type.isin(["QUERY", "SYNTHETIC_TEST"])].copy()
    acc_df["accuracy"] = acc_df["metrics"].apply(lambda m: m.get("accuracy"))
    acc_df = acc_df.dropna(subset=["accuracy"])

    line = (
        alt.Chart(acc_df)
        .mark_line(point=True)
        .encode(x="timestamp:T", y="accuracy:Q", color="event_type")
    )
    st.altair_chart(line, use_container_width=True)

    # --- 3️⃣ Latency ---
    st.subheader("Latency Over Time")
    acc_df["latency"] = acc_df["metrics"].apply(lambda m: m.get("latency"))
    lat = (
        alt.Chart(acc_df)
        .mark_line(point=True)
        .encode(x="timestamp:T", y="latency:Q", color="event_type")
    )
    st.altair_chart(lat, use_container_width=True)

    # --- 4️⃣ RL Agent Decisions ---
    st.subheader("RL Agent Actions")
    action_chart = (
        alt.Chart(df[df.action_taken.notnull()])
        .mark_bar()
        .encode(x="action_taken", y="count()", color="action_taken")
    )
    st.altair_chart(action_chart, use_container_width=True)

    # --- 5️⃣ Rewards ---
    st.subheader("Reward Signal Trend")
    rew = (
        alt.Chart(df.dropna(subset=["reward_signal"]))
        .mark_line(point=True)
        .encode(x="timestamp:T", y="reward_signal:Q")
    )
    st.altair_chart(rew, use_container_width=True)


