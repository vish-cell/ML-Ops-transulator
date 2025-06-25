# ML-Ops-transulator

This project showcases an end-to-end MLOps pipeline for a Whisper AI transcription application, designed for easy deployment and monitoring on a Kubernetes cluster. The core application comprises a simple web-based frontend connected to a Flask backend, which leverages a pre-trained Whisper model to perform multi-language speech-to-text transcription. All components are containerized using Docker and orchestrated with Kubernetes, specifically tested on Minikube for local development.

## 🌟 Project Overview
---

The primary goal of this project is to demonstrate the deployment and operational aspects of a machine learning application. It includes:

* **A Whisper AI Backend:** A Flask application that handles audio transcription requests using the Whisper model.
* **A Web Frontend:** A simple webpage allowing users to interact with the transcription service.
* **Containerization:** `Dockerfiles` define the build process for both the frontend and backend images.
* **Kubernetes Orchestration:** All application and monitoring components are deployed and managed within a Kubernetes cluster.
* **Comprehensive Monitoring:** Integration with Prometheus for metrics collection and Grafana for visualization and alerting.

![bar plot](https://github.com/Irene-arch/Documenting_Example/assets/56026296/5ebedeb8-65e4-4f09-a2a5-0699119f5ff7)

## 🧠 About the Whisper Application

This application works on the *Whisper app*, a pre-trained model capable of transcribing any language. The Whisper model, being a powerful pre-trained speech-to-text model, has significant resource requirements.

* **Model Size:** Even a "small" Whisper model can require substantial resources. For context, the `base` model used in this setup has a size of approximately **1.5GB RAM** when loaded. Larger models can easily exceed **10GB RAM**.

* **Local Development Considerations:** Due to these resource demands, this application has been rigorously tested and is primarily intended for deployment on `minikube` for local development and testing, or a cloud-based Kubernetes cluster with sufficient compute and memory. This application was specifically run on `Minikube`.

## 🚀 Deployment

This project offers two primary methods for deploying the Kubernetes application: via native Kubernetes YAML manifests or using Helm Charts for simplified management.

### Prerequisites

Before deploying, ensure you have the following tools installed and configured:

* **Minikube:** For running a local Kubernetes cluster.
    * Start your Minikube cluster: `minikube start`
    * Ensure `minikube` is running and `kubectl` context is set: `minikube status`
* **Docker:** For building and pushing container images.
* **Kubectl:** The Kubernetes command-line tool.
* **Helm:** The Kubernetes package manager (for Helm chart deployment).

### Option 1: Deploying with Kubernetes YAML Manifests (Native Kubectl)

This method provides granular control over each Kubernetes resource. Ensure you are in the root directory of your project (e.g., `C:\Users\visha\Desktop\intern`) when running these commands.

#### 1. Create Namespaces (if they don't exist)

It's crucial to create the dedicated namespaces for your application and monitoring components before deploying resources into them.
