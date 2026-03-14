"""
Test: Full pipeline — YAML spec → Endpoints → Tool definitions.

Run with:  python tests/test_pipeline.py
"""

import sys
from pathlib import Path

# Add parser folder to path (same trick as tool_generator)
sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))

from openapi_parser import parse_openapi
from tool_generator import generate_tools


def test_pipeline():
    endpoints = parse_openapi("specs/orders.yaml")
    tools = generate_tools(endpoints)

    # We expect exactly 4 tools
    assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"

    # Check the tool names are what we expect
    tool_names = [t.name for t in tools]
    assert "get_order" in tool_names, "Missing get_order"
    assert "list_orders" in tool_names, "Missing list_orders"
    assert "create_order" in tool_names, "Missing create_order"
    assert "delete_order" in tool_names, "Missing delete_order"

    # Check create_order has 3 body parameters
    create_tool = [t for t in tools if t.name == "create_order"][0]
    assert len(create_tool.parameters) == 3, f"Expected 3 params, got {len(create_tool.parameters)}"
    assert create_tool.method == "POST"

    # Check get_order has 1 path parameter
    get_tool = [t for t in tools if t.name == "get_order"][0]
    assert len(get_tool.parameters) == 1
    assert get_tool.parameters[0].location == "path"

    print("All tests passed!")
    print(f"Pipeline: orders.yaml → {len(endpoints)} endpoints → {len(tools)} tools")
    for t in tools:
        print(f"  {t.name:20s} {t.method:8s} {t.path}")


if __name__ == "__main__":
    test_pipeline()