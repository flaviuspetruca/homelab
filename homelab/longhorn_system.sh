#!/bin/bash
set -euo pipefail

NAMESPACE="longhorn-system"

echo "Listing all namespaced resources in namespace '$NAMESPACE'..."

RESOURCE_TYPES=$(kubectl api-resources --verbs=list --namespaced -o name)

echo "Fetching all resources in $NAMESPACE..."

for resource in $RESOURCE_TYPES; do
  items=$(kubectl -n "$NAMESPACE" get "$resource" --ignore-not-found -o json 2>/dev/null || true)
  count=$(echo "$items" | jq '.items | length')
  if [[ "$count" -gt 0 ]]; then
    echo "Processing resource type: $resource ($count items)"
    echo "$items" | jq -c '.items[] | {name: .metadata.name, finalizers: .metadata.finalizers}' | while read -r item; do
      name=$(echo "$item" | jq -r '.name')
      finalizers=$(echo "$item" | jq '.finalizers')
      if [[ "$finalizers" != "null" ]] && [[ "$finalizers" != "[]" ]]; then
        echo "  Removing finalizers from $resource/$name ..."
        kubectl patch "$resource" "$name" -n "$NAMESPACE" -p '{"metadata":{"finalizers":[]}}' --type=merge
      fi
    done
  fi
done

echo "Removing finalizers from namespace $NAMESPACE itself..."

# Get namespace JSON
kubectl get namespace "$NAMESPACE" -o json > /tmp/ns.json

# Remove finalizers from namespace JSON
jq 'del(.spec.finalizers)' /tmp/ns.json > /tmp/ns-patched.json

# Patch the namespace to remove finalizers and allow deletion
kubectl replace --raw "/api/v1/namespaces/$NAMESPACE/finalize" -f /tmp/ns-patched.json

echo "Namespace '$NAMESPACE' finalizers removed and deletion should proceed."

echo "Done. Please check with: kubectl get namespace $NAMESPACE"
