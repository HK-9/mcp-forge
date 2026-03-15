import json
import urllib.request
import yaml

response = urllib.request.urlopen("http://localhost:8002/openapi.json")
spec = json.loads(response.read())

with open("specs/payments.yaml", "w") as f:
    yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

print("Saved to specs/payments.yaml")