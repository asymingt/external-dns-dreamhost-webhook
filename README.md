# Description

This is a simple webhook for external-dns that transforms dyanmic DNS operations made by external-dns to HTTP GET and POST operations to the Dreamhost API. Before you use it, you will need to visit the [Dreamhost API](https://panel.dreamhost.com/index.cgi?tree=home.api) to generate an API key. You will then add this API key as a secret in kubernetes by running the following command with `DREAMHOST_ACCESS_KEY` replaced by your access key:

```
kubectl create secret generic dreamhost-credentials --from-literal=api-access-key='DREAMHOST_ACCESS_KEY' -n external-dns
```

Once this is done you can write a configuration file that sets up external-dns to use the new webook with this secret API key.

```yaml
namespace: external-dns
policy: sync
provider:
  name: webhook
  webhook:
    image:
      repository: ghcr.io/asymingt/external-dns-dreamhost-webhook
      tag: v0.0.1
    env:
      - name: ACCESS_KEY
        valueFrom:
          secretKeyRef:
            name: dreamhost-credentials
            key: api-access-key
    livenessProbe:
      httpGet:
        path: /health
        port: http-wh-metrics
      initialDelaySeconds: 10
      timeoutSeconds: 5
    readinessProbe:
      httpGet:
        path: /ready
        port: http-wh-metrics
      initialDelaySeconds: 10
      timeoutSeconds: 5
extraArgs:
  - "--txt-prefix=reg-%{record_type}-"
```

Then install external-dns and configure it to use this webhook:

```
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update
helm install external-dns-dreamhost external-dns/external-dns -f external-dns-dreamhost-values.yaml -n external-dns
```