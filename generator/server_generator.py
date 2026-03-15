"""
Server Generator — Step 11c

Takes ToolDefinitions from the parser and generates an MCP server file
using the Jinja2 template.
"""

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Add parser folder to path
sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))
from openapi_parser import parse_openapi
from tool_generator import generate_tools


# ── Helper: build function signature string ──
def _build_func_params(tool) -> str:
    """Build the function parameter string like 'order_id: str, customer_id: str | None = None'"""
    parts = []
    # Required params first, then optional
    required = [p for p in tool.parameters if p.required]
    optional = [p for p in tool.parameters if not p.required]

    for p in required:
        py_type = "int" if p.param_type == "integer" else "str"
        parts.append(f"{p.name}: {py_type}")

    for p in optional:
        py_type = "int" if p.param_type == "integer" else "str"
        parts.append(f"{p.name}: {py_type} | None = None")

    return ", ".join(parts)


# ── Helper: build function body string ──
def _build_func_body(tool) -> str:
    """Build the function body that makes the HTTP request."""
    lines = []
    method = tool.method  # "GET", "POST", etc.
    path = tool.path      # "/orders/{order_id}"

    # Convert path params: /orders/{order_id} stays the same (Python f-string compatible)
    path_params = [p for p in tool.parameters if p.location == "path"]
    query_params = [p for p in tool.parameters if p.location == "query"]
    body_params = [p for p in tool.parameters if p.location == "body"]

    if method == "GET":
        if query_params:
            lines.append("params = {}")
            for p in query_params:
                lines.append(f"if {p.name} is not None:")
                lines.append(f'    params["{p.name}"] = {p.name}')
            lines.append(f'response = httpx.get(f"{{API_BASE}}{path}", params=params)')
        else:
            lines.append(f'response = httpx.get(f"{{API_BASE}}{path}")')
        lines.append("if response.status_code == 200:")
        lines.append("    return str(response.json())")
        lines.append('return f"Error {response.status_code}: {response.text}"')

    elif method == "POST":
        json_dict = ", ".join(f'"{p.name}": {p.name}' for p in body_params)
        lines.append("response = httpx.post(")
        lines.append(f'    f"{{API_BASE}}{path}",')
        lines.append(f"    json={{{json_dict}}},")
        lines.append(")")
        lines.append("if response.status_code == 201:")
        lines.append("    return str(response.json())")
        lines.append('return f"Error {response.status_code}: {response.text}"')

    elif method == "DELETE":
        lines.append(f'response = httpx.delete(f"{{API_BASE}}{path}")')
        lines.append("if response.status_code == 204:")
        lines.append('    return "Deleted successfully"')
        lines.append('return f"Error {response.status_code}: {response.text}"')

    elif method in ("PUT", "PATCH"):
        json_dict = ", ".join(f'"{p.name}": {p.name}' for p in body_params)
        lines.append(f"response = httpx.{method.lower()}(")
        lines.append(f'    f"{{API_BASE}}{path}",')
        lines.append(f"    json={{{json_dict}}},")
        lines.append(")")
        lines.append("if response.status_code == 200:")
        lines.append("    return str(response.json())")
        lines.append('return f"Error {response.status_code}: {response.text}"')

    return "\n".join(lines)


def generate_server(
    spec_path: str,
    output_path: str,
    server_name: str = "Generated MCP Server",
    api_base: str = "http://localhost:8000",
    port: int = 8001,
):
    """Generate an MCP server file from an OpenAPI spec."""
    # Step 1: Parse the spec
    endpoints = parse_openapi(spec_path)
    tools = generate_tools(endpoints)

    # Step 2: Prepare template data
    template_tools = []
    for tool in tools:
        template_tools.append({
            "func_name": tool.name,
            "func_params": _build_func_params(tool),
            "description": tool.description,
            "func_body": _build_func_body(tool),
        })

    # Step 3: Render the template
    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates")),
        keep_trailing_newline=True,
    )
    template = env.get_template("mcp_server.py.j2")

    result = template.render(
        server_name=server_name,
        api_base=api_base,
        port=port,
        tools=template_tools,
    )

    # Step 4: Write the output file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result)
    print(f"Generated MCP server: {output_path}")


# ── Quick test ──────────────────────────────────────
if __name__ == "__main__":
    generate_server(
        spec_path="specs/orders.yaml",
        output_path="generated/orders_mcp_server.py",
        server_name="Orders MCP Server",
        api_base="http://localhost:8000",
        port=8001,
    )