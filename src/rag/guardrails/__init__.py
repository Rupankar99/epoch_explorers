"""RAG Guardrails module - Response validation and safety checking."""

from .guardrails_service import GuardrailsService, RiskLevel, GuardrailViolation, validate_response_tool
from .custom_guardrails import CustomGuardrails, SafetyLevel

__all__ = [
    # ============================================================================
    # GUARDRAILS-AI Library (when available)
    # ============================================================================
    "GuardrailsService",
    "RiskLevel",
    "GuardrailViolation",
    "validate_response_tool",
    
    # ============================================================================
    # CUSTOM GUARDRAILS (Simple, effective, no external dependencies)
    # ============================================================================
    "CustomGuardrails",
    "SafetyLevel",
]
