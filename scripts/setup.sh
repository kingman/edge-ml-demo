#!/usr/bin/env sh

if [ -z "${GOOGLE_CLOUD_PROJECT}" ]; then
    echo 'The GOOGLE_CLOUD_PROJECT environment variable that points to the default Google Cloud project is not defined. Terminating...'
    return
fi

if ! command -v kubectl >/dev/null 2>&1; then
    echo "## Install k3s"
    curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mledge-agent
EOF
    kubectl create clusterrolebinding mledge-agent-cluster-admin \
    --clusterrole=cluster-admin \
    --serviceaccount=default:mledge-agent
fi

AGENT_KEY_ADDED=$(kubectl get secret mledge-agent-reader)
if [[ ! ${AGENT_KEY_ADDED} ]]; then
    echo "## Add agent reader key"
    if [ -z "${AGENT_KEY_PATH}" ]; then
        echo 'The AGENT_KEY_PATH environment variable is not defined. The variable points to agent reader key file. Terminating...'
        return
    fi
    kubectl create secret docker-registry mledge-agent-reader \
    --docker-server=https://gcr.io \
    --docker-username=_json_key \
    --docker-email=optional@example.com \
    --docker-password="$(cat ${AGENT_KEY_PATH})"
fi

GCR_KEY_ADDED=$(kubectl get secret mledge-gcr-reader)
if [[ ! ${GCR_KEY_ADDED} ]]; then
    echo "## Add gcr reader key"
    if [ -z "${GCR_KEY_PATH}" ]; then
        echo 'The GCR_KEY_PATH environment variable is not defined. The variable points to gcr reader key file. Terminating...'
        return
    fi
    kubectl create secret docker-registry mledge-gcr-reader \
    --docker-server=https://gcr.io \
    --docker-username=_json_key \
    --docker-email=optional@example.com \
    --docker-password="$(cat ${GCR_KEY_PATH})"
fi

DEVICE_PRIVATE_KEY_ADDED=$(kubectl get secret device-secrets)
if [[ ! ${DEVICE_PRIVATE_KEY_ADDED} ]]; then
    echo "## Add IoT device private key"
    if [ -z "${DEVICE_PRIVATE_KEY_PATH}" ]; then
        echo 'The DEVICE_PRIVATE_KEY_PATH environment variable is not defined. The variable points to device private key file. Terminating...'
        return
    fi
    kubectl create secret generic device-secrets \
    --from-file=device_private.pem=${DEVICE_PRIVATE_KEY_PATH}
fi

GOOGLE_ROOT_PEM_ADDED=$(kubectl get secret root-pem)
if [[ ! ${GOOGLE_ROOT_PEM_ADDED} ]]; then
    echo "## Add Google root pem"
    GCP_ROOT_CERT_FILE="roots.pem"
    if [ ! -f "${GCP_ROOT_CERT_FILE}" ]; then
        echo "## Download Google Cloud root cert"
        wget https://pki.goog/roots.pem
    fi
    kubectl create secret generic root-pem \
    --from-file=${GCP_ROOT_CERT_FILE}=./${GCP_ROOT_CERT_FILE}
fi

GCS_KEY_ADDED=$(kubectl get secret gcs-key)
if [[ ! ${GCS_KEY_ADDED} ]]; then
    echo "## Add Cloud Storage key"
    if [ -z "${GCS_KEY_PATH}" ]; then
        echo 'The GCS_KEY_PATH environment variable is not defined. The variable points to Cloud Storage key file. Terminating...'
        return
    fi
    kubectl create secret generic gcs-key \
    --from-file=key.json=${GCS_KEY_PATH}
fi

CLOUD_IOT_DEVICE_CONFIG=cloud_config.ini
if [ ! -f "${CLOUD_IOT_DEVICE_CONFIG}" ]; then
    echo "## Creating device config file"
    if [ -z "${CLOUD_IOT_REGION}" ]; then
        echo 'The CLOUD_IOT_REGION environment variable that points to the Cloud IoT region to use. Terminating...'
        return
    fi

    if [ -z "${CLOUD_IOT_REGISTRY}" ]; then
        echo 'The CLOUD_IOT_REGISTRY environment variable that points to the Cloud IoT registry for the device. Terminating...'
        return
    fi

    if [ -z "${CLOUD_IOT_DEVICE}" ]; then
        echo 'The CLOUD_IOT_DEVICE environment variable that points to the Cloud IoT device id for the device. Terminating...'
        return
    fi
    envsubst < device_config_template.ini > ${CLOUD_IOT_DEVICE_CONFIG}    
fi

DEVICE_CONFIG_ADDED=$(kubectl get configmap device-config)
if [[ ! ${DEVICE_CONFIG_ADDED} ]]; then
    echo "## Add device configmap to k8s cluster"
    kubectl create configmap device-config --from-file=${CLOUD_IOT_DEVICE_CONFIG}
fi