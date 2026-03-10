# Export values for Airflow docker image
export IMAGE_NAME=my-dags
export IMAGE_TAG=1
export NAMESPACE=airflow
export RELEASE_NAME=airflow

# Build image
docker build --pull --tag $IMAGE_NAME:$IMAGE_TAG -f cicd/Dockerfile .

# Load image into kind
kind load docker-image $IMAGE_NAME:$IMAGE_TAG

# Upgrade airflow
helm upgrade $RELEASE_NAME apache-airflow/airflow \
    --namespace $NAMESPACE -f chart/values-override.yaml \
    --set-string images.airflow.tag="$IMAGE_TAG"

# Restart pods so new image is used
kubectl delete pods -n $NAMESPACE --all

# Port forward
kubectl port-forward svc/$RELEASE_NAME-api-server 8080:8080 --namespace $NAMESPACE