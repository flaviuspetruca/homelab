from homelab.utils import run_cmd


def install_base_packages():
    run_cmd("sudo apt update && sudo apt upgrade -y")
    run_cmd("sudo apt install -y curl vim net-tools htop")


def install_k3s(role, control_plane_ip=None, token=None):
    if role == "control-plane":
        run_cmd("curl -sfL https://get.k3s.io | sh -s - server --cluster-init")
    else:
        run_cmd(
            f"curl -sfL https://get.k3s.io | K3S_URL=https://{control_plane_ip}:6443 K3S_TOKEN={token} sh -s - agent"
        )


def install_helm():
    run_cmd(
        "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
    )
    run_cmd("helm plugin install https://github.com/databus23/helm-diff")
