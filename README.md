---

# 🏠 Homelab Kubernetes Cluster

## k3s • Traefik • MetalLB • Longhorn • Pi-hole • Nextcloud • Cloudflared

This is my personal homelab running a fully self-hosted, production-grade Kubernetes stack using [k3s](https://k3s.io). It's designed to be:

- Lightweight
- Secure
- Remotely accessible (no exposed ports)
- Cloud-native, with full containerization and declarative infrastructure

---

## 🧠 Why I Built This

I wanted a real-world platform to:

- Host apps like **Nextcloud** and **Pi-hole**
- Deep-dive into **Kubernetes** in a homelab setting
- Enable **secure remote access** without exposing ports
- Practice **DevOps**, GitOps, and modern self-hosting patterns

---

## ⚙️ Architecture Overview

This stack is composed of tightly integrated, cloud-native components:

| Component     | Role |
|--------------|------|
| **argocd**   | Continuous deployment |
| **k3s**      | Lightweight Kubernetes distro |
| **MetalLB**  | LoadBalancer for bare-metal networking |
| **Traefik**  | Ingress controller, TLS, routing |
| **Cloudflared** | Encrypted remote tunnel access |
| **Longhorn** | Cloud-style distributed persistent storage |
| **Pi-hole**  | DNS-level ad blocking |
| **Nextcloud**| Private cloud with file sync, calendar, and more |

---

## 🔧 Installation Guide

### 📦 Prerequisites

- 2+ machines (RPis, NUCs, or x86 servers)
- Ubuntu Server 22.04 installed
- Static IPs set via DHCP or Netplan
- Cloudflare-managed domain

---

### 🖥️ Step 1: Install Ubuntu Server

Install [Ubuntu Server 22.04](https://ubuntu.com/download/server) on each node.

Post-install config:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl vim net-tools htop
```

Set static IP via Netplan (optional):

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

#### On the control plane node (`node1`):

```bash
curl -sfL https://get.k3s.io | sh -
```

Get your node token:

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

#### On worker node(s):

```bash
curl -sfL https://get.k3s.io | K3S_URL=https://<CONTROL_PLANE_IP>:6443 K3S_TOKEN=<TOKEN> sh -
```

---

### 📦 Step 3: Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```
---
### Step 4: 🛠️ Manual Setup Commands (One-Time Setup)

#### 🔑 1. Cloudflare Tunnel Setup (Cloudflared)

First, authenticate and create the tunnel. This saves a credentials JSON you’ll mount as a secret.

```bash
cloudflared tunnel login
cloudflared tunnel create homelab-tunnel
cloudflared tunnel route dns homelab-tunnel <your-subdomain.yourdomain.com>
```

Save the `~/.cloudflared/<tunnel>.json` and create a Kubernetes secret:

```bash
kubectl create secret generic cloudflared-credentials \
  --from-file=credentials.json=~/.cloudflared/<tunnel>.json \
  -n cloudflared
```

Optionally, create a ConfigMap for the ingress rules:

```bash
kubectl create configmap cloudflared-ingress \
  --from-file=config.yaml=./cloudflared-config.yaml \
  -n cloudflared
```

---

#### 🔐 2. Longhorn UI Auth

Longhorn doesn't support built-in auth, so we inject it using a middleware with basic-auth.

Generate an htpasswd hash:

```bash
htpasswd -c ./auth longhornadmin
```

Then create a Kubernetes secret:

```bash
kubectl create secret generic basic-auth \
  -n longhorn-system \
  --from-literal=users='<output_from_htpasswd>'
```

---

#### 🧾 3. Nextcloud Secrets

Create Kubernetes secrets for Nextcloud admin and MariaDB access:

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

### Step 5: Apply the chart
---
Install it:

```bash
helm dependency update ./homelab
helm install homelab ./homelab -n homelab --create-namespace -f ./homelab/values.yaml
```

## 🧱 Core Components Explained

---

### 🚀 **k3s** – Lightweight Kubernetes

- Runs a minimal Kubernetes distribution across `node1` (control plane) and `node2` (worker).
- Uses `containerd` instead of Docker.
- No external etcd needed, simplifying setup.

> 🧩 All apps like Nextcloud, Pi-hole, and Longhorn run as native Kubernetes workloads here.

---

## 🧱 Component Breakdown

### 1. 🧬 ArgoCD – GitOps Engine

- Manages all app deployments declaratively via Git.
- Syncs your chart and values into the cluster.
- Automatically reconciles state on change.

ArgoCD is deployed via your umbrella chart and exposed via Traefik and Cloudflared.

---

### 2. 🌐 MetalLB – Bare Metal LoadBalancer

- Assigns LAN IPs to services of type `LoadBalancer`.
- Enables direct local access to services like Pi-hole or Traefik.

Configuration is managed in your chart as a CRD manifest + Helm `values.yaml`.

---

### 3. 🚪 Traefik – Ingress & TLS

- Manages HTTP routing and automatic TLS with Let's Encrypt.
- Fully Kubernetes-native: Ingress, Middleware, Certificates.

Routes traffic to Nextcloud, ArgoCD, and other services based on hostname.

---

### 4. ☁️ Cloudflared – Secure Tunnel to Internet

- Exposes internal services to the internet **without opening ports**.
- Connects to Cloudflare Tunnel + DNS.

All tunnels are configured as Kubernetes resources using your credentials + Helm values.

Example:
```yaml
cloudflared:
  tunnelName: homelab-tunnel
  credentialsSecret: cloudflared-credentials
  ingress:
    - hostname: nextcloud.mydomain.com
      service: http://nextcloud.nextcloud.svc.cluster.local:80
```

---

### 5. 🧠 Pi-hole – DNS-level Ad Blocking

- Deployed inside Kubernetes with persistent Longhorn storage.
- Exposed via MetalLB IP on LAN and optionally via tunnel.

Authentication credentials and config are handled via Kubernetes Secrets and Helm values.

---

### 6. 📁 Nextcloud – Private Cloud Platform

- Handles file sync, notes, calendar, and contacts.
- Deployed via Helm with separate MariaDB subchart.
- Uses Longhorn PVC for storage.

All credentials are configured via Helm secrets:

```yaml
nextcloud:
  adminUser: admin
  adminPassword: secret
  database:
    rootPassword: rootpass
    password: dbpass
```

---

### 7. 💾 Longhorn – Persistent Storage Engine

- Provides resilient block storage for stateful apps.
- Replicates volumes across nodes.
- Installed via chart and secured with basic-auth middleware.

Chart sets up the middleware, ingress, and secrets for Longhorn UI access.

#### 🧪 Get the initial admin password

```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

---
### 🧠 8. ArgoCD – GitOps Continuous Delivery
- ArgoCD manages application deployments declaratively via Git.

- Ensures your Kubernetes state matches the code in your repo.

- Enables version-controlled, repeatable deployments of services like Traefik, Pi-hole, and Nextcloud.

- 🔁 Any change you commit to your Git repository (manifests, Helm values, etc.) is automatically applied to your cluster by ArgoCD.

#### 🧬 Connect ArgoCD to your Git repo

Example App:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nextcloud
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/homelab-k8s
    targetRevision: HEAD
    path: nextcloud
  destination:
    server: https://kubernetes.default.svc
    namespace: nextcloud
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## 🛠 Tooling & Workflow

| Tool      | Role |
|-----------|------|
| **Helm**  | Package & deploy the umbrella chart |
| **ArgoCD**| Sync cluster state from Git |
| **Cloudflare** | DNS + tunnel orchestration |
| **Longhorn** | Persistent volume management |
| **Git**   | Source of truth for all infrastructure |

---

## 🔐 Secrets Management

Secrets are templated using Helm values and stored securely via Kubernetes secrets:

- `nextcloud-admin-creds`
- `pihole-creds`
- `cloudflared-credentials`
- `longhorn-basic-auth`

---