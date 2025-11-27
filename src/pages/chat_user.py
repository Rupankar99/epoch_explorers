"""
User-facing Chat Page
Simple, clean interface for asking questions
"""

import streamlit as st
from datetime import datetime
import json


def show():
    """Render user chat page"""
    st.set_page_config(
        page_title="Chat - RAG Assistant",
        page_icon="💬",
        layout="wide"
    )
    
    st.title("💬 RAG Assistant Chat")
    st.markdown("Ask questions about your knowledge base")
    
    # Initialize session state
    if "user_messages" not in st.session_state:
        st.session_state.user_messages = []
    if "user_response_mode" not in st.session_state:
        st.session_state.user_response_mode = "concise"
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        response_mode = st.radio(
            "Response Style",
            ["concise", "verbose"],
            format_func=lambda x: {
                "concise": "📌 Brief & Clear",
                "verbose": "📚 Detailed"
            }[x],
            help="Choose how detailed the answers should be"
        )
        st.session_state.user_response_mode = response_mode
        
        st.divider()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.user_messages = []
            st.rerun()
        
        if st.button("📥 Export Chat", use_container_width=True):
            if st.session_state.user_messages:
                export_data = json.dumps(
                    st.session_state.user_messages,
                    indent=2,
                    default=str
                )
                st.download_button(
                    "Download",
                    export_data,
                    f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
        
        st.divider()
        st.caption(f"Messages: {len(st.session_state.user_messages)}")
    
    # Chat messages
    for msg in st.session_state.user_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("metadata"):
                st.caption(f"Quality: {msg['metadata'].get('retrieval_quality', 0):.1%}")
    
    # Chat input
    if user_input := st.chat_input("Ask me anything...", key="user_input"):
        # Add user message
        st.session_state.user_messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get response
        with st.spinner("🔍 Searching..."):
            try:
                from src.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent
                
                agent = LangGraphRAGAgent()
                result = agent.ask_question(
                    question=user_input,
                    response_mode=st.session_state.user_response_mode
                )
                
                if result.get("success"):
                    answer = result.get("answer", "Sorry, I couldn't find an answer.")
                    
                    msg = {
                        "role": "assistant",
                        "content": answer,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if st.session_state.user_response_mode == "verbose":
                        msg["metadata"] = {
                            "retrieval_quality": result.get("retrieval_quality", 0),
                            "sources": len(result.get("source_docs", []))
                        }
                    
                    st.session_state.user_messages.append(msg)
                    st.rerun()
                else:
                    st.error("Failed to get answer. Please try again.")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    show()
