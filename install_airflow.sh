# Create or replace a kind cluster
kind delete cluster --name kind
kind create cluster --image kindest/node:v1.29.4

# Add airflow to my Helm repo
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm show values apache-airflow/airflow > chart/values-example.yaml

# Export values for Airflow docker image
export IMAGE_NAME=my-dags
export IMAGE_TAG=1
export NAMESPACE=airflow
export RELEASE_NAME=airflow
export GIT_SECRET_FILE=k8s/secrets/git-secrets.yaml

# Build the image and load it into kind
docker build --pull --tag $IMAGE_NAME:$IMAGE_TAG -f cicd/Dockerfile .
kind load docker-image $IMAGE_NAME:$IMAGE_TAG

# Create a namespace
kubectl create namespace $NAMESPACE

# Apply kubernetes secrets
if [ ! -f "$GIT_SECRET_FILE" ]; then
    echo "Missing $GIT_SECRET_FILE"
    echo "Create it from k8s/secrets/git-secrets.example.yaml before installing."
    exit 1
fi

kubectl apply -f "$GIT_SECRET_FILE"

# Install Airflow using Helm
helm install $RELEASE_NAME apache-airflow/airflow \
    --namespace $NAMESPACE -f chart/values-override.yaml \
    --set-string images.airflow.tag="$IMAGE_TAG" \
    --debug

# Port forward the API server
kubectl port-forward svc/$RELEASE_NAME-api-server 8080:8080 --namespace $NAMESPACE
