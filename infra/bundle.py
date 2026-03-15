"""
Bundle the Lambda deployment package.

Installs pip dependencies and copies the api/ folder into a single
directory that CDK can upload directly — no Docker needed.

Run:  python infra/bundle.py
"""

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BUNDLE_DIR = PROJECT_ROOT / "infra" / "lambda_bundle"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
API_DIR = PROJECT_ROOT / "api"


def bundle():
    # Clean previous bundle
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir()

    # Install only the dependencies Lambda needs (not mcp, click, jinja2, etc.)
    # Create a minimal requirements file for Lambda
    lambda_reqs = BUNDLE_DIR / "requirements.txt"
    lambda_reqs.write_text("fastapi\nuvicorn\npydantic\nmangum\n")

    print("Installing Lambda dependencies (Linux x86_64)...")
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
    lambda_reqs.unlink()  # Remove the temp requirements file

    # Copy the api/ folder
    print("Copying api/ folder...")
    shutil.copytree(API_DIR, BUNDLE_DIR / "api", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.db"))

    print(f"Bundle ready at: {BUNDLE_DIR}")


if __name__ == "__main__":
    bundle()
