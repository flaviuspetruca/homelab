import shutil
from homelab.utils import (
    GENERATED_CUSTOM_CHARTS_DIR,
    GENERATED_VALUES_DIR,
    run_cmd,
    save_yaml,
    load_yaml,
)
from pathlib import Path
import click


def copy_custom_charts(
    selected_apps, src: Path, dest: Path = GENERATED_CUSTOM_CHARTS_DIR
):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for app in selected_apps:
        app_chart = src / f"{app}-extras"
        if app_chart.exists():
            shutil.copytree(app_chart, dest / f"{app}-extras")
            click.echo(f"📂 Copied {app_chart} → {dest / f'{app}-extras'}")


def create_namespace(app: str):
    run_cmd(
        f"kubectl create namespace {app} --dry-run=client -o yaml | kubectl apply -f -"
    )


def update_values_file(template_path: Path, overlays: dict):
    vals = load_yaml(template_path)
    vals.update(overlays)
    save_yaml(GENERATED_VALUES_DIR / template_path.name, vals)
