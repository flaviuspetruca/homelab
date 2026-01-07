# 🏠 Homelab Kubernetes Cluster

## k3s • Traefik • MetalLB • Longhorn • Pi-hole • Nextcloud • Cloudflared

This is my personal homelab running a fully self-hosted, production-grade Kubernetes stack using [k3s](https://k3s.io). It’s designed to be:

-   Lightweight
-   Secure
-   Remotely accessible (no exposed ports)
-   Cloud-native, with full containerization and declarative infrastructure

---

## 🧠 Why I Built This

I wanted a real-world platform to:

-   Host apps like **Nextcloud** and **Pi-hole**
-   Deep-dive into **Kubernetes** in a homelab setting
-   Enable **secure remote access** without exposing ports
-   Practice **DevOps**, GitOps, and modern self-hosting patterns

---

### 📦 Prerequisites

-   2+ machines (Raspberry Pis, NUCs, or x86 servers)
-   Ubuntu Server 22.04 installed
-   Static IPs set via DHCP or Netplan
-   Cloudflare-managed domain
-   At least one control plane node (HA supported with multiple control planes)

Install [Ubuntu Server 22.04](https://ubuntu.com/download/server) on each node.

---

## ⚡ Automated Setup with `homelab` CLI

For a faster and more consistent setup, you can use the included **`homelab` CLI tool**.
This wraps the manual setup steps into a streamlined workflow.

### 📦 Install Dependencies

Ensure Python 3.9+ is installed on your local machine:

```bash
git clone https://github.com/flaviuspetruca/homelab.git
cd homelab
pip install -r requirements.txt
```

### ⚡ Available Commands

```bash
python homelab --help
```

#### 🔧 Initialize Cluster

Sets up the base k3s cluster across nodes (control plane + workers):
Run this on all nodes.

```bash
python homelab init
```

This will:

-   Configure nodes
-   Install k3s with control plane and workers
-   Prepare prerequisites for Helm and Helmfile

#### 🚀 Deploy Applications

Deploys your chosen stack interactively:

```bash
python homelab deploy
```

This will:

-   Prompt for which components to install (Nextcloud, Pi-hole, etc.)
-   Apply Helmfile releases
-   Configure secrets and ingress as needed

---

## 🖥️ Manual Setup (Optional)

If you prefer fine-grained control, you can still follow the **manual setup** instructions below.

### 🖥️ Step 1: Install Ubuntu Server

Install [Ubuntu Server 22.04](https://ubuntu.com/download/server) on each node.

Post-install config:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl vim net-tools htop
```

Set a static IP via Netplan (optional):

```yaml
# /etc/netplan/00-installer-config.yaml
network:
    version: 2
    ethernets:
        eth0:
            addresses:
                - 192.168.1.10/24
            gateway4: 192.168.1.1
            nameservers:
                addresses: [1.1.1.1, 8.8.8.8]
```

```bash
sudo netplan apply
```

---

### ☸️ Step 2: Install k3s

#### On the first control plane node:

```bash
curl -sfL https://get.k3s.io | sh -s - server --cluster-init
```

Retrieve the node token:

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

#### On additional control plane nodes:

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL=https://<IP-of-first-server>:6443 \
  K3S_TOKEN=<node-token> \
  sh -s - server
```

#### On worker nodes:

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL=https://<IP-of-first-server>:6443 \
  K3S_TOKEN=<node-token> \
  sh -s - agent
```

---

### 📦 Step 3: Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

helm plugin install https://github.com/databus23/helm-diff
```

---

### 🛠️ Step 4: One-Time Setup

#### 🔑 Cloudflared Tunnel

Install cloudflared:

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

Authenticate and create the tunnel:

```bash
cloudflared tunnel login
cloudflared tunnel create homelab-tunnel
cloudflared tunnel route dns homelab-tunnel <subdomain.yourdomain.com>
```

Save credentials JSON and mount it as a secret:

```bash
kubectl create namespace cloudflared
kubectl create secret generic cloudflared-credentials \
  --from-file=credentials.json=~/.cloudflared/<tunnel>.json \
  -n cloudflared
```

---

#### 🔐 Longhorn UI Authentication

```bash
htpasswd -c ./auth longhornadmin
kubectl create secret generic basic-auth \
  -n longhorn-system \
  --from-literal=users='<output_from_htpasswd>'
```

---

#### 🧾 Nextcloud Secrets

```bash
kubectl create secret generic nextcloud-admin-creds \
  -n nextcloud \
  --from-literal=nextcloud-username=<username> \
  --from-literal=nextcloud-password=<password>
```

---

#### 🧰 Pi-hole Secrets

```bash
kubectl create secret generic pihole-creds \
  -n pihole \
  --from-literal=password=<admin-password>
```

---

### 📦 Step 5: Deploy Components with Helmfile

Install CRDs in phases to avoid race conditions:

```bash
helmfile -l name=cert-manager apply
kubectl wait --for=condition=Available --timeout=120s deployment/cert-manager -n cert-manager
helmfile -l name=cert-manager-extras apply

helmfile -l name=metallb apply
kubectl wait --for=condition=Available --timeout=120s deployment/controller -n metallb-system
helmfile -l name=metallb-extras apply
```

Then apply the rest:

```bash
helmfile apply
```

---

## 🧱 Core Components Explained

| Component       | Role                                                            |
| --------------- | --------------------------------------------------------------- |
| **k3s**         | Lightweight Kubernetes distro with containerd, no external etcd |
| **ArgoCD**      | GitOps engine for declarative, version-controlled deployments   |
| **MetalLB**     | LoadBalancer IP allocation for bare-metal clusters              |
| **Traefik**     | Ingress, routing, TLS with Let’s Encrypt                        |
| **Cloudflared** | Secure tunnels to Cloudflare, no exposed ports                  |
| **Pi-hole**     | DNS ad-blocking with Longhorn-backed persistence                |
| **Nextcloud**   | Private cloud storage & collaboration platform                  |
| **Longhorn**    | Replicated distributed storage across nodes                     |
