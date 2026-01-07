import click
import yaml
from homelab.k3s import install_base_packages, install_k3s, install_helm
from homelab.helm import GENERATED_VALUES_DIR, copy_custom_charts, create_namespace
from homelab.release_mappings import APP_REPOS, HELMFILE_RELEASES
from homelab.utils import (
    CUSTOM_CHARTS_DIR,
    GENERATED_DIR,
    VALUES_DIR,
    load_yaml,
    save_yaml,
    ensure_dir,
)


@click.group()
def cli():
    """Homelab CLI – bootstrap and deploy your homelab cluster."""
    pass


@cli.command()
@click.option("--role", type=click.Choice(["control-plane", "worker"]), required=True)
def init(role):
    click.echo(f"🚀 Initializing node as {role}...")
    install_base_packages()
    if role == "worker":
        ip = click.prompt("Control-plane IP")
        token = click.prompt("Node token", hide_input=True)
        install_k3s(role, ip, token)
    else:
        install_k3s(role)
    install_helm()
    click.echo("✅ Node bootstrap complete.")


APP_FILES = {
    "argocd": VALUES_DIR / "values-argocd.yaml",
    "cert-manager": VALUES_DIR / "values-cert-manager.yaml",
    "longhorn": VALUES_DIR / "values-longhorn.yaml",
    "metallb": VALUES_DIR / "values-metallb.yaml",
    "nextcloud": VALUES_DIR / "values-nextcloud.yaml",
    "pihole": VALUES_DIR / "values-pihole.yaml",
}

# Data-driven configuration per app
APP_CONFIG = {
    "nextcloud": {
        "prompts": {
            "subdomain": ("Nextcloud subdomain", "nextcloud"),
            "storage": ("Nextcloud persistent storage size", "100Gi"),
            "db_root_pass": ("MariaDB root password", None, True),
            "db_user_pass": ("MariaDB nextcloud user password", None, True),
            "db_user": ("MariaDB nextcloud username", "nextcloud"),
        },
        "update_func": lambda vals, answers, domain: update_nextcloud(
            vals, answers, domain
        ),
    },
    "pihole": {
        "prompts": {"subdomain": ("Pi-hole subdomain", "pihole")},
        "update_func": lambda vals, answers, domain: vals.update(
            {"ingress": [{"host": f"{answers['subdomain']}.{domain}"}]}
        ),
    },
    "argocd": {
        "prompts": {"subdomain": ("ArgoCD hostname", "argocd")},
        "update_func": lambda vals, answers, domain: vals["server"]["ingress"].update(
            {
                "hostname": f"{answers['subdomain']}.{domain}",
                "hosts": [f"{answers['subdomain']}.{domain}"],
            }
        ),
    },
    "longhorn": {
        "prompts": {"replica_count": ("Longhorn default replica count", 2)},
        "update_func": lambda vals, answers, domain: vals["defaultSettings"].update(
            {"defaultReplicaCount": answers["replica_count"]}
        ),
    },
}


def update_nextcloud(vals, answers, domain):
    host = f"{answers['subdomain']}.{domain}"
    vals["nextcloud"]["host"] = host
    vals["nextcloud"]["trustedDomains"] = [
        host,
        "localhost",
        "nextcloud.nextcloud.svc.cluster.local",
        "nextcloud.local",
    ]
    vals["nextcloud"]["extraEnv"][0]["value"] = host
    vals["ingress"]["hosts"][0]["host"] = host
    vals["ingress"]["tls"][0]["hosts"] = [host]
    vals["persistence"]["size"] = answers["storage"]
    vals["mariadb"]["auth"].update(
        {
            "rootPassword": answers["db_root_pass"],
            "password": answers["db_user_pass"],
            "username": answers["db_user"],
        }
    )


GENERATED_HELMFILE = GENERATED_DIR / "helmfile.yaml"


def generate_helmfile(selected_apps):
    repos = []
    releases = []

    for app in selected_apps:
        # add repo if defined for this app
        repo = APP_REPOS.get(app)
        if repo and repo not in repos:
            repos.append(repo)

        # add releases for this app
        app_releases = HELMFILE_RELEASES.get(app, [])
        if not isinstance(app_releases, list):
            app_releases = [app_releases]

        for rel in app_releases:
            rel_copy = rel.copy()

            # fix paths to ./generated
            if "values" in rel_copy:
                rel_copy["values"] = [
                    v.replace("./values", "./generated/values").replace(
                        "./custom-charts", "./generated/custom-charts"
                    )
                    for v in rel_copy["values"]
                ]
            if "chart" in rel_copy and rel_copy["chart"].startswith("./custom-charts"):
                rel_copy["chart"] = rel_copy["chart"].replace(
                    "./custom-charts", "./generated/custom-charts"
                )

            releases.append(rel_copy)

    final = {"repositories": repos, "releases": releases}

    ensure_dir(GENERATED_DIR)
    with open(GENERATED_DIR / "helmfile.yaml", "w") as f:
        yaml.safe_dump(final, f, sort_keys=False)

    click.echo(f"✅ Wrote {GENERATED_DIR}/helmfile.yaml")


@cli.command()
def deploy():
    """Prompt for parameters and generate overlay values for Helmfile + custom charts."""
    click.echo("⚙️  Generating overlays...")

    domain = click.prompt("Base domain for the homelab, ex: example.com", type=str)

    # Select apps
    click.echo("Available apps to deploy:")
    for i, app in enumerate(APP_FILES.keys(), 1):
        click.echo(f"{i}. {app}")
    selected_input = click.prompt(
        "Enter the numbers of the apps to deploy, separated by commas (e.g., 1,3,5)",
        default=",".join(str(i) for i in range(1, len(APP_FILES) + 1)),
    )
    selected_indices = [
        int(x.strip()) for x in selected_input.split(",") if x.strip().isdigit()
    ]
    selected_apps = [
        list(APP_FILES.keys())[i - 1]
        for i in selected_indices
        if 0 < i <= len(APP_FILES)
    ]
    click.echo(f"✅ Selected apps: {', '.join(selected_apps)}")

    ensure_dir(GENERATED_VALUES_DIR)

    # Create namespaces and update values
    for app in selected_apps:
        create_namespace(app)
        template_path = APP_FILES[app]
        vals = load_yaml(template_path)

        if app in APP_CONFIG:
            # Prompt user for required fields
            answers = {}
            for key, prompt_data in APP_CONFIG[app]["prompts"].items():
                message = prompt_data[0]
                default = prompt_data[1]
                hide = prompt_data[2] if len(prompt_data) > 2 else False
                answers[key] = click.prompt(message, default=default, hide_input=hide)
            APP_CONFIG[app]["update_func"](vals, answers, domain)

        save_yaml(GENERATED_VALUES_DIR / template_path.name, vals)
        click.echo(f"✅ Wrote overlay for {app}")

    # Copy custom charts
    copy_custom_charts(selected_apps, CUSTOM_CHARTS_DIR)

    # Generate helmfile.yaml
    generate_helmfile(selected_apps)
    click.echo("\n📦 Deployment complete!")
