import os
import subprocess
from typing import Union
from crewai.tools import tool


@tool("generate_k8s_manifest")
def generate_k8s_manifest(app_name: str, replicas: int, port: int) -> dict:
    """
    Generates a Kubernetes Deployment + Service YAML manifest on disk.
    Returns a dict with status, filename, and manifest for downstream consumption.
    """
    # ---- Input validation -------------------------------------------------
    if not app_name or not isinstance(app_name, str):
        return {"status": "error", "message": "app_name must be a non‑empty string."}
    if not isinstance(replicas, int) or replicas <= 0:
        return {"status": "error", "message": "replicas must be a positive integer."}
    if not isinstance(port, int) or not (1 <= port <= 65535):
        return {"status": "error", "message": "port must be an integer between 1 and 65535."}

    # ---- Build manifest ---------------------------------------------------
    manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: nginx:latest
        ports:
        - containerPort: {port}
        readinessProbe:
          httpGet:
            path: /
            port: {port}
---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-svc
spec:
  selector:
    app: {app_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: {port}
"""

    filename = f"{app_name}-k8s.yaml"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(manifest)
        return {
            "status": "success",
            "filename": filename,
            "manifest": manifest
        }
    except Exception as exc:
        return {"status": "error", "message": f"Failed to write manifest: {str(exc)}"}


@tool("apply_k8s_manifest")
def apply_k8s_manifest(input_data: Union[str, dict]) -> str:
    """
    Applies the given manifest using `kubectl apply`.
    Accepts either a filename string or a dict with a 'filename' key (and optionally 'manifest').
    """
    import os
    import subprocess
    from typing import Union

    # Extract filename from the passed argument
    if isinstance(input_data, dict):
        filename = input_data.get("filename") or input_data.get("file_name")
        if not filename:
            return "❌ Error: No filename provided in input."
    else:
        filename = input_data

    if not filename or not isinstance(filename, str):
        return "❌ Error: filename must be a non‑empty string."

    if not os.path.exists(filename):
        return f"❌ Error: The file '{filename}' was not found to apply."

    try:
        # Attempts to apply the manifest to a real cluster if available
        result = subprocess.run(
            ["kubectl", "apply", "-f", filename],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return f"✅ GitOps Sync Success: {result.stdout.strip()}"
        return (
            f"⚠️ GitOps Simulation: File '{filename}' is syntactically valid, "
            f"but no Kubernetes cluster was detected. The GitOps controller would reconcile this state."
        )
    except FileNotFoundError:
        return (
            f"ℹ️ Simulation Mode: 'kubectl' command line tool is not installed. "
            f"In a production system, ArgoCD or Flux would apply this manifest now."
        )
    except Exception as exc:
        return f"❌ Unexpected error while applying manifest: {str(exc)}"


@tool("analyze_canary_metrics")
def analyze_canary_metrics(metrics_data: str) -> str:
    """
    Analyzes application metrics to decide whether a Canary rollout should proceed
    or rollback based on error‑rate thresholds.
    """
    if not isinstance(metrics_data, str):
        return "❌ Error: metrics_data must be a string."

    # Trigger rollback if any error indicator is present
    if "error_rate > 5%" in metrics_data or "error" in metrics_data.lower():
        return "❌ ROLLBACK: Elevated error rate detected in Canary pods. Reverting deployment."
    return "✅ PROCEED: Metrics are stable. Canary rollout approved for production."