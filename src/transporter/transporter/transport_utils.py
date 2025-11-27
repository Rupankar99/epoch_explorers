import re


def build_incident_prompt_context(payload: dict) -> str:
    """Extract key fields from telemetry payload to create LLM-ready context."""

    print("inside utils")
    # Helper: safely extract nested dict values
    def get(d, *keys, default=None):
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, default)
            else:
                return default
        return d

    # Extract fields
    environment = get(payload, "tags", "Environment") or get(payload, "properties", "environment")
    cost_center = get(payload, "tags", "CostCenter")
    criticality = get(payload, "tags", "BusinessCriticality")
    data_classification = get(payload, "tags", "DataClassification")
    category = get(payload, "category")
    operation = get(payload, "operationName", "value")
    status_value = get(payload, "status", "value")
    status_code = get(payload, "properties", "statusCode")
    error_code = get(payload, "properties", "error", "code")
    error_message = get(payload, "properties", "error", "message")
    resource_id = get(payload, "resourceId")

    print(environment,"environment")
    
    # Extract region from resourceId (e.g., "prod-rg-southeastasia")
    region_match = re.search(r"prod-rg-([a-z0-9-]+)", resource_id or "", re.IGNORECASE)
    region = region_match.group(1) if region_match else "unknown"
    
    # Format key details into a readable LLM prompt block
    context_lines = [
        f"Region: {region}",
        f"Department / Cost Center: {cost_center or 'Unknown'}",
        f"Category: {category or 'N/A'}",
        f"Operation: {operation or 'N/A'}",
        f"Resource: {resource_id or 'N/A'}",
        f"Environment: {environment or 'Unknown'}",
        f"Business Criticality: {criticality or 'N/A'}",
        f"Data Classification: {data_classification or 'N/A'}",
        f"Status: {status_value or 'N/A'} (HTTP {status_code or 'N/A'})",
        f"Error Code: {error_code or 'N/A'}",
        f"Error Message: {error_message or 'N/A'}",
    ]
    
    # Return nicely formatted context block
    return "\n".join(context_lines)
        
