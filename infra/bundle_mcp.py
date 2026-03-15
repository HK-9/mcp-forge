"""
Bundle the MCP server Lambda deployment package.

Similar to bundle.py but includes the MCP SDK and its dependencies
instead of FastAPI.

Run:  python infra/bundle_mcp.py
"""

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BUNDLE_DIR = PROJECT_ROOT / "infra" / "mcp_lambda_bundle"
MCP_SERVER_DIR = PROJECT_ROOT / "mcp_server"


def bundle():
    # Clean previous bundle
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir()

    # MCP SDK dependencies for Lambda
    # mcp[cli] pulls in the full SDK; httpx for HTTP calls to the Orders API
    lambda_reqs = BUNDLE_DIR / "requirements.txt"
    lambda_reqs.write_text("mcp\nhttpx\nstarlette\nsse-starlette\nanyio\npydantic\nuvicorn\nmangum\n")

    print("Installing MCP Lambda dependencies (Linux x86_64)...")
    subprocess.run(
        [
            "pip", "install",
            "-r", str(lambda_reqs),
            "-t", str(BUNDLE_DIR),
            "--platform", "manylinux2014_x86_64",
            "--only-binary=:all:",
            "--python-version", "3.12",
            "--implementation", "cp",
            "--quiet",
        ],
        check=True,
    )
    lambda_reqs.unlink()  # Remove temp requirements file

    # Copy the mcp_server/ folder
    print("Copying mcp_server/ folder...")
    shutil.copytree(
        MCP_SERVER_DIR,
        BUNDLE_DIR / "mcp_server",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    print(f"Bundle ready at: {BUNDLE_DIR}")


if __name__ == "__main__":
    bundle()
