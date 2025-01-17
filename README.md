# ExternalDNS - Dreamhost Webhook
❤️ this project is a clone of [external-dns-vultr-webhook](https://github.com/vultr/external-dns-vultr-webhook) with adaptations for Dreamhost. It is in alpha and massively experimental, so please take care when you use it. It should not be used in production!

ExternalDNS is a Kubernetes add-on for automatically managing Domain Name System (DNS) records for Kubernetes services by using different DNS providers. By default, Kubernetes manages DNS records internally, but ExternalDNS takes this functionality a step further by delegating the management of DNS records to an external DNS provider such as this one. Therefore, the Dreamhost webhook allows to manage your Dreamhost domains inside your kubernetes cluster with [ExternalDNS](https://github.com/kubernetes-sigs/external-dns).

To use ExternalDNS with Dreamhost, you need your Dreamhost API token of the account managing your domains, which you can generate by visiting [this page](https://panel.dreamhost.com/?tree=home.api) on the Dreamhost website.

For detailed technical instructions on how the Dreamhost webhook is deployed using the Bitnami Helm charts for ExternalDNS, see[deployment instructions](#kubernetes-deployment).

## Kubernetes Deployment

The deployment can be performed in every way Kubernetes supports.
The following example shows the deployment as
a [sidecar container](https://kubernetes.io/docs/concepts/workloads/pods/#workload-resources-for-managing-pods) in the
ExternalDNS pod
using the [Bitnami Helm charts for ExternalDNS](https://github.com/bitnami/charts/tree/main/bitnami/external-dns).

⚠️ This webhook requires at least ExternalDNS v0.14.0.

The webhook can be installed using either the Bitnami chart or the ExternalDNS one.

First, create the Dreamhost secret:

```yaml
kubectl create secret generic dreamhost-credentials --from-literal=api-key='<EXAMPLE_PLEASE_REPLACE>' -n external-dns
```

### Using the Bitnami chart

Skip this if you already have the Bitnami repository added:

```shell
helm repo add bitnami https://charts.bitnami.com/bitnami
```

You can then create the helm values file, for example
`external-dns-dreamhost-values.yaml`:

```yaml
image:
  registry: registry.k8s.io
  repository: external-dns/external-dns
  tag: v0.14.0

provider: webhook

extraArgs:
  webhook-provider-url: http://localhost:8888
  txt-prefix: reg-

sidecars:
  - name: dreamhost-webhook
    image: ghcr.io/asymingt/external-dns-dreamhost-webhook:v0.1.1
    ports:
      - containerPort: 8888
        name: webhook
      - containerPort: 8080
        name: http
    livenessProbe:
      httpGet:
        path: /health
        port: http
      initialDelaySeconds: 10
      timeoutSeconds: 5
    readinessProbe:
      httpGet:
        path: /ready
        port: http
      initialDelaySeconds: 10
      timeoutSeconds: 5
    env:
      - name: DREAMHOST_API_KEY
        valueFrom:
          secretKeyRef:
            name: dreamhost-credentials
            key: api-key
```

And then:

```shell
# install external-dns with helm
helm install external-dns-dreamhost bitnami/external-dns -f external-dns-dreamhost-values.yaml -n external-dns
```

### Using the ExternalDNS chart

Skip this if you already have the ExternalDNS repository added:

```shell
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
```

You can then create the helm values file, for example
`external-dns-dreamhost-values.yaml`:

```yaml
namespace: external-dns
policy: sync
provider:
  name: webhook
  webhook:
    image:
      repository: ghcr.io/asymingt/external-dns-dreamhost-webhook
      tag: v0.1.1
    env:
      - name: DREAMHOST_API_KEY
        valueFrom:
          secretKeyRef:
            name: dreamhost-credentials
            key: api-key
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
```

And then:

```shell
# install external-dns with helm
helm install external-dns-dreamhost external-dns/external-dns -f external-dns-dreamhost-values.yaml --version 1.14.3 -n external-dns
```

## Environment variables

The following environment variables are available:

| Variable        | Description                      | Notes                      |
| --------------- | -------------------------------- | -------------------------- |
| DREAMHOST_API_KEY | Dreamhost API token                | Mandatory                  |
| DRY_RUN         | If set, changes won't be applied | Default: `false`           |
| WEBHOOK_HOST    | Webhook hostname or IP address   | Default: `localhost`       |
| WEBHOOK_PORT    | Webhook port                     | Default: `8888`            |
| HEALTH_HOST     | Liveness and readiness hostname  | Default: `0.0.0.0`         |
| HEALTH_PORT     | Liveness and readiness port      | Default: `8080`            |
| READ_TIMEOUT    | Servers' read timeout in ms      | Default: `60000`           |
| WRITE_TIMEOUT   | Servers' write timeout in ms     | Default: `60000`           |

Additional environment variables for domain filtering:

| Environment variable           | Description                        |
| ------------------------------ | ---------------------------------- |
| DOMAIN_FILTER                  | Filtered domains                   |
| EXCLUDE_DOMAIN_FILTER          | Excluded domains                   |
| REGEXP_DOMAIN_FILTER           | Regex for filtered domains         |
| REGEXP_DOMAIN_FILTER_EXCLUSION | Regex for excluded domains         |

If the `REGEXP_DOMAIN_FILTER` is set, the following variables will be used to
build the filter:

- REGEXP_DOMAIN_FILTER
- REGEXP_DOMAIN_FILTER_EXCLUSION

otherwise, the filter will be built using:

- DOMAIN_FILTER
- EXCLUDE_DOMAIN_FILTER

## Tweaking the configuration

While tweaking the configuration, there are some points to take into
consideration:

- if `WEBHOOK_HOST` and `HEALTH_HOST` are set to the same address/hostname or
  one of them is set to `0.0.0.0` remember to use different ports.
- if your records don't get deleted when applications are uninstalled, you
  might want to verify the policy in use for ExternalDNS: if it's `upsert-only`
  no deletion will occur. It must be set to `sync` for deletions to be
  processed. Please add the following to `external-dns-dreamhost-values.yaml` if
  you want this strategy:

  ```yaml
  policy: sync
  ```

## Development

The basic development tasks are provided by make. Run `make help` to see the
available targets.