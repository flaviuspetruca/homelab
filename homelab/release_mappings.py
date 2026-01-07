HELMFILE_RELEASES = {
    "argocd": {
        "name": "argocd",
        "namespace": "argocd",
        "chart": "argo/argo-cd",
        "values": ["./values/values-argocd.yaml"],
    },
    "longhorn": [
        {
            "name": "longhorn",
            "namespace": "longhorn-system",
            "chart": "longhorn/longhorn",
            "values": ["./values/values-longhorn.yaml"],
        },
        {
            "name": "longhorn-extras",
            "namespace": "longhorn-system",
            "chart": "./custom-charts/longhorn-extras",
            "needs": ["longhorn"],
            "values": ["./custom-charts/longhorn-extras/values.yaml"],
        },
    ],
    "pihole": {
        "name": "pihole",
        "namespace": "pihole",
        "chart": "mojo2600/pihole",
        "values": ["./values/values-pihole.yaml"],
    },
    "nextcloud": {
        "name": "nextcloud",
        "namespace": "nextcloud",
        "chart": "nextcloud/nextcloud",
        "values": ["./values/values-nextcloud.yaml"],
    },
    "cert-manager": [
        {
            "name": "cert-manager",
            "namespace": "cert-manager",
            "chart": "jetstack/cert-manager",
            "version": "v1.14.5",
            "values": ["./values/values-cert-manager.yaml"],
        },
        {
            "name": "cert-manager-extras",
            "namespace": "cert-manager",
            "chart": "./custom-charts/cert-manager-extras",
            "needs": ["cert-manager"],
            "values": ["./custom-charts/cert-manager-extras/values.yaml"],
        },
    ],
    "metallb": [
        {
            "name": "metallb",
            "namespace": "metallb-system",
            "chart": "metallb/metallb",
            "values": ["./values/values-metallb.yaml"],
        },
        {
            "name": "metallb-extras",
            "namespace": "metallb-system",
            "chart": "./custom-charts/metallb-extras",
            "needs": ["metallb"],
            "values": ["./custom-charts/metallb-extras/values.yaml"],
        },
    ],
    "cloudflared": {
        "name": "cloudflared-extras",
        "namespace": "cloudflared",
        "chart": "./custom-charts/cloudflared-extras",
    },
}

APP_REPOS = {
    "argocd": {"name": "argo", "url": "https://argoproj.github.io/argo-helm"},
    "longhorn": {"name": "longhorn", "url": "https://charts.longhorn.io"},
    "pihole": {
        "name": "mojo2600",
        "url": "https://mojo2600.github.io/pihole-kubernetes/",
    },
    "nextcloud": {"name": "nextcloud", "url": "https://nextcloud.github.io/helm/"},
    "cert-manager": {"name": "jetstack", "url": "https://charts.jetstack.io"},
    "metallb": {"name": "metallb", "url": "https://metallb.github.io/metallb"},
    # cloudflared only has a custom chart → no repo
}
