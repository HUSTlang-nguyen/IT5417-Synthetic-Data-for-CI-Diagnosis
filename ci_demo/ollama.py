"""Small local HTTP client; no credentials and no cloud fallback."""
from __future__ import annotations
import json
import time
import urllib.request
from urllib.parse import urlsplit

GENERATOR_MODEL = "qwen2.5-coder:7b-instruct"
# Future diagnosis/SFT checkpoint identity; this is not an Ollama generation tag.
DIAGNOSTIC_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
OPTIONS = {"temperature": 0.2, "seed": 5417, "num_ctx": 4096, "num_predict": 1536}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "path": {"type": "string", "enum": ["properr/__init__.py"]},
        "content": {"type": "string"},
        "proposed_label": {"type": "string", "enum": ["logic", "import", "syntax", "other"]},
        "explanation": {"type": "string"},
    }, "required": ["path", "content", "proposed_label", "explanation"],
}

def endpoint_url(endpoint):
    parsed = urlsplit(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Only a local HTTP Ollama endpoint is supported.")
    if parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("Endpoint must be a local origin, without credentials or path.")
    return endpoint.rstrip("/")

def request(endpoint, path, payload=None, timeout=600):
    base = endpoint_url(endpoint)
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000: raise ValueError("Model response too large")
    return raw.decode("utf-8")

def model_info(endpoint, model):
    tags = json.loads(request(endpoint, "/api/tags", timeout=15))
    entry = next((x for x in tags.get("models", []) if x.get("name") == model or x.get("model") == model), None)
    if entry is None: raise RuntimeError("Model not downloaded: " + model)
    details = json.loads(request(endpoint, "/api/show", {"model": model}, timeout=15))
    return {"tag": entry, "details": details}

def schema_for_path(path):
    import copy
    schema = copy.deepcopy(SCHEMA)
    schema["properties"]["path"]["enum"] = [path]
    return schema

def generate(endpoint, model, prompt, attempt, *, allowed_file=None, timeout=600):
    if model != GENERATOR_MODEL:
        raise ValueError("Generation requires the configured 7B generator.")
    payload = {
        "model": model, "stream": False, "format": schema_for_path(allowed_file) if allowed_file else SCHEMA,
        "messages": [{"role": "user", "content": prompt}],
        "options": {**OPTIONS, "seed": OPTIONS["seed"] + attempt},
        "keep_alive": 0,
    }
    start = time.monotonic()
    raw = request(endpoint, "/api/chat", payload) if timeout == 600 else request(endpoint, "/api/chat", payload, timeout=timeout)
    return payload, raw, round(time.monotonic() - start, 3)
