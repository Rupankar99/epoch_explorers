"""
Chat-Enhanced RAG Interface

Provides unified chat protocol across all access methods (Streamlit, API, CLI, direct import).
Supports dual modes: Admin (ingestion, healing, optimization) and User (retrieval, Q&A).
Seamlessly integrates with existing LangGraph agent without breaking changes.
"""

import json
import uuid
import time
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from pathlib import Path


class ChatMode(Enum):
    """Chat mode enum"""
    USER = "user"           # Query and retrieval only
    ADMIN = "admin"         # Full access: ingest, optimize, heal


class ResponseMode(Enum):
    """Response generation mode"""
    CONCISE = "concise"     # 1-2 sentences, public only
    VERBOSE = "verbose"     # Detailed with context, public+internal
    INTERNAL = "internal"   # Full details, all levels, role required


class ChatCommandType(Enum):
    """Chat command types"""
    # Retrieval commands (user + admin)
    QUERY = "query"                    # Ask question: "query: what is budget?"
    RAG_QUERY = "rag_query"           # Query with RAG: "rag_query: ...?"
    
    # Ingestion commands (admin only)
    INGEST_FILE = "ingest_file"       # Ingest file: "ingest_file: /path/to/file.pdf"
    INGEST_TEXT = "ingest_text"       # Ingest text: "ingest_text: document text content"
    INGEST_TABLE = "ingest_table"     # Ingest table: "ingest_table: table_name db_path"
    
    # Healing/Optimization (admin only)
    HEAL = "heal"                      # Heal document: "heal: doc_id quality_score"
    OPTIMIZE = "optimize"              # Optimize: "optimize: doc_id"
    CHECK_HEALTH = "check_health"      # Check embedding health: "check_health: doc_id"
    
    # Configuration
    SET_MODE = "set_mode"              # Set response mode: "set_mode: concise|verbose|internal"
    SET_CHAT_MODE = "set_chat_mode"   # Switch mode: "set_chat_mode: admin|user"
    GET_STATUS = "get_status"          # Get system status
    HELP = "help"                      # Show help
    CLEAR = "clear"                    # Clear session


@dataclass
class ChatMessage:
    """Unified chat message format"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sender: str = "user"               # "user" or "agent"
    content: str = ""
    mode: ChatMode = ChatMode.USER
    response_mode: ResponseMode = ResponseMode.CONCISE
    command_type: Optional[ChatCommandType] = None
    
    # Metadata
    session_id: str = ""
    user_id: str = ""
    department: str = ""
    role: str = ""
    
    # For responses
    status: str = "pending"            # pending|processing|success|error
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatCommand:
    """Parsed chat command"""
    command_type: ChatCommandType
    raw_input: str
    args: List[str]
    kwargs: Dict[str, Any]
    
    @staticmethod
    def parse(text: str) -> Tuple[Optional['ChatCommand'], Optional[str]]:
        """Parse chat text into command
        
        Returns: (ChatCommand, error_message) - one will be None
        """
        text = text.strip()
        
        # Help and status commands
        if text.lower() in ["help", "/help", "?"]:
            return ChatCommand(ChatCommandType.HELP, text, [], {}), None
        
        if text.lower() in ["status", "/status"]:
            return ChatCommand(ChatCommandType.GET_STATUS, text, [], {}), None
        
        if text.lower() in ["clear", "/clear"]:
            return ChatCommand(ChatCommandType.CLEAR, text, [], {}), None
        
        # Mode commands
        if text.lower().startswith("set_mode:") or text.lower().startswith("mode:"):
            mode_str = text.split(":", 1)[1].strip().lower()
            if mode_str not in ["concise", "verbose", "internal"]:
                return None, f"Invalid response mode: {mode_str}"
            return ChatCommand(ChatCommandType.SET_MODE, text, [mode_str], {}), None
        
        if text.lower().startswith("set_chat_mode:") or text.lower().startswith("chat_mode:"):
            mode_str = text.split(":", 1)[1].strip().lower()
            if mode_str not in ["admin", "user"]:
                return None, f"Invalid chat mode: {mode_str}"
            return ChatCommand(ChatCommandType.SET_CHAT_MODE, text, [mode_str], {}), None
        
        # Multi-part commands (admin commands)
        for cmd_prefix, cmd_type in [
            ("ingest_file:", ChatCommandType.INGEST_FILE),
            ("ingest_text:", ChatCommandType.INGEST_TEXT),
            ("ingest_table:", ChatCommandType.INGEST_TABLE),
            ("heal:", ChatCommandType.HEAL),
            ("optimize:", ChatCommandType.OPTIMIZE),
            ("check_health:", ChatCommandType.CHECK_HEALTH),
        ]:
            if text.lower().startswith(cmd_prefix):
                args_str = text.split(":", 1)[1].strip()
                args = [arg.strip() for arg in args_str.split("|")]
                return ChatCommand(cmd_type, text, args, {}), None
        
        # RAG query commands
        if text.lower().startswith("rag_query:") or text.lower().startswith("rag:"):
            query = text.split(":", 1)[1].strip()
            return ChatCommand(ChatCommandType.RAG_QUERY, text, [query], {}), None
        
        if text.lower().startswith("query:"):
            query = text.split(":", 1)[1].strip()
            return ChatCommand(ChatCommandType.QUERY, text, [query], {}), None
        
        # Default: treat as RAG query
        return ChatCommand(ChatCommandType.RAG_QUERY, text, [text], {}), None


@dataclass
class ChatResponse:
    """Unified chat response format"""
    message_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "success"            # success|error|pending
    content: str = ""
    command_type: Optional[ChatCommandType] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Metadata
    session_id: str = ""
    processing_time_ms: float = 0.0
    tokens_used: int = 0
    source_docs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, handling enums"""
        data = asdict(self)
        if self.command_type:
            data['command_type'] = self.command_type.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=2)


class ChatSession:
    """Manages chat session state and history"""
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        user_id: str = "anonymous",
        department: str = "general",
        role: str = "user",
        mode: ChatMode = ChatMode.USER
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.department = department
        self.role = role
        self.mode = mode
        self.response_mode = ResponseMode.CONCISE
        
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_history: List[ChatMessage] = []
        self.command_history: List[ChatCommand] = []
        self.context: Dict[str, Any] = {
            "last_doc_id": None,
            "last_query": None,
            "ingested_files": [],
            "healed_docs": []
        }
    
    def is_admin(self) -> bool:
        """Check if session is in admin mode"""
        return self.mode == ChatMode.ADMIN
    
    def add_message(self, message: ChatMessage) -> None:
        """Add message to history"""
        message.session_id = self.session_id
        message.user_id = self.user_id
        message.department = self.department
        message.role = self.role
        self.message_history.append(message)
        self.last_activity = datetime.now()
    
    def add_command(self, command: ChatCommand) -> None:
        """Add command to history"""
        self.command_history.append(command)
    
    def set_response_mode(self, mode: ResponseMode) -> None:
        """Change response mode"""
        self.response_mode = mode
    
    def set_chat_mode(self, mode: ChatMode) -> None:
        """Change chat mode (admin/user)"""
        self.mode = mode
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "department": self.department,
            "role": self.role,
            "mode": self.mode.value,
            "response_mode": self.response_mode.value,
            "last_doc_id": self.context["last_doc_id"],
            "last_query": self.context["last_query"],
            "ingested_files": self.context["ingested_files"],
            "healed_docs": self.context["healed_docs"]
        }
    
    def update_context(self, **kwargs) -> None:
        """Update context fields"""
        for key, value in kwargs.items():
            if key in self.context:
                self.context[key] = value


class ChatRAGInterface:
    """Main chat interface bridging all access methods"""
    
    def __init__(self, agent_invoke_fn: Callable):
        """
        Initialize chat interface
        
        Args:
            agent_invoke_fn: Function to invoke RAG agent (from langgraph_rag_agent.invoke)
        """
        self.agent_invoke_fn = agent_invoke_fn
        self.sessions: Dict[str, ChatSession] = {}
        self._doc_id_cache: Dict[str, str] = {}  # Cache to check for duplicates
    
    def _generate_doc_id(
        self,
        source_type: str,
        source_name: str,
        custom_doc_id: Optional[str] = None
    ) -> str:
        """
        Automatically generate unique doc_id based on source.
        
        Args:
            source_type: "file" | "text" | "table" | "url"
            source_name: filename, table_name, or URL string
            custom_doc_id: Optional custom doc_id (overrides auto-generation)
        
        Returns:
            Unique doc_id with format: prefix_source_timestamp
        
        Examples:
            file_budget_report_20250128_153045
            text_user_input_20250128_153045
            table_knowledge_base_20250128_153045
        """
        import re
        import hashlib
        
        # Allow custom override
        if custom_doc_id:
            return self._ensure_unique_doc_id(custom_doc_id)
        
        # Sanitize source_name (remove special chars, lowercase, replace spaces)
        sanitized = re.sub(r'[^a-z0-9_\-.]', '_', source_name.lower())
        # Remove file extension for cleaner doc_id
        sanitized = re.sub(r'\.[^.]*$', '', sanitized)
        # Replace multiple underscores with single
        sanitized = re.sub(r'_+', '_', sanitized)
        # Limit length
        sanitized = sanitized[:30]
        
        # Prefix by source type
        prefixes = {
            "file": "file",
            "text": "text_user_input",
            "table": "table",
            "url": "url"
        }
        
        prefix = prefixes.get(source_type, "doc")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_doc_id = f"{prefix}_{sanitized}_{timestamp}"
        return self._ensure_unique_doc_id(base_doc_id)
    
    def _ensure_unique_doc_id(self, base_doc_id: str) -> str:
        """
        Ensure doc_id is truly unique by checking cache and incrementing if needed.
        
        Args:
            base_doc_id: Base doc_id to check/increment
        
        Returns:
            Unique doc_id (may have counter suffix if collision detected)
        """
        doc_id = base_doc_id
        counter = 0
        
        # Check cache (in-memory session tracking)
        while doc_id in self._doc_id_cache:
            counter += 1
            microseconds = int(time.time() * 1_000_000) % 1_000_000
            doc_id = f"{base_doc_id}_{microseconds}_{counter}"
        
        # Add to cache
        self._doc_id_cache[doc_id] = datetime.now().isoformat()
        
        return doc_id
    
    def create_session(
        self,
        user_id: str = "anonymous",
        department: str = "general",
        role: str = "user",
        mode: ChatMode = ChatMode.USER
    ) -> ChatSession:
        """Create new chat session"""
        session = ChatSession(
            user_id=user_id,
            department=department,
            role=role,
            mode=mode
        )
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    async def process_message(
        self,
        text: str,
        session_id: str,
        **agent_kwargs
    ) -> ChatResponse:
        """
        Process chat message through RAG agent
        
        Args:
            text: Chat input text
            session_id: Session ID
            **agent_kwargs: Additional kwargs for agent.invoke()
        
        Returns:
            ChatResponse with result or error
        """
        session = self.get_session(session_id)
        if not session:
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                status="error",
                error=f"Session not found: {session_id}"
            )
        
        # Parse command
        command, parse_error = ChatCommand.parse(text)
        if parse_error:
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                status="error",
                error=parse_error
            )
        
        # Create message
        msg = ChatMessage(
            sender="user",
            content=text,
            mode=session.mode,
            response_mode=session.response_mode,
            command_type=command.command_type if command else None,
            session_id=session_id,
            user_id=session.user_id,
            department=session.department,
            role=session.role
        )
        session.add_message(msg)
        
        # Process command
        start_time = time.time()
        
        if not command:
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                status="error",
                error="Failed to parse command"
            )
        
        session.add_command(command)
        
        try:
            # Handle different command types
            if command.command_type == ChatCommandType.HELP:
                response_text = self._get_help_text(session)
                return ChatResponse(
                    message_id=msg.message_id,
                    session_id=session_id,
                    status="success",
                    content=response_text,
                    command_type=command.command_type,
                    processing_time_ms=time.time() - start_time
                )
            
            elif command.command_type == ChatCommandType.GET_STATUS:
                status_text = self._get_status_text(session)
                return ChatResponse(
                    message_id=msg.message_id,
                    session_id=session_id,
                    status="success",
                    content=status_text,
                    command_type=command.command_type,
                    processing_time_ms=time.time() - start_time
                )
            
            elif command.command_type == ChatCommandType.SET_MODE:
                mode = ResponseMode[command.args[0].upper()]
                session.set_response_mode(mode)
                return ChatResponse(
                    message_id=msg.message_id,
                    session_id=session_id,
                    status="success",
                    content=f"✓ Response mode set to: {mode.value}",
                    command_type=command.command_type,
                    processing_time_ms=time.time() - start_time
                )
            
            elif command.command_type == ChatCommandType.SET_CHAT_MODE:
                if not session.is_admin():
                    # Non-admins cannot switch to admin mode
                    if command.args[0].lower() == "admin":
                        return ChatResponse(
                            message_id=msg.message_id,
                            session_id=session_id,
                            status="error",
                            error="Permission denied: Admin mode requires elevated privileges",
                            command_type=command.command_type,
                            processing_time_ms=time.time() - start_time
                        )
                
                mode = ChatMode[command.args[0].upper()]
                session.set_chat_mode(mode)
                return ChatResponse(
                    message_id=msg.message_id,
                    session_id=session_id,
                    status="success",
                    content=f"✓ Chat mode set to: {mode.value}",
                    command_type=command.command_type,
                    processing_time_ms=time.time() - start_time
                )
            
            elif command.command_type == ChatCommandType.CLEAR:
                session.message_history = []
                session.command_history = []
                session.context = {
                    "last_doc_id": None,
                    "last_query": None,
                    "ingested_files": [],
                    "healed_docs": []
                }
                return ChatResponse(
                    message_id=msg.message_id,
                    session_id=session_id,
                    status="success",
                    content="✓ Session cleared",
                    command_type=command.command_type,
                    processing_time_ms=time.time() - start_time
                )
            
            # Admin-only commands
            if not session.is_admin() and command.command_type in [
                ChatCommandType.INGEST_FILE,
                ChatCommandType.INGEST_TEXT,
                ChatCommandType.INGEST_TABLE,
                ChatCommandType.HEAL,
                ChatCommandType.OPTIMIZE,
                ChatCommandType.CHECK_HEALTH
            ]:
                return ChatResponse(
                    message_id=msg.message_id,
                    session_id=session_id,
                    status="error",
                    error=f"Permission denied: {command.command_type.value} requires admin mode",
                    command_type=command.command_type,
                    processing_time_ms=time.time() - start_time
                )
            
            # Delegate to agent
            result = await self._invoke_agent(
                command=command,
                session=session,
                **agent_kwargs
            )
            
            session.update_context(last_query=text)
            
            return ChatResponse(
                message_id=msg.message_id,
                session_id=session_id,
                status="success" if result.get("status") == "success" else "error",
                content=result.get("content", ""),
                command_type=command.command_type,
                result=result.get("result"),
                error=result.get("error"),
                processing_time_ms=time.time() - start_time,
                tokens_used=result.get("tokens_used", 0),
                source_docs=result.get("source_docs", [])
            )
        
        except Exception as e:
            return ChatResponse(
                message_id=msg.message_id,
                session_id=session_id,
                status="error",
                error=f"Agent error: {str(e)}",
                command_type=command.command_type,
                processing_time_ms=time.time() - start_time
            )
    
    async def _invoke_agent(
        self,
        command: ChatCommand,
        session: ChatSession,
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke RAG agent based on command type"""
        
        # Build agent state from command
        state = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "department": session.department,
            "role": session.role,
            "response_mode": session.response_mode.value,
            "user_context": session.get_context(),
            **kwargs
        }
        
        try:
            if command.command_type == ChatCommandType.QUERY:
                state["query"] = command.args[0]
                result = self.agent_invoke_fn(state)
                return {
                    "status": "success",
                    "content": result.get("answer", ""),
                    "result": result,
                    "source_docs": result.get("source_docs", [])
                }
            
            elif command.command_type == ChatCommandType.RAG_QUERY:
                state["query"] = command.args[0]
                result = self.agent_invoke_fn(state)
                return {
                    "status": "success",
                    "content": result.get("answer", ""),
                    "result": result,
                    "source_docs": result.get("source_docs", []),
                    "tokens_used": result.get("tokens_used", 0)
                }
            
            elif command.command_type == ChatCommandType.INGEST_FILE:
                if not command.args:
                    return {"status": "error", "error": "File path required"}
                
                file_path = command.args[0]
                
                # Auto-generate doc_id from filename
                filename = Path(file_path).name
                auto_doc_id = self._generate_doc_id("file", filename)
                
                state["document_path"] = file_path
                state["doc_id"] = auto_doc_id  # Provide auto-generated doc_id
                state["action"] = "ingest"
                
                result = self.agent_invoke_fn(state)
                session.context["ingested_files"].append({
                    "path": file_path,
                    "doc_id": auto_doc_id,
                    "ingested_at": datetime.now().isoformat()
                })
                session.context["last_doc_id"] = auto_doc_id
                
                return {
                    "status": "success",
                    "content": f"✓ Ingested: {file_path}\n   doc_id: {auto_doc_id}",
                    "result": {**result, "doc_id": auto_doc_id}
                }
            
            elif command.command_type == ChatCommandType.INGEST_TEXT:
                if not command.args:
                    return {"status": "error", "error": "Text content required"}
                
                text_content = command.args[0]
                
                # Auto-generate doc_id for text input
                auto_doc_id = self._generate_doc_id("text", "user_input")
                
                state["document_text"] = text_content
                state["doc_id"] = auto_doc_id  # Provide auto-generated doc_id
                state["action"] = "ingest"
                
                result = self.agent_invoke_fn(state)
                session.context["ingested_files"].append({
                    "type": "text",
                    "doc_id": auto_doc_id,
                    "ingested_at": datetime.now().isoformat()
                })
                session.context["last_doc_id"] = auto_doc_id
                
                return {
                    "status": "success",
                    "content": f"✓ Ingested text content\n   doc_id: {auto_doc_id}",
                    "result": {**result, "doc_id": auto_doc_id}
                }
            
            elif command.command_type == ChatCommandType.INGEST_TABLE:
                if len(command.args) < 1:
                    return {"status": "error", "error": "Table name required"}
                
                table_name = command.args[0]
                db_path = command.args[1] if len(command.args) > 1 else None
                
                # Auto-generate doc_id from table name
                auto_doc_id = self._generate_doc_id("table", table_name)
                
                state["table_name"] = table_name
                if db_path:
                    state["database_path"] = db_path
                state["doc_id"] = auto_doc_id  # Provide auto-generated doc_id
                state["action"] = "ingest_table"
                
                result = self.agent_invoke_fn(state)
                session.context["ingested_files"].append({
                    "type": "table",
                    "table_name": table_name,
                    "doc_id": auto_doc_id,
                    "ingested_at": datetime.now().isoformat()
                })
                session.context["last_doc_id"] = auto_doc_id
                
                return {
                    "status": "success",
                    "content": f"✓ Ingested table: {table_name}\n   doc_id: {auto_doc_id}",
                    "result": {**result, "doc_id": auto_doc_id}
                }
            
            elif command.command_type == ChatCommandType.HEAL:
                if len(command.args) < 2:
                    return {"status": "error", "error": "doc_id and quality_score required"}
                
                doc_id = command.args[0]
                quality = float(command.args[1])
                state["doc_id"] = doc_id
                state["current_quality"] = quality
                state["action"] = "heal"
                
                result = self.agent_invoke_fn(state)
                session.context["healed_docs"].append(doc_id)
                
                return {
                    "status": "success",
                    "content": f"✓ Healing started for {doc_id}",
                    "result": result
                }
            
            elif command.command_type == ChatCommandType.OPTIMIZE:
                if not command.args:
                    return {"status": "error", "error": "doc_id required"}
                
                doc_id = command.args[0]
                state["doc_id"] = doc_id
                state["action"] = "optimize"
                
                result = self.agent_invoke_fn(state)
                
                return {
                    "status": "success",
                    "content": f"✓ Optimization applied to {doc_id}",
                    "result": result
                }
            
            elif command.command_type == ChatCommandType.CHECK_HEALTH:
                if not command.args:
                    return {"status": "error", "error": "doc_id required"}
                
                doc_id = command.args[0]
                state["doc_id"] = doc_id
                state["action"] = "check_health"
                
                result = self.agent_invoke_fn(state)
                
                return {
                    "status": "success",
                    "content": f"✓ Health check completed",
                    "result": result
                }
            
            else:
                return {"status": "error", "error": f"Unknown command: {command.command_type.value}"}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_help_text(self, session: ChatSession) -> str:
        """Get help text based on session mode"""
        base_help = """
📚 RAG Chat Commands
====================

QUERY COMMANDS:
  query: <question>          - Simple question answering
  rag_query: <question>      - RAG-based question answering
  rag: <question>            - Shorthand for rag_query

MODE COMMANDS:
  set_mode: concise|verbose|internal    - Change response mode
  mode: concise|verbose|internal        - Shorthand
  set_chat_mode: admin|user             - Switch chat mode
  chat_mode: admin|user                 - Shorthand

SYSTEM COMMANDS:
  status                     - Show session status
  clear                      - Clear session history
  help                       - Show this help
"""
        
        admin_help = """
ADMIN COMMANDS (File Ingestion):
  ingest_file: <path>        - Ingest document file
  ingest_text: <content>     - Ingest text content
  ingest_table: <table>|<db> - Ingest database table

HEALING & OPTIMIZATION:
  heal: <doc_id>|<quality>   - Heal document (quality 0-1)
  optimize: <doc_id>         - Optimize document
  check_health: <doc_id>     - Check embedding health
"""
        
        if session.is_admin():
            return base_help + admin_help
        else:
            return base_help + "\n⚠️  Admin commands not available in user mode\n"
    
    def _get_status_text(self, session: ChatSession) -> str:
        """Get status text for session"""
        return f"""
📊 Session Status
=================
Session ID:      {session.session_id}
User:            {session.user_id} ({session.department}/{session.role})
Mode:            {session.mode.value.upper()}
Response Mode:   {session.response_mode.value}
Messages:        {len(session.message_history)}
Commands:        {len(session.command_history)}
Last Doc:        {session.context['last_doc_id'] or 'None'}
Ingested Files:  {len(session.context['ingested_files'])}
Healed Docs:     {len(session.context['healed_docs'])}
Created:         {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Last Activity:   {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}
"""
