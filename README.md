# Description

This is a simple webhook for external-dns that transforms dyanmic DNS operations made by external-dns to HTTP GET and POST operations to the Dreamhost API. Before you use it, you will need to visit the [Dreamhost API](https://panel.dreamhost.com/index.cgi?tree=home.api) to generate an API key. You will then add this API key as a secret in kubernetes by running the following command with `DREAMHOST_ACCESS_KEY` replaced by your access key:

```
kubectl create secret generic dreamhost-credentials --from-literal=api-access-key='DREAMHOST_ACCESS_KEY' -n external-dns
```

Once this is done you can create a configuration file called `external-dns-dreamhost-webhook.yaml` that sets up external-dns to use the new webook with this secret API key.

```yaml
namespace: external-dns
policy: sync
provider:
  name: webhook
  webhook:
    image:
      repository: docker.io/asymingt/external-dns-dreamhost-webhook
      tag: v0.0.2
    env:
      - name: DREAMHOST_ACCESS_KEY
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
helm install external-dns-dreamhost external-dns/external-dns -f external-dns-dreamhost-webhook.yaml -n external-dns
```

Finally, annotate a service to instruct external-dns to add record for it. For example your domain `nginx.example.org` will now route to this service:

```
kubectl annotate service nginx "external-dns.alpha.kubernetes.io/hostname=nginx.example.org."
```