import os, yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def str_to_bool(v):
    return str(v).lower() in ("true", "1", "yes", "on")

def build_config():
    # Layer 1: Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # Layer 2: YAML
    env_name = os.getenv("APP_ENV", "development")
    yaml_path = f"config.{env_name}.yaml"
    if os.path.exists(yaml_path):
        with open(yaml_path) as f:
            yaml_cfg = yaml.safe_load(f) or {}
        config.update(yaml_cfg)

    # Layer 3: .env file
    load_dotenv()
    if os.getenv("NUM_WORKERS"):
        config["workers"] = int(os.getenv("NUM_WORKERS"))

    # Layer 4: OS env vars with APP_ prefix
    mapping = {
        "APP_PORT":      "port",
        "APP_WORKERS":   "workers",
        "APP_DEBUG":     "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY":   "api_key",
    }
    for env_key, cfg_key in mapping.items():
        val = os.getenv(env_key)
        if val is not None:
            config[cfg_key] = val

    return config

@app.get("/effective-config")
async def effective_config(request: Request):
    config = build_config()

    # Layer 5: CLI overrides from ?set=key=value
    for item in request.query_params.getlist("set"):
        if "=" in item:
            k, v = item.split("=", 1)
            config[k] = v

    # Type coercion
    config["port"]    = int(config["port"])
    config["workers"] = int(config["workers"])
    config["debug"]   = str_to_bool(config["debug"])
    config["log_level"] = str(config["log_level"])

    # Mask api_key
    config["api_key"] = "****"

    return JSONResponse(content=config)
