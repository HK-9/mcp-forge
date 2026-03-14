"""
OpenAPI Parser — Step 6: Clean data structures.

Instead of just printing, we store parsed data in dataclasses.
A dataclass is like a struct — it holds named fields with types.
"""

from dataclasses import dataclass, field

import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@dataclass
class Parameter:
    """Represents one input to an API endpoint."""
    name: str
    location: str       # "path", "query", or "body"
    param_type: str     # "string", "integer", etc.
    required: bool
    description: str = ""


@dataclass
class Endpoint:
    """Represents one API operation (e.g., GET /orders/{order_id})."""
    path: str
    method: str         # "get", "post", etc.
    summary: str
    operation_id: str
    parameters: list[Parameter] = field(default_factory=list)


def load_spec(file_path: str) -> dict:
    """Load an OpenAPI YAML file and return it as a Python dict."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def resolve_ref(spec: dict, ref: str) -> dict:
    """Follow a $ref like '#/components/schemas/CreateOrderRequest'."""
    parts = ref.lstrip("#/").split("/")
    result = spec
    for part in parts:
        result = result[part]
    return result


def parse_parameters(operation: dict) -> list[Parameter]:
    """Extract path/query parameters from an operation."""
    params = []
    for p in operation.get("parameters", []):
        params.append(Parameter(
            name=p["name"],
            location=p["in"],
            param_type=p.get("schema", {}).get("type", "string"),
            required=p.get("required", False),
            description=p.get("schema", {}).get("title", ""),
        ))
    return params


def parse_request_body(operation: dict, spec: dict) -> list[Parameter]:
    """Extract request body fields as Parameters with location='body'."""
    params = []
    request_body = operation.get("requestBody")
    if not request_body:
        return params

    json_schema = request_body.get("content", {}).get("application/json", {}).get("schema", {})

    if "$ref" in json_schema:
        json_schema = resolve_ref(spec, json_schema["$ref"])

    required_fields = json_schema.get("required", [])
    for field_name, field_info in json_schema.get("properties", {}).items():
        params.append(Parameter(
            name=field_name,
            location="body",
            param_type=field_info.get("type", "string"),
            required=field_name in required_fields,
            description=field_info.get("description", ""),
        ))
    return params


def parse_openapi(file_path: str) -> list[Endpoint]:
    """Main function: parse an OpenAPI spec and return a list of Endpoints."""
    spec = load_spec(file_path)
    endpoints = []

    for path, path_item in spec["paths"].items():
        for method in path_item:
            if method not in HTTP_METHODS:
                continue

            operation = path_item[method]

            # Combine path/query params + body fields into one list
            all_params = parse_parameters(operation)
            all_params += parse_request_body(operation, spec)

            endpoint = Endpoint(
                path=path,
                method=method,
                summary=operation.get("summary", ""),
                operation_id=operation.get("operationId", ""),
                parameters=all_params,
            )
            endpoints.append(endpoint)

    return endpoints


# ── Quick test ──────────────────────────────────────
if __name__ == "__main__":
    endpoints = parse_openapi("specs/orders.yaml")

    for ep in endpoints:
        print(f"\n{ep.method.upper():8s} {ep.path}")
        print(f"         operation_id: {ep.operation_id}")
        print(f"         summary: {ep.summary}")
        for p in ep.parameters:
            print(f"         param: {p.name} (location={p.location}, type={p.param_type}, required={p.required})")