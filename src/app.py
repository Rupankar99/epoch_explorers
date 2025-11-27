import streamlit as st
from dotenv import load_dotenv
from pages import rag_matrics_report,settings,rag_metadata_report,chunk_embedding_report

load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Rag Metrics", "Rag Metadata","Chunk Embedding","Settings"]
)

st.sidebar.divider()
st.sidebar.info("💡 Select a page from above to get started")

# Route to appropriate page
if page == "Rag Metrics":
    rag_matrics_report.show()
elif page == "Rag Metadata":
    rag_metadata_report.show()
    
elif page == "Chunk Embedding":
    chunk_embedding_report.show()

elif page == "Settings":
    settings.show()
