"""
LangGraph Middleware for Chat Integration

Intercepts chat commands, handles file uploads, and seamlessly integrates
with LangGraph workflow without breaking existing ingestion/retrieval pipelines.
"""

import os
import json
import asyncio
from typing import Any, Dict, Callable, Optional
from pathlib import Path
import tempfile
from datetime import datetime


class ChatMiddleware:
    """Middleware for processing chat-specific operations in LangGraph"""
    
    def __init__(self, agent_invoke_fn: Callable):
        """
        Initialize middleware
        
        Args:
            agent_invoke_fn: The agent.invoke() method from LangGraph
        """
        self.agent_invoke_fn = agent_invoke_fn
        self.temp_dir = tempfile.gettempdir()
    
    async def process_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state for chat-specific operations
        
        Handles:
        - File upload to temp storage
        - Command routing
        - Session context
        - Response mode application
        
        Returns modified state ready for agent processing
        """
        
        # Extract chat metadata if present
        action = state.get("action", "query")
        response_mode = state.get("response_mode", "concise")
        user_context = state.get("user_context", {})
        session_id = state.get("session_id", "default")
        
        # Apply user context to state
        if user_context:
            state.update({
                "user_id": user_context.get("user_id"),
                "department": user_context.get("department"),
                "role": user_context.get("role"),
                "is_admin": user_context.get("mode") == "admin"
            })
        
        # Apply response mode
        state["response_mode"] = response_mode
        
        # Process action-specific state modifications
        if action == "query":
            # Simple query - pass through
            pass
        
        elif action == "ingest":
            # File ingestion - prepare document path
            if "document_path" in state:
                state["document_path"] = str(Path(state["document_path"]).absolute())
            elif "document_text" in state:
                # For text ingestion, save to temp file
                temp_file = os.path.join(
                    self.temp_dir,
                    f"chat_ingest_{session_id}_{datetime.now().timestamp()}.txt"
                )
                with open(temp_file, "w") as f:
                    f.write(state["document_text"])
                state["document_path"] = temp_file
                state["_temp_file"] = temp_file
        
        elif action == "ingest_table":
            # Table ingestion - validate inputs
            if not state.get("table_name") or not state.get("database_path"):
                raise ValueError("table_name and database_path required for ingest_table")
        
        elif action == "heal":
            # Healing action - RL agent will handle
            if not state.get("doc_id") or state.get("current_quality") is None:
                raise ValueError("doc_id and current_quality required for heal")
        
        elif action == "optimize":
            # Optimization action
            if not state.get("doc_id"):
                raise ValueError("doc_id required for optimize")
        
        elif action == "check_health":
            # Health check
            if not state.get("doc_id"):
                raise ValueError("doc_id required for check_health")
        
        return state
    
    def cleanup_temp_files(self, state: Dict[str, Any]) -> None:
        """Clean up temporary files after processing"""
        if "_temp_file" in state:
            try:
                os.remove(state["_temp_file"])
            except Exception as e:
                print(f"Warning: Failed to cleanup temp file: {e}")


class ChatStateEnhancer:
    """Enhances state with chat-specific fields needed by LangGraph nodes"""
    
    @staticmethod
    def enhance_for_ingestion(state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance state for ingestion workflow"""
        enhanced = state.copy()
        
        # Ensure required fields for ingestion
        enhanced.setdefault("doc_id", f"chat_{datetime.now().timestamp()}")
        enhanced.setdefault("metadata", {})
        enhanced.setdefault("user_context", {})
        
        # Add chat-specific metadata
        if "session_id" in state:
            enhanced["metadata"]["session_id"] = state["session_id"]
        
        if "user_id" in state:
            enhanced["metadata"]["user_id"] = state["user_id"]
        
        # Response mode for classification
        enhanced["metadata"]["response_mode"] = state.get("response_mode", "concise")
        
        return enhanced
    
    @staticmethod
    def enhance_for_retrieval(state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance state for retrieval workflow"""
        enhanced = state.copy()
        
        # Ensure response mode
        enhanced.setdefault("response_mode", "concise")
        
        # Ensure user context for RBAC
        if "user_context" not in enhanced:
            enhanced["user_context"] = {
                "user_id": enhanced.get("user_id", "anonymous"),
                "department": enhanced.get("department", "general"),
                "role": enhanced.get("role", "user"),
                "mode": "admin" if enhanced.get("is_admin") else "user"
            }
        
        return enhanced
    
    @staticmethod
    def enhance_for_healing(state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance state for healing/optimization workflow"""
        enhanced = state.copy()
        
        # Ensure required fields for RL agent
        enhanced.setdefault("doc_id", "unknown")
        enhanced.setdefault("current_quality", 0.5)
        enhanced.setdefault("session_id", "default")
        
        return enhanced


class ResponseModeProcessor:
    """Processes responses based on selected response mode"""
    
    @staticmethod
    def process_answer(
        answer: str,
        response_mode: str,
        context: Optional[str] = None,
        sources: Optional[list] = None
    ) -> str:
        """Process answer based on response mode"""
        
        if response_mode == "concise":
            # For concise mode: only use first sentence or two
            sentences = answer.split(".")
            concise = ". ".join(sentences[:2]).strip()
            if not concise.endswith("."):
                concise += "."
            return concise
        
        elif response_mode == "verbose":
            # For verbose mode: add context and sources
            result = answer
            
            if context:
                result += f"\n\nContext:\n{context[:500]}..."
            
            if sources:
                result += f"\n\nSources:\n" + "\n".join([f"- {s}" for s in sources[:5]])
            
            return result
        
        elif response_mode == "internal":
            # For internal mode: include all details
            result = answer
            
            if context:
                result += f"\n\nFull Context:\n{context}"
            
            if sources:
                result += f"\n\nAll Sources:\n" + "\n".join([f"- {s}" for s in sources])
            
            return result
        
        else:
            return answer


class FileUploadHandler:
    """Handles file uploads in chat context"""
    
    def __init__(self, max_file_size_mb: int = 100):
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = {
            ".pdf", ".docx", ".txt", ".csv", ".xlsx", ".pptx", ".json"
        }
    
    def validate_file(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file for ingestion
        
        Returns: (is_valid, error_message)
        """
        path = Path(file_path)
        
        if not path.exists():
            return False, f"File not found: {file_path}"
        
        if not path.is_file():
            return False, f"Not a file: {file_path}"
        
        if path.suffix.lower() not in self.allowed_extensions:
            return False, f"Unsupported file type: {path.suffix}"
        
        if path.stat().st_size > self.max_file_size:
            return False, f"File too large: {path.stat().st_size / 1024 / 1024:.1f}MB (max {self.max_file_size_mb}MB)"
        
        return True, None
    
    def prepare_file_for_ingestion(
        self,
        file_path: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare file for ingestion"""
        
        is_valid, error = self.validate_file(file_path)
        if not is_valid:
            raise ValueError(error)
        
        path = Path(file_path)
        
        return {
            "document_path": str(path.absolute()),
            "doc_id": doc_id or f"doc_{path.stem}_{datetime.now().timestamp()}",
            "source_type": self._detect_source_type(path),
            "file_size": path.stat().st_size,
            "metadata": metadata or {}
        }
    
    @staticmethod
    def _detect_source_type(path: Path) -> str:
        """Detect source type from file extension"""
        ext = path.suffix.lower()
        
        if ext == ".pdf":
            return "pdf"
        elif ext == ".docx":
            return "docx"
        elif ext in [".txt"]:
            return "txt"
        elif ext in [".csv"]:
            return "csv"
        elif ext in [".xlsx", ".xls"]:
            return "xlsx"
        elif ext == ".pptx":
            return "pptx"
        elif ext == ".json":
            return "json"
        else:
            return "unknown"


class ChatCommandRouter:
    """Routes chat commands to appropriate workflow"""
    
    def __init__(self, agent_invoke_fn: Callable):
        self.agent_invoke_fn = agent_invoke_fn
        self.middleware = ChatMiddleware(agent_invoke_fn)
        self.enhancer = ChatStateEnhancer()
    
    async def route_command(self, command_type: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route command to appropriate workflow"""
        
        # Enhance state
        if command_type in ["ingest_file", "ingest_text", "ingest_table"]:
            state = self.enhancer.enhance_for_ingestion(state)
            state["action"] = command_type
        elif command_type in ["query", "rag_query"]:
            state = self.enhancer.enhance_for_retrieval(state)
            state["action"] = "query"
        elif command_type in ["heal", "optimize", "check_health"]:
            state = self.enhancer.enhance_for_healing(state)
            state["action"] = command_type
        
        # Process through middleware
        state = await self.middleware.process_state(state)
        
        # Invoke agent
        try:
            result = self.agent_invoke_fn(state)
            return {
                "status": "success",
                "result": result,
                "command_type": command_type
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "command_type": command_type
            }
        finally:
            # Cleanup
            self.middleware.cleanup_temp_files(state)


# Integration utility for LangGraph agent
def create_chat_router(agent_invoke_fn: Callable) -> ChatCommandRouter:
    """Factory function to create chat router"""
    return ChatCommandRouter(agent_invoke_fn)
