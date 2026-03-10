# Create or replace a kind cluster
kind delete cluster --name kind
kind create cluster --image kindest/node:v1.29.4 --config k8s/clusters/kind-cluster.yaml

# Add airflow to my Helm repo
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm show values apache-airflow/airflow > chart/values-example.yaml

# Export values for Airflow docker image
export REGION=ap-northeast-2
export ECR_REGISTRY=636916184249.dkr.ecr.ap-northeast-2.amazonaws.com
export ECR_REPOSITORY=my-dags-repo
export NAMESPACE=airflow
export RELEASE_NAME=airflow
export GIT_SECRET_FILE=k8s/secrets/git-secrets.yaml
export ECR_PULL_SECRET=ecr-registry-secret

# Authenticate with ECR
aws ecr get-login-password --region $REGION \
    | docker login --username AWS --password-stdin $ECR_REGISTRY

# Get the latest image tag from ECR
export IMAGE_TAG=$(aws ecr describe-images \
    --repository-name $ECR_REPOSITORY \
    --region $REGION \
    --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' \
    --output text)

if [ -z "$IMAGE_TAG" ] || [ "$IMAGE_TAG" = "None" ]; then
    echo "No image tag found in ECR repository: $ECR_REPOSITORY"
    exit 1
fi

# Create a namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply kubernetes secrets only when private repo credentials are needed
if [ -f "$GIT_SECRET_FILE" ]; then
    kubectl apply -f "$GIT_SECRET_FILE"
fi

# Create imagePullSecret for private ECR access
kubectl create secret docker-registry $ECR_PULL_SECRET \
    --namespace $NAMESPACE \
    --docker-server=$ECR_REGISTRY \
    --docker-username=AWS \
    --docker-password="$(aws ecr get-login-password --region $REGION)" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f k8s/volumes/airflow-logs-pv.yaml
kubectl apply -f k8s/volumes/airflow-logs-pvc.yaml

# Install Airflow using Helm
helm install $RELEASE_NAME apache-airflow/airflow \
    --namespace $NAMESPACE -f chart/values-override-persistence.yaml \
    --set-string images.airflow.repository=$ECR_REGISTRY/$ECR_REPOSITORY \
    --set-string images.airflow.tag="$IMAGE_TAG" \
    --set imagePullSecrets[0].name="$ECR_PULL_SECRET" \
    --debug

# Port forward the API server
kubectl port-forward svc/$RELEASE_NAME-api-server 8080:8080 --namespace $NAMESPACE
