from __future__ import annotations
import os, platform
from pathlib import Path

ENV_STATE = "HB_NODE_STATE_PATH"

def canonical_state_path() -> Path:
    if platform.system() == "Windows":
        root = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return root / "HashBurst" / "Node" / "identity"
    return Path("/var/lib/hashburst/node/identity")

def resolve_state_path(cli_value: str | None = None, config_value: str | None = None) -> tuple[Path, str]:
    if cli_value:
        return Path(cli_value).expanduser(), "cli"
    if os.environ.get(ENV_STATE):
        return Path(os.environ[ENV_STATE]).expanduser(), "environment"
    if config_value:
        return Path(config_value).expanduser(), "config"
    return canonical_state_path(), "canonical-default"