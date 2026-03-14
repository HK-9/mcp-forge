"""
Fetches the OpenAPI spec from the running FastAPI app and saves it as YAML.

Why YAML? It's easier to read than JSON, and most OpenAPI specs in the wild are YAML.
"""
import json
import urllib.request

import yaml

# Fetch the auto-generated spec from FastAPI
response = urllib.request.urlopen("http://localhost:8000/openapi.json")
spec = json.loads(response.read())

# Save as YAML
with open("specs/orders.yaml", "w") as f:
    yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

print("Saved to specs/orders.yaml")