# 🏠 Homelab Kubernetes Cluster with k3s, Traefik, MetalLB, Longhorn, Pi-hole, Nextcloud & Cloudflared

This project is my personal homelab running a fully self-hosted application stack on Kubernetes using [k3s](https://k3s.io). It’s designed to be lightweight, resilient, and remotely accessible—without compromising on security.

---

## 🧠 Why I Built This

I wanted a real-world platform to:

- Host and manage services like Nextcloud and Pi-hole
- Learn and experiment with Kubernetes in a homelab context
- Access services remotely without opening ports or exposing my IP
- Explore self-hosting, DNS, storage, and ingress in a production-like environment

This stack is cloud-native and forward-thinking—everything is containerized, declaratively deployed, and controlled with modern DevOps principles.

---

## ⚙️ Core Components and How They Work Together

### 🚀 1. **k3s** – Lightweight Kubernetes

- Installs and runs a Kubernetes cluster across 2 nodes.
- Chosen for its small footprint, ease of install, and built-in features (like containerd, Traefik by default—though I replace it).
- Nodes:
  - `node1`: Control plane + worker
  - `node2`: Worker

> 🧩 All services (Nextcloud, Pi-hole, etc.) are deployed as Kubernetes workloads inside this cluster.

---

### 🌐 2. **MetalLB** – LoadBalancer for Bare Metal

- Kubernetes services like Traefik or Pi-hole need a `LoadBalancer` type service to get an external IP.
- MetalLB assigns IPs from a pool (e.g. `192.168.1.240-250`) on the local LAN.
- This simulates a cloud-style load balancer in a home environment.

> 🧭 Any service that needs to be reachable internally (or via Cloudflared) uses MetalLB to expose a stable IP.

---

### 🚪 3. **Traefik** – Ingress Controller

- Handles routing HTTP(S) traffic to internal services.
- Automatically provisions TLS certificates via Let's Encrypt (internally).
- Integrates with Kubernetes via Ingress and Middleware resources.

> 🛣️ All HTTP requests hit Traefik first. It forwards traffic to the right service (e.g., Nextcloud, Pi-hole) based on hostname or path rules.

---

### ☁️ 4. **Cloudflared** – Secure Tunnels to the Internet

- Cloudflared creates encrypted tunnels between my homelab and Cloudflare.
- This allows me to access services (like Nextcloud) over the internet **without exposing ports or my IP address**.
- DNS is managed by Cloudflare; tunnels route traffic securely to internal Kubernetes services.

#### Why Cloudflared?

- NAT traversal without router config
- No open ports = smaller attack surface
- Zero-trust access (can add auth via Cloudflare Access)
- Works great with dynamic IPs

> 🌍 When I go to `nextcloud.mydomain.com`, Cloudflare routes the request over the tunnel directly into my Traefik ingress. No need for a reverse proxy or dynamic DNS hacks.

---

### 🧠 5. **Pi-hole** – Network-wide DNS Ad Blocker

- Deployed as a Kubernetes workload with persistent storage.
- Optionally exposed internally (`pihole.local`) and via a Cloudflared subdomain.
- Provides DNS resolution for all devices on my LAN.

> 🛡️ Traefik does not handle Pi-hole traffic. Instead, it's either accessed directly (via MetalLB IP) or tunneled via Cloudflared if I'm remote.

---

### 💾 6. **Longhorn** – Persistent Distributed Storage

- Provides a cloud-like block storage system inside Kubernetes.
- Enables stateful apps (like Nextcloud and Pi-hole) to persist data even if pods move between nodes.
- Replicates volumes across nodes for resilience.

> 🗃️ All app data is stored on Longhorn volumes, ensuring data survives restarts, reboots, and pod rescheduling.

---

### 📁 7. **Nextcloud** – Your Private Cloud

- Deployed inside Kubernetes with access via `https://nextcloud.mydomain.com`.
- Stores files on a Longhorn PVC.
- Ingressed through Traefik, exposed via Cloudflared for remote access.

> 🧑‍💻 I use this daily for file syncing, calendar, notes, and mobile access—all without relying on Google or Dropbox.

---

## 🛠️ Dev & Ops Tooling

- [Helm](https://helm.sh): Managing complex apps like Nextcloud or Traefik
- [Cloudflare](https://cloudflare.com): DNS and tunnel orchestration



