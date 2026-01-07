import subprocess
import yaml
from pathlib import Path
import os

BASE_DIR = Path(__file__).parent
VALUES_DIR = BASE_DIR / "values"
CUSTOM_CHARTS_DIR = BASE_DIR / "custom-charts"
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_VALUES_DIR = GENERATED_DIR / "values"
GENERATED_CUSTOM_CHARTS_DIR = GENERATED_DIR / "custom-charts"


def run_cmd(cmd: str):
    print(f"▶ {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def save_yaml(path: Path, data: dict):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False)


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
