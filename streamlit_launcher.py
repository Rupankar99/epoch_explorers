"""
Streamlit Application Launcher
Runs the LangGraph RAG Agent Dashboard

This file should be run with: streamlit run streamlit_launcher.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import the streamlit app module to execute it
import src.pages.streamlit_app  # noqa: F401

# Note: Importing the module triggers streamlit's execution
# All page configuration and UI code is defined in streamlit_app.py
