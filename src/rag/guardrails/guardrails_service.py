"""
Guardrails Service - Response Validation & Safety Agent

Validates RAG responses against multiple guardrails:
- Hallucination detection (is response grounded in context?)
- Security policies (no sensitive data leakage?)
- Factual accuracy (can responses be verified?)
- Appropriate tone (is response appropriate?)
- Completeness (does response answer the question?)

Works as separate service/agent to ensure clean separation of concerns.
Can be implemented as:
1. Separate tool call pipeline
2. Validation layer after response generation
3. Concurrent safety check service
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional
from langchain_core.tools import tool
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for guardrail violations."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailViolation:
    """Represents a guardrail violation."""
    
    def __init__(self, guardrail_type: str, risk_level: RiskLevel, message: str, details: Dict = None):
        """
        Initialize violation.
        
        Args:
            guardrail_type: Type of guardrail (hallucination, security, etc.)
            risk_level: Risk level of violation
            message: Human-readable message
            details: Additional details
        """
        self.guardrail_type = guardrail_type
        self.risk_level = risk_level
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "guardrail_type": self.guardrail_type,
            "risk_level": self.risk_level.value,
            "message": self.message,
            "details": self.details
        }


class GuardrailsService:
    """Service for validating RAG responses."""
    
    def __init__(self, llm_service=None):
        """
        Initialize guardrails service.
        
        Args:
            llm_service: LLMService for semantic validation
        """
        self.llm_service = llm_service
        self.violations: List[GuardrailViolation] = []
    
    # ========================================================================
    # GUARDRAIL 1: HALLUCINATION DETECTION
    # ========================================================================
    
    def check_hallucination(self, response: str, context: str, question: str) -> Tuple[bool, GuardrailViolation]:
        """
        Detect if response is hallucinating (making up information).
        
        Checks:
        - Is response grounded in provided context?
        - Are key facts in response present in context?
        - Are there unsupported claims?
        
        Args:
            response: Generated response
            context: Retrieved context documents
            question: Original question
        
        Returns:
            Tuple: (is_valid, violation_if_any)
        """
        try:
            if not self.llm_service:
                return True, None
            
            # Use LLM to check hallucination
            hallucination_prompt = f"""
Analyze if the response is grounded in the provided context.
A response is hallucinating if it makes up facts not present in the context.

QUESTION: {question}

CONTEXT:
{context[:1000]}  # First 1000 chars

RESPONSE:
{response}

Respond with ONLY valid JSON:
{{
    "is_hallucinating": false,
    "hallucinated_claims": [],
    "grounding_score": 0.95,
    "explanation": "Response is well-grounded in provided context"
}}

Grounding Score: 1.0 = fully grounded, 0.0 = complete hallucination
"""
            
            result = self.llm_service.generate_response(hallucination_prompt)
            analysis = json.loads(result)
            
            if analysis.get("is_hallucinating"):
                risk_level = RiskLevel.HIGH if len(analysis.get("hallucinated_claims", [])) > 2 else RiskLevel.MEDIUM
                violation = GuardrailViolation(
                    "hallucination",
                    risk_level,
                    "Response contains unsupported claims",
                    {
                        "hallucinated_claims": analysis.get("hallucinated_claims", []),
                        "grounding_score": analysis.get("grounding_score", 0)
                    }
                )
                return False, violation
            
            return True, None
        
        except json.JSONDecodeError:
            # If LLM parsing fails, use simpler heuristics
            return self._simple_hallucination_check(response, context)
        except Exception as e:
            # Fail open on errors
            print(f"Hallucination check error: {e}")
            return True, None
    
    def _simple_hallucination_check(self, response: str, context: str) -> Tuple[bool, GuardrailViolation]:
        """Simple heuristic hallucination check."""
        response_lower = response.lower()
        context_lower = context.lower()
        
        # Check if key phrases from response are in context
        words = set(response_lower.split())
        context_words = set(context_lower.split())
        
        # If most response words are in context, likely not hallucinating
        covered = len(words & context_words) / max(len(words), 1)
        
        if covered < 0.3:  # Less than 30% overlap
            violation = GuardrailViolation(
                "hallucination",
                RiskLevel.MEDIUM,
                "Response coverage of context is low",
                {"coverage_score": covered}
            )
            return False, violation
        
        return True, None
    
    # ========================================================================
    # GUARDRAIL 2: SECURITY & SENSITIVE DATA
    # ========================================================================
    
    def check_security(self, response: str) -> Tuple[bool, GuardrailViolation]:
        """
        Check for security policy violations.
        
        Detects:
        - Personal Identifiable Information (PII): emails, phone, SSN, credit cards
        - Internal credentials: passwords, API keys, tokens
        - Sensitive patterns: unauthorized access attempts
        
        Args:
            response: Generated response
        
        Returns:
            Tuple: (is_safe, violation_if_any)
        """
        violations_found = []
        
        # Check for email addresses (PII)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, response):
            violations_found.append(("PII - Email Address", RiskLevel.HIGH))
        
        # Check for phone numbers
        phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        if re.search(phone_pattern, response):
            violations_found.append(("PII - Phone Number", RiskLevel.HIGH))
        
        # Check for social security numbers
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, response):
            violations_found.append(("PII - SSN", RiskLevel.CRITICAL))
        
        # Check for credit card numbers
        cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        if re.search(cc_pattern, response):
            violations_found.append(("PII - Credit Card", RiskLevel.CRITICAL))
        
        # Check for API keys / passwords
        if re.search(r'(api[_-]?key|password|token|secret|credential)[\s:=]+\S+', response, re.IGNORECASE):
            violations_found.append(("Security - API/Password Exposure", RiskLevel.CRITICAL))
        
        # Check for SQL injection patterns
        if re.search(r"(\bUNION\b|\bSELECT\b.*\bWHERE\b|\bDROP\b.*\bTABLE\b)", response, re.IGNORECASE):
            violations_found.append(("Security - SQL Patterns", RiskLevel.MEDIUM))
        
        if violations_found:
            max_risk = max(v[1] for v in violations_found)
            violation = GuardrailViolation(
                "security",
                max_risk,
                "Response contains sensitive/security-sensitive data",
                {
                    "violations": [{"type": v[0], "risk": v[1].value} for v in violations_found]
                }
            )
            return False, violation
        
        return True, None
    
    # ========================================================================
    # GUARDRAIL 3: FACTUAL ACCURACY
    # ========================================================================
    
    def check_factual_accuracy(self, response: str, context: str) -> Tuple[bool, GuardrailViolation]:
        """
        Check factual accuracy of response against context.
        
        Extracts claims and verifies them against context facts.
        
        Args:
            response: Generated response
            context: Retrieved context
        
        Returns:
            Tuple: (is_accurate, violation_if_any)
        """
        if not self.llm_service:
            return True, None
        
        try:
            accuracy_prompt = f"""
Extract factual claims from the response and verify them against the context.
A claim is verified if it appears supported in the context.

CONTEXT:
{context[:1000]}

RESPONSE:
{response}

Respond with ONLY valid JSON:
{{
    "claims": [
        {{"claim": "...", "verified": true, "confidence": 0.95}},
        {{"claim": "...", "verified": false, "confidence": 0.8}}
    ],
    "accuracy_score": 0.95,
    "unverified_critical_claims": []
}}
"""
            
            result = self.llm_service.generate_response(accuracy_prompt)
            analysis = json.loads(result)
            
            accuracy_score = analysis.get("accuracy_score", 1.0)
            unverified = analysis.get("unverified_critical_claims", [])
            
            if accuracy_score < 0.7 or unverified:
                violation = GuardrailViolation(
                    "factual_accuracy",
                    RiskLevel.MEDIUM,
                    f"Response has accuracy score {accuracy_score}",
                    {
                        "accuracy_score": accuracy_score,
                        "unverified_claims": unverified
                    }
                )
                return False, violation
            
            return True, None
        
        except Exception as e:
            # Fail open on errors
            print(f"Accuracy check error: {e}")
            return True, None
    
    # ========================================================================
    # GUARDRAIL 4: TONE & APPROPRIATENESS
    # ========================================================================
    
    def check_tone(self, response: str, question: str) -> Tuple[bool, GuardrailViolation]:
        """
        Check if response tone is appropriate.
        
        Detects:
        - Offensive or discriminatory language
        - Sarcasm or inappropriate humor
        - Excessive negativity
        - Inappropriate expertise claims
        
        Args:
            response: Generated response
            question: Original question
        
        Returns:
            Tuple: (is_appropriate, violation_if_any)
        """
        if not self.llm_service:
            return True, None
        
        try:
            tone_prompt = f"""
Analyze if the response tone is appropriate and professional.

QUESTION: {question}

RESPONSE:
{response}

Respond with ONLY valid JSON:
{{
    "is_appropriate": true,
    "tone_issues": [],
    "contains_offensive_language": false,
    "contains_excessive_uncertainty": false,
    "contains_harmful_advice": false,
    "recommendations": []
}}
"""
            
            result = self.llm_service.generate_response(tone_prompt)
            analysis = json.loads(result)
            
            if not analysis.get("is_appropriate"):
                issues = analysis.get("tone_issues", [])
                risk_level = RiskLevel.HIGH if analysis.get("contains_harmful_advice") else RiskLevel.MEDIUM
                
                violation = GuardrailViolation(
                    "tone",
                    risk_level,
                    "Response tone or content is inappropriate",
                    {
                        "issues": issues,
                        "contains_offensive": analysis.get("contains_offensive_language", False),
                        "contains_uncertainty": analysis.get("contains_excessive_uncertainty", False)
                    }
                )
                return False, violation
            
            return True, None
        
        except Exception as e:
            print(f"Tone check error: {e}")
            return True, None
    
    # ========================================================================
    # GUARDRAIL 5: COMPLETENESS
    # ========================================================================
    
    def check_completeness(self, response: str, question: str) -> Tuple[bool, GuardrailViolation]:
        """
        Check if response adequately answers the question.
        
        Args:
            response: Generated response
            question: Original question
        
        Returns:
            Tuple: (is_complete, violation_if_any)
        """
        if not self.llm_service:
            return True, None
        
        try:
            completeness_prompt = f"""
Does the response adequately answer the question? What information is missing?

QUESTION: {question}

RESPONSE:
{response}

Respond with ONLY valid JSON:
{{
    "answers_question": true,
    "completeness_score": 0.95,
    "missing_information": [],
    "recommendation": "Response adequately addresses the question"
}}

Completeness Score: 1.0 = fully answers, 0.0 = completely off-topic
"""
            
            result = self.llm_service.generate_response(completeness_prompt)
            analysis = json.loads(result)
            
            if not analysis.get("answers_question") or analysis.get("completeness_score", 1.0) < 0.5:
                violation = GuardrailViolation(
                    "completeness",
                    RiskLevel.LOW,
                    "Response may not fully answer the question",
                    {
                        "completeness_score": analysis.get("completeness_score", 0),
                        "missing": analysis.get("missing_information", [])
                    }
                )
                return False, violation
            
            return True, None
        
        except Exception as e:
            print(f"Completeness check error: {e}")
            return True, None
    
    # ========================================================================
    # COMPREHENSIVE VALIDATION
    # ========================================================================
    
    def validate_response(
        self,
        response: str,
        context: str,
        question: str,
        check_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive response validation.
        
        Args:
            response: Generated response
            context: Retrieved context
            question: Original question
            check_types: Specific checks to run (None = all)
        
        Returns:
            Dict with validation results
        """
        if check_types is None:
            check_types = ["hallucination", "security", "accuracy", "tone", "completeness"]
        
        checks = {}
        max_risk = RiskLevel.SAFE
        
        # Run each check
        if "hallucination" in check_types:
            valid, violation = self.check_hallucination(response, context, question)
            checks["hallucination"] = {"valid": valid, "violation": violation.to_dict() if violation else None}
            if violation and violation.risk_level.value > max_risk.value:
                max_risk = violation.risk_level
        
        if "security" in check_types:
            valid, violation = self.check_security(response)
            checks["security"] = {"valid": valid, "violation": violation.to_dict() if violation else None}
            if violation and violation.risk_level.value > max_risk.value:
                max_risk = violation.risk_level
        
        if "accuracy" in check_types:
            valid, violation = self.check_factual_accuracy(response, context)
            checks["accuracy"] = {"valid": valid, "violation": violation.to_dict() if violation else None}
            if violation and violation.risk_level.value > max_risk.value:
                max_risk = violation.risk_level
        
        if "tone" in check_types:
            valid, violation = self.check_tone(response, question)
            checks["tone"] = {"valid": valid, "violation": violation.to_dict() if violation else None}
            if violation and violation.risk_level.value > max_risk.value:
                max_risk = violation.risk_level
        
        if "completeness" in check_types:
            valid, violation = self.check_completeness(response, question)
            checks["completeness"] = {"valid": valid, "violation": violation.to_dict() if violation else None}
            if violation and violation.risk_level.value > max_risk.value:
                max_risk = violation.risk_level
        
        # Determine if response is safe
        is_safe = all(c["valid"] for c in checks.values())
        
        return {
            "is_safe": is_safe,
            "max_risk_level": max_risk.value,
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
            "recommendation": self._get_recommendation(is_safe, max_risk)
        }
    
    def _get_recommendation(self, is_safe: bool, max_risk: RiskLevel) -> str:
        """Get recommendation based on validation results."""
        if is_safe:
            return "Response is safe to return to user"
        elif max_risk == RiskLevel.CRITICAL:
            return "BLOCK: Response poses critical risk. Do not return to user."
        elif max_risk == RiskLevel.HIGH:
            return "REVIEW: Response has high-risk issues. Consider manual review before returning."
        elif max_risk == RiskLevel.MEDIUM:
            return "WARN: Response has medium-risk issues. Consider flagging to user."
        else:
            return "INFO: Response has minor issues but can be returned."


# ============================================================================
# TOOL WRAPPER
# ============================================================================

@tool
def validate_response_tool(
    response: str,
    context: str,
    question: str,
    llm_service=None,
    check_types: List[str] = None
) -> str:
    """
    Validate RAG response against multiple guardrails.
    
    Args:
        response: Generated response
        context: Retrieved context
        question: Original question
        llm_service: LLM service for semantic checks
        check_types: Specific checks to run
    
    Returns:
        JSON string with validation results
    """
    try:
        service = GuardrailsService(llm_service)
        result = service.validate_response(response, context, question, check_types)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    # Example usage
    guardrails = GuardrailsService()
    
    response = "The company was founded in 1995 by John Smith."
    context = "Our company was established in 1995."
    question = "When was the company founded?"
    
    result = guardrails.validate_response(response, context, question)
    print(json.dumps(result, indent=2))
