FROM ghcr.io/flant/shell-operator:v1.4.10

USER root
RUN apk add --no-cache python3 py3-pip py3-yaml ca-certificates && \
    pip install --no-cache-dir --break-system-packages \
        deckhouse-sdk==1.0.0 || \
    pip install --no-cache-dir --break-system-packages \
        pyyaml requests
USER shell-operator
