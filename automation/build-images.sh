#!/bin/bash
set -e
source ./automation/.env

# Remove carriage returns from variables, which can happen with Windows line endings
DOCKER_USERNAME="${DOCKER_USERNAME//$'\r'/}"
IMAGE_VERSION="${IMAGE_VERSION//$'\r'/}"

NEW_VERSION=$((IMAGE_VERSION + 1))
sed -i "s/^IMAGE_VERSION=.*/IMAGE_VERSION=$NEW_VERSION/" ./automation/.env

IMAGE_TAG="v${NEW_VERSION}"
echo "Building and pushing Docker images with tag: ${IMAGE_TAG}"

# Ask user what to build/push
echo "What do you want to build/push?"
echo "1) Backend only"
echo "2) Frontend only"
echo "Any other key) Both Backend and Frontend"
read -p "Enter your choice: " CHOICE

case "$CHOICE" in
    1)
        echo "Proceeding with Backend only..."
        BACKEND_IMAGE_NAME="${DOCKER_USERNAME}/whisper:${IMAGE_TAG}"
        echo "--> Building ${BACKEND_IMAGE_NAME}"
        docker build -t "${BACKEND_IMAGE_NAME}" docker/backend/
        echo "--> Pushing ${BACKEND_IMAGE_NAME}"
        docker push "${BACKEND_IMAGE_NAME}"
        ;;
    2)
        echo "Proceeding with Frontend only..."
        FRONTEND_IMAGE_NAME="${DOCKER_USERNAME}/website:${IMAGE_TAG}"
        echo "--> Building ${FRONTEND_IMAGE_NAME}"
        docker build -t "${FRONTEND_IMAGE_NAME}" docker/frontend/
        echo "--> Pushing ${FRONTEND_IMAGE_NAME}"
        docker push "${FRONTEND_IMAGE_NAME}"
        ;;
    *)
        echo "Proceeding with both Backend and Frontend..."
        BACKEND_IMAGE_NAME="${DOCKER_USERNAME}/whisper:${IMAGE_TAG}"
        echo "--> Building ${BACKEND_IMAGE_NAME}"
        docker build -t "${BACKEND_IMAGE_NAME}" ../docker/backend/
        echo "--> Pushing ${BACKEND_IMAGE_NAME}"
        docker push "${BACKEND_IMAGE_NAME}"
        echo ""
        FRONTEND_IMAGE_NAME="${DOCKER_USERNAME}/website:${IMAGE_TAG}"
        echo "--> Building ${FRONTEND_IMAGE_NAME}"
        docker build -t "${FRONTEND_IMAGE_NAME}" ../docker/frontend/
        echo "--> Pushing ${FRONTEND_IMAGE_NAME}"
        docker push "${FRONTEND_IMAGE_NAME}"
        ;;
esac

echo "Images built and pushed successfully. Updated .env to IMAGE_VERSION=${NEW_VERSION}"