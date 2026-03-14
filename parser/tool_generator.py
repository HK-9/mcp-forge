"""
Tool Name Generator — Step 7

Converts parsed Endpoint objects into clean MCP tool names.

Mapping logic:
  GET    /orders/{order_id}  →  get_order     (singular, because it's one item)
  GET    /orders             →  list_orders   (plural, because it's a collection)
  POST   /orders             →  create_order
  DELETE /orders/{order_id}  →  delete_order
  PUT    /orders/{order_id}  →  update_order
"""

from dataclasses import dataclass, field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from openapi_parser import Endpoint, Parameter, parse_openapi


def _singularize(word: str) -> str:
    """Naive singularization: just strip trailing 's'.
    
    Good enough for PoC. Real projects use a library like 'inflect'.
    """
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _get_resource_name(path: str) -> tuple[str, bool]:
    """Extract the resource name from a path and whether it targets a single item.
    
    '/orders/{order_id}' → ('orders', True)   — single item
    '/orders'            → ('orders', False)  — collection
    """
    segments = [s for s in path.split("/") if s]  # remove empty strings from leading /
    
    # Check if last segment is a path parameter like {order_id}
    is_single = segments[-1].startswith("{") if segments else False
    
    # The resource name is the last non-parameter segment
    for seg in reversed(segments):
        if not seg.startswith("{"):
            return seg, is_single
    
    return "resource", is_single


def generate_tool_name(endpoint: Endpoint) -> str:
    """Generate a clean tool name from an Endpoint.
    
    Examples:
      GET /orders/{order_id}  →  get_order
      GET /orders             →  list_orders
      POST /orders            →  create_order
    """
    resource, is_single = _get_resource_name(endpoint.path)
    method = endpoint.method.lower()
    
    if method == "get":
        if is_single:
            return f"get_{_singularize(resource)}"
        else:
            return f"list_{resource}"
    elif method == "post":
        return f"create_{_singularize(resource)}"
    elif method == "put" or method == "patch":
        return f"update_{_singularize(resource)}"
    elif method == "delete":
        return f"delete_{_singularize(resource)}"
    else:
        return f"{method}_{_singularize(resource)}"


@dataclass
class ToolDefinition:
    """A fully resolved MCP tool — ready to be used for code generation later."""
    name: str
    description: str
    method: str
    path: str
    parameters: list[Parameter] = field(default_factory=list)


def generate_tools(endpoints: list[Endpoint]) -> list[ToolDefinition]:
    """Convert a list of Endpoints into a list of ToolDefinitions."""
    tools = []
    for ep in endpoints:
        tool = ToolDefinition(
            name=generate_tool_name(ep),
            description=ep.summary,
            method=ep.method.upper(),
            path=ep.path,
            parameters=ep.parameters,
        )
        tools.append(tool)
    return tools


# ── Quick test ──────────────────────────────────────
if __name__ == "__main__":
    endpoints = parse_openapi("specs/orders.yaml")
    tools = generate_tools(endpoints)

    for tool in tools:
        print(f"\n🔧 {tool.name}")
        print(f"   {tool.method} {tool.path}")
        print(f"   \"{tool.description}\"")
        for p in tool.parameters:
            print(f"   param: {p.name} ({p.location}, {p.param_type}, required={p.required})")