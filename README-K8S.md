# ☸️ AJAX AI - Kubernetes Deployment Guide

This directory contains the production-grade Kubernetes manifests to deploy **AJAX AI** along with its microservices:
- **`ajax-ai-app`**: FastAPI MVC Backend, Web Dashboard, and Autonomous AI Agent (Auto-scaled 2–10 Pods).
- **`postgres`**: Relational database storage (StatefulSet + PersistentVolume).
- **`meilisearch`**: Sub-millisecond text search engine & GraphRAG entry point (Deployment + PersistentVolume).
- **`ingress`**: NGINX Ingress routing external HTTP traffic.
- **`hpa`**: Horizontal Pod Autoscaler targeting CPU & Memory metrics.

---

## 📁 Kubernetes Manifest Structure

```text
k8s/
├── namespace.yaml       # 'ajax-ai' isolated namespace
├── configmap.yaml       # Environment configs (Ports, Models, Database hosts)
├── secrets.yaml         # Sensitive credentials (API Keys, DB passwords, JWT)
├── pvc.yaml             # PersistentVolumeClaims for Data, Logs, Postgres, Meilisearch
├── postgres.yaml        # PostgreSQL 16 StatefulSet & ClusterIP Service
├── meilisearch.yaml     # Meilisearch 1.7 Deployment & ClusterIP Service
├── ajax-app.yaml        # AJAX AI Deployment (2 replicas) & Service
├── hpa.yaml             # Horizontal Pod Autoscaler (2 to 10 replicas)
├── ingress.yaml         # Ingress Controller configuration
└── kustomization.yaml   # Unified Kustomize deployment bundle
```

---

## 🚀 Quick Start Deployment

### 1. Build the Docker Image
Ensure your Docker image is built locally or pushed to your registry (e.g., Docker Hub, ECR, GCR):

```bash
docker build -t ajax-ai:latest .
```

> **For Minikube:** Load the image directly into Minikube without pushing to an external registry:
> ```bash
> minikube image load ajax-ai:latest
> ```
> 
> **For Kind:**
> ```bash
> kind load docker-image ajax-ai:latest
> ```

---

### 2. Configure Secrets & Keys
Open [`k8s/secrets.yaml`](file:///c:/Users/Ajaysingh/PROJECT/Ai%20full%203.0/k8s/secrets.yaml) and add your actual API keys (e.g., `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.):

```yaml
stringData:
  OPENAI_API_KEY: "sk-your-openai-key"
  GROQ_API_KEY: "gsk_your_groq_key"
  POSTGRES_PASSWORD: "your_strong_password"
```

---

### 3. Deploy Everything with Kustomize

Deploy the entire stack in one command:

```bash
kubectl apply -k k8s/
```

Or step-by-step:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/meilisearch.yaml
kubectl apply -f k8s/ajax-app.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

---

### 4. Verify Pods & Services Status

Check the status of all pods in the `ajax-ai` namespace:

```bash
kubectl get pods -n ajax-ai -w
```

Expected output:
```text
NAME                           READY   STATUS    RESTARTS   AGE
ajax-ai-app-7d98c56d8f-abc12   1/1     Running   0          45s
ajax-ai-app-7d98c56d8f-xyz34   1/1     Running   0          45s
meilisearch-578df9cb8b-def56   1/1     Running   0          50s
postgres-0                     1/1     Running   0          55s
```

Check services and ingress:
```bash
kubectl get svc,pvc,hpa,ingress -n ajax-ai
```

---

### 5. Accessing the Application

#### Option A: Port-Forwarding (Local Testing / Quick Access)
```bash
kubectl port-forward svc/ajax-ai-service 8000:8000 -n ajax-ai
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

#### Option B: Via Ingress (Production / Domain)
Ensure NGINX Ingress Controller is installed:
```bash
# In Minikube:
minikube addons enable ingress
minikube tunnel
```
Now access the web interface directly via your cluster IP or configured hostname.

---

## 🛠️ Management & Debugging

### View Real-Time Logs
```bash
# Follow logs of the AI app
kubectl logs -l app=ajax-ai -n ajax-ai -f

# Follow PostgreSQL logs
kubectl logs postgres-0 -n ajax-ai -f

# Follow Meilisearch logs
kubectl logs -l app=meilisearch -n ajax-ai -f
```

### Execute a Shell Inside the AI Pod
```bash
kubectl exec -it deployment/ajax-ai-app -n ajax-ai -- /bin/bash
```

### Scale Replicas Manually
```bash
kubectl scale deployment ajax-ai-app --replicas=4 -n ajax-ai
```

### Teardown / Delete Stack
```bash
kubectl delete -k k8s/
```
