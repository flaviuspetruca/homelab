import click
import yaml
from pathlib import Path

# base dir for your values
VALUES_DIR = Path(__file__).parent / "values"

# mapping apps -> values file
APP_FILES = {
    "nextcloud": VALUES_DIR / "values-nextcloud.yaml",
    "pihole": VALUES_DIR / "values-pihole.yaml",
    "argocd": VALUES_DIR / "values-argocd.yaml",
    # add more as needed
}


def load_yaml(path: Path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_yaml(path: Path, data: dict):
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False)


@click.group()
def cli():
    """Homelab CLI for bootstrapping and configuring apps."""
    pass


@cli.command()
@click.argument("app")
def configure(app):
    """Configure values for a given APP (e.g., nextcloud, pihole)."""
    if app not in APP_FILES:
        click.echo(f"❌ Unknown app: {app}")
        return

    values_file = APP_FILES[app]
    if not values_file.exists():
        click.echo(f"❌ Missing values file: {values_file}")
        return

    values = load_yaml(values_file)

    # Example: nextcloud config
    if app == "nextcloud":
        username = click.prompt("Nextcloud admin username", default="admin")
        password = click.prompt("Nextcloud admin password", hide_input=True)
        domain = click.prompt("Domain for Nextcloud", default="nextcloud.local")

        # overwrite
        values["nextcloud"]["username"] = username
        values["nextcloud"]["password"] = password
        values["nextcloud"]["host"] = domain

    elif app == "pihole":
        password = click.prompt("Pi-hole web password", hide_input=True)
        values["adminPassword"] = password

    # TODO: add other apps similarly

    save_yaml(values_file, values)
    click.echo(f"✅ Updated {values_file} for {app}")


if __name__ == "__main__":
    cli()
