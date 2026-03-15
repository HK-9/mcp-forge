"""
MCP Forge CLI — the main entry point for the platform.

Commands:
    register  — Register an API by providing its OpenAPI spec URL
    generate  — Generate MCP server code from a registered API
    serve     — Start the gateway server with all registered APIs

Usage:
    python cli.py register --name orders --spec-url http://localhost:8000/openapi.json --api-base http://localhost:8000
    python cli.py register --name payments --spec-url http://localhost:8002/openapi.json --api-base http://localhost:8002
    python cli.py generate --name orders
    python cli.py generate --all
    python cli.py serve
"""

import json
import urllib.request
import sys
from pathlib import Path

import click
import yaml

# Add parser and generator to path
sys.path.insert(0, str(Path(__file__).parent / "parser"))
sys.path.insert(0, str(Path(__file__).parent / "generator"))

from server_generator import generate_server

REGISTRY_FILE = Path("registry.json")
SPECS_DIR = Path("specs")
GENERATED_DIR = Path("generated")


def _load_registry() -> dict:
    """Load the API registry from disk."""
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {}


def _save_registry(registry: dict):
    """Save the API registry to disk."""
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))


@click.group()
def cli():
    """MCP Forge — generate MCP servers from OpenAPI specs."""
    pass


@cli.command()
@click.option("--name", required=True, help="Short name for the API (e.g., orders)")
@click.option("--spec-url", required=True, help="URL to the OpenAPI JSON spec (e.g., http://localhost:8000/openapi.json)")
@click.option("--api-base", required=True, help="Base URL of the API (e.g., http://localhost:8000)")
def register(name: str, spec_url: str, api_base: str):
    """Register an API by fetching its OpenAPI spec."""
    click.echo(f"Fetching spec from {spec_url}...")

    try:
        response = urllib.request.urlopen(spec_url)
        spec = json.loads(response.read())
    except Exception as e:
        click.echo(f"Error fetching spec: {e}", err=True)
        return

    # Save spec as YAML
    SPECS_DIR.mkdir(exist_ok=True)
    spec_path = SPECS_DIR / f"{name}.yaml"
    with open(spec_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    click.echo(f"Saved spec to {spec_path}")

    # Update registry
    registry = _load_registry()
    registry[name] = {
        "spec_path": str(spec_path),
        "api_base": api_base,
        "spec_url": spec_url,
    }
    _save_registry(registry)
    click.echo(f"Registered API: {name}")


@cli.command()
@click.option("--name", default=None, help="Generate server for a specific API")
@click.option("--all", "gen_all", is_flag=True, help="Generate servers for all registered APIs")
def generate(name: str | None, gen_all: bool):
    """Generate MCP server code from registered API specs."""
    registry = _load_registry()

    if not registry:
        click.echo("No APIs registered. Use 'register' first.", err=True)
        return

    if gen_all:
        apis_to_generate = list(registry.keys())
    elif name:
        if name not in registry:
            click.echo(f"API '{name}' not found. Registered: {list(registry.keys())}", err=True)
            return
        apis_to_generate = [name]
    else:
        click.echo("Specify --name or --all", err=True)
        return

    GENERATED_DIR.mkdir(exist_ok=True)
    for api_name in apis_to_generate:
        config = registry[api_name]
        output_path = str(GENERATED_DIR / f"{api_name}_mcp_server.py")
        click.echo(f"Generating {output_path}...")
        generate_server(
            spec_path=config["spec_path"],
            output_path=output_path,
            server_name=f"{api_name.title()} MCP Server",
            api_base=config["api_base"],
        )

    click.echo("Done!")


@cli.command()
@click.option("--port", default=9000, help="Port for the gateway server")
def serve(port: int):
    """Start the MCP gateway with all registered APIs."""
    import importlib.util

    registry = _load_registry()
    if not registry:
        click.echo("No APIs registered. Use 'register' first.", err=True)
        return

    # Dynamically build the gateway
    import httpx
    from mcp.server.fastmcp import FastMCP
    from openapi_parser import parse_openapi
    from tool_generator import generate_tools

    gateway = FastMCP(
        name="MCP Forge Gateway",
        instructions="Unified MCP gateway for all registered APIs.",
        host="127.0.0.1",
        port=port,
    )

    for api_name, config in registry.items():
        click.echo(f"Loading API: {api_name}")
        endpoints = parse_openapi(config["spec_path"])
        tools = generate_tools(endpoints)

        for tool in tools:
            tool_name = f"{api_name}_{tool.name}"
            api_base = config["api_base"]

            # Build the tool caller
            def make_caller(t=tool, base=api_base):
                def caller(**kwargs) -> str:
                    path = t.path
                    for p in t.parameters:
                        if p.location == "path" and p.name in kwargs:
                            path = path.replace(f"{{{p.name}}}", str(kwargs[p.name]))

                    url = f"{base}{path}"
                    query = {p.name: kwargs[p.name] for p in t.parameters if p.location == "query" and p.name in kwargs and kwargs[p.name] is not None}
                    body = {p.name: kwargs[p.name] for p in t.parameters if p.location == "body" and p.name in kwargs}

                    if t.method == "GET":
                        r = httpx.get(url, params=query)
                    elif t.method == "POST":
                        r = httpx.post(url, json=body)
                    elif t.method == "DELETE":
                        r = httpx.delete(url)
                    elif t.method in ("PUT", "PATCH"):
                        r = httpx.request(t.method, url, json=body)
                    else:
                        return f"Unsupported: {t.method}"

                    if r.status_code in (200, 201):
                        return str(r.json())
                    elif r.status_code == 204:
                        return "Deleted successfully"
                    return f"Error {r.status_code}: {r.text}"

                caller.__name__ = tool_name
                caller.__doc__ = t.description
                annotations = {}
                for p in t.parameters:
                    py_type = int if p.param_type == "integer" else float if p.param_type == "number" else str
                    if not p.required:
                        py_type = py_type | None
                    annotations[p.name] = py_type
                annotations["return"] = str
                caller.__annotations__ = annotations
                caller.__defaults__ = tuple(None for p in t.parameters if not p.required) or None
                return caller

            gateway.tool()(make_caller())
            click.echo(f"  Tool: {tool_name}")

    click.echo(f"\nStarting MCP Forge Gateway on port {port}...")
    gateway.run()


if __name__ == "__main__":
    cli()