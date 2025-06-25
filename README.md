# ML-Ops-transulator
This project showcases an end-to-end MLOps pipeline for a Whisper AI transcription application, designed for easy deployment and monitoring on a Kubernetes cluster. The core application comprises a simple web-based frontend connected to a Flask backend, which leverages a pre-trained Whisper model to perform multi-language speech-to-text transcription. All components are containerized using Docker and orchestrated with Kubernetes, specifically tested on Minikube for local development.

# 🌟 Project Overview
The primary goal of this project is to demonstrate the deployment and operational aspects of a machine learning application. It includes:

A Whisper AI Backend: A Flask application that handles audio transcription requests using the Whisper model.

A Web Frontend: A simple webpage allowing users to interact with the transcription service.

Containerization: Dockerfiles define the build process for both the frontend and backend images.

Kubernetes Orchestration: All application and monitoring components are deployed and managed within a Kubernetes cluster.

Comprehensive Monitoring: Integration with Prometheus for metrics collection and Grafana for visualization and alerting.

# 🧠 About the Whisper Application
The Whisper model, being a powerful pre-trained speech-to-text model, has significant resource requirements.

Model Size: Even a "small" Whisper model can require substantial resources. For context, the base model used in this setup has a size of approximately 1.5GB RAM when loaded. Larger models can easily exceed 10GB RAM.

Local Development Considerations: Due to these resource demands, this application has been rigorously tested and is primarily intended for deployment on minikube for local development and testing, or a cloud-based Kubernetes cluster with sufficient compute and memory.

# 🚀 Deployment
This project offers two primary methods for deploying the Kubernetes application: via native Kubernetes YAML manifests or using Helm Charts for simplified management.

## Prerequisites
Before deploying, ensure you have the following tools installed and configured:

### Minikube: For running a local Kubernetes cluster.

Start your Minikube cluster: minikube start

Ensure minikube is running and kubectl context is set: minikube status

Docker: For building and pushing container images.

Kubectl: The Kubernetes command-line tool.

Helm: The Kubernetes package manager (for Helm chart deployment).

## Option 1: Deploying with Kubernetes YAML Manifests (Native Kubectl)
This method provides granular control over each Kubernetes resource. Ensure you are in the root directory of your project (e.g., C:\Users\visha\Desktop\intern) when running these commands.

1. Create Namespaces (if they don't exist)
It's crucial to create the dedicated namespaces for your application and monitoring components before deploying resources into them.

kubectl create namespace whisper-namespace --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

2. Apply Monitoring Resources (in monitoring namespace)
These commands deploy Prometheus, Grafana, and related components responsible for collecting and visualizing metrics from your Kubernetes cluster and applications.

kubectl apply -f full-monitoring/base-monitoring.yaml -n monitoring

kubectl apply -f full-monitoring/prometheus.yaml -n monitoring

kubectl apply -f full-monitoring/prometheus-rules.yaml -n monitoring

kubectl apply -f full-monitoring/kube-metrics.yaml -n monitoring

kubectl apply -f full-monitoring/node-exporter.yaml -n monitoring

kubectl apply -f full-monitoring/grafana.yaml -n monitoring

3. Apply Application Resources (in whisper-namespace)
These commands deploy your Whisper backend, frontend, persistent volume claims, and network policies within the application namespace.

kubectl apply -f k8s/volumes/model-pvc.yaml -n whisper-namespace

kubectl apply -f k8s/deployments/backend-deployment.yaml -n whisper-namespace

kubectl apply -f k8s/service/backend-service.yaml -n whisper-namespace

kubectl apply -f k8s/deployments/frontend-deployment.yaml -n whisper-namespace

kubectl apply -f k8s/service/frontend-service.yaml -n whisper-namespace

kubectl apply -f k8s/network-policy/base-policy.yaml -n whisper-namespace

kubectl apply -f k8s/network-policy/backend-policy.yaml -n whisper-namespace

kubectl apply -f k8s/network-policy/frontend-policy.yaml -n whisper-namespace

#  Option 2: Deploying with Helm Charts (Recommended)
For a complete and streamlined deployment of all Kubernetes components (application and monitoring), you can use the provided Helm chart. Helm simplifies the packaging, deployment, and management of Kubernetes applications.

Navigate to the Helm Chart directory:

cd helm

Install the Helm Chart:

helm install helm-release .

The . signifies that you are installing the chart from the current directory.
You can customize deployments by modifying values.yaml or by overriding values with --set flags during helm install.

📈 Monitoring Tools
This project integrates a robust monitoring stack for comprehensive observability:

Prometheus: Deployed in the monitoring namespace, Prometheus is configured to scrape metrics from the Kubernetes cluster itself (nodes, pods, services) and directly from the application pods (backend and frontend).

Grafana: Also deployed in the monitoring namespace, Grafana provides rich dashboards for visualizing the metrics collected by Prometheus. It's pre-configured to connect to the Prometheus instance. Remember to change the default adminPassword in helm/values.yaml for production environments!

After deployment (especially with Helm), you can typically access Grafana and your frontend application via minikube service commands:

# To see output of application see
##  application at 
minikube service (service name of front) -n whisper-namespace
After getting url   example     http://localhost:6536       add / app at last   so   http://localhost:6536/app

## Grafana dashboard
minikube service helm-release-grafana-service -n monitoring      #  service name may vary if it helm or manual deployment

## Prometheus UI
kubectl port-forward <prometheus-pod-name> 9090:9090 -n monitoring


# 🚧 Missing Work & Future Considerations
Initially, there was a plan to integrate a full CI/CD pipeline using Jenkins for automated deployments. However, due to the substantial resource requirements of the Whisper model (especially for larger models) and the limitations of running such workloads on a development laptop, this was deferred.

Instead, the project currently provides a local automation script (automation/build-images.sh) that supports:

Building and pushing Docker images to Docker Hub.

Performing rollbacks for application deployments.

Future enhancements could include:

Implementing a robust CI/CD pipeline on a cloud-based Kubernetes service (e.g., GKE, EKS, AKS) to handle the resource-intensive ML model builds and deployments.

Exploring optimized inference solutions (e.g., ONNX Runtime, TensorRT) or model serving frameworks (e.g., KServe, Seldon Core) for better performance and resource utilization.

Adding more sophisticated autoscaling rules based on application-specific metrics.

Implementing more advanced alerting and notification mechanisms.
