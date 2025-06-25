# ML-Ops-transulator
This project works on whisper app (a pre-trained model which can transcribe any language)
setup is simple frontend webpage connected to backend flask application runs on k8s
code is in docker file

# About whisper 
This application has more than size of 10GB for small model ~1.5GB RAM
I ran this application on minikube.


# run these to deploy the k8s application

## Create Namespaces (if they don't exist)
kubectl create namespace whisper-namespace
kubectl create namespace monitoring

## Apply Monitoring Resources (in 'monitoring' namespace)
kubectl apply -f full-monitoring/base-monitoring.yaml -n monitoring
kubectl apply -f full-monitoring/prometheus.yaml -n monitoring
kubectl apply -f full-monitoring/prometheus-rules.yaml -n monitoring
kubectl apply -f full-monitoring/kube-metrics.yaml -n monitoring
kubectl apply -f full-monitoring/node-exporter.yaml -n monitoring
kubectl apply -f full-monitoring/grafana.yaml -n monitoring

## Apply Application Resources (in 'whisper-namespace')
kubectl apply -f k8s/volumes/model-pvc.yaml -n whisper-namespace
kubectl apply -f k8s/deployments/backend-deployment.yaml -n whisper-namespace
kubectl apply -f k8s/service/backend-service.yaml -n whisper-namespace
kubectl apply -f k8s/deployments/frontend-deployment.yaml -n whisper-namespace
kubectl apply -f k8s/service/frontend-service.yaml -n whisper-namespace
kubectl apply -f k8s/network-policy/base-policy.yaml -n whisper-namespace
kubectl apply -f k8s/network-policy/backend-policy.yaml -n whisper-namespace
kubectl apply -f k8s/network-policy/frontend-policy.yaml -n whisper-namespace

or  just by running

## helm (for complete deployment of k8s application)
"helm install helm-release ."     ----   inside path intern\helm>


# Monitoring  tools
Both Prometheus and Grafana tools has been used  in seperate namespace monitoring.

# Missing work
Planned to work on jenkins for automation but application load is too much for laptop when tred to run large models.
instead i just gave local scrypt to rollback functions , building and pushing images to dockerhub.
