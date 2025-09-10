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

## ⚙️ Architecture Overview

This stack is composed of tightly integrated, cloud-native components:

| Component       | Role                                             |
| --------------- | ------------------------------------------------ |
| **ArgoCD**      | Continuous deployment & GitOps                   |
| **k3s**         | Lightweight Kubernetes distro                    |
| **MetalLB**     | LoadBalancer for bare-metal networking           |
| **Traefik**     | Ingress controller, TLS, routing                 |
| **Cloudflared** | Encrypted remote tunnel access                   |
| **Longhorn**    | Distributed persistent storage                   |
| **Pi-hole**     | DNS-level ad blocking                            |
| **Nextcloud**   | Private cloud with file sync, calendar, and more |

---

## 🔧 Installation Guide

### 📦 Prerequisites

-   2+ machines (Raspberry Pis, NUCs, or x86 servers)
-   Ubuntu Server 22.04 installed
-   Static IPs set via DHCP or Netplan
-   Cloudflare-managed domain
-   At least one control plane node (HA supported with multiple control planes)

---

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

The `--cluster-init` flag initializes the datastore, allowing HA with multiple control plane nodes.

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

#### 🔑 1. Install Cloudflared & Configure Tunnel

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

Save the credentials JSON and mount it as a secret:

```bash
kubectl create namespace cloudflared
kubectl create secret generic cloudflared-credentials \
  --from-file=credentials.json=~/.cloudflared/<tunnel>.json \
  -n cloudflared
```

Optionally, create a ConfigMap for ingress rules:

```bash
kubectl create configmap cloudflared-ingress \
  --from-file=config.yaml=./cloudflared-config.yaml \
  -n cloudflared
```

---

#### 🔐 2. Longhorn UI Authentication

Longhorn lacks built-in auth, so secure the UI with Traefik middleware and basic auth.

```bash
htpasswd -c ./auth longhornadmin
kubectl create secret generic basic-auth \
  -n longhorn-system \
  --from-literal=users='<output_from_htpasswd>'
```

---

#### 🧾 3. Nextcloud Secrets

```bash
kubectl create secret generic nextcloud-admin-creds \
  -n nextcloud \
  --from-literal=nextcloud-username=<username> \
  --from-literal=nextcloud-password=<password>

kubectl create secret generic nextcloud-mariadb-secret \
  -n nextcloud \
  --from-literal=mariadb-root-password=<rootpass> \
  --from-literal=mariadb-password=<dbpass>
```

---

#### 🧰 4. Pi-hole Secrets

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

-   **k3s** – Lightweight Kubernetes distro with containerd, no external etcd
-   **ArgoCD** – GitOps engine for declarative, version-controlled deployments
-   **MetalLB** – LoadBalancer IP allocation for bare-metal clusters
-   **Traefik** – Ingress, routing, TLS with Let’s Encrypt
-   **Cloudflared** – Secure tunnels to Cloudflare, no exposed ports
-   **Pi-hole** – DNS ad-blocking with Longhorn-backed persistence
-   **Nextcloud** – Private cloud storage & collaboration platform
-   **Longhorn** – Replicated distributed storage across nodes

---

## 🛠 Tooling & Workflow

| Tool           | Role                               |
| -------------- | ---------------------------------- |
| **Helm**       | Package & deploy charts            |
| **Helmfile**   | Manage multiple Helm releases      |
| **ArgoCD**     | GitOps-driven sync of manifests    |
| **Cloudflare** | DNS + secure tunnels               |
| **Longhorn**   | Persistent volume management       |
| **Git**        | Source of truth for infrastructure |

---

## 🔐 Secrets Management

Secrets are managed via Kubernetes and templated into Helm values:

-   `nextcloud-admin-creds`
-   `nextcloud-mariadb-secret`
-   `pihole-creds`
-   `cloudflared-credentials`
-   `basic-auth` (for Longhorn UI)

---

✅ Fixed typos (`fazes → phases`, worker join command),
✅ Clarified node roles (control plane vs. worker),
✅ Added missing `cloudflared` installation,
✅ Smoothed the installation order for CRDs,
✅ Improved readability and structure.
