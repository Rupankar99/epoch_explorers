"""
Chat Interface Modules

Provides unified chat protocol across all access methods:
- Streamlit UI (web)
- FastAPI (HTTP API)
- CLI (command line)
- Direct Python import
"""

from .chat_interface import (
    ChatRAGInterface,
    ChatSession,
    ChatMessage,
    ChatCommand,
    ChatCommandType,
    ChatResponse,
    ChatMode,
    ResponseMode
)

from .chat_middleware import (
    ChatMiddleware,
    ChatStateEnhancer,
    ResponseModeProcessor,
    FileUploadHandler,
    ChatCommandRouter,
    create_chat_router
)

__all__ = [
    # Interface
    "ChatRAGInterface",
    "ChatSession",
    "ChatMessage",
    "ChatCommand",
    "ChatCommandType",
    "ChatResponse",
    "ChatMode",
    "ResponseMode",
    # Middleware
    "ChatMiddleware",
    "ChatStateEnhancer",
    "ResponseModeProcessor",
    "FileUploadHandler",
    "ChatCommandRouter",
    "create_chat_router"
]
