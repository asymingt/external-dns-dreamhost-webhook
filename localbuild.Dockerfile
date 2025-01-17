FROM gcr.io/distroless/static-debian11:nonroot
USER 20000:20000
ADD --chmod=555 build/bin/external-dns-dreamhost-webhook /opt/external-dns-dreamhost-webhook/app

ENTRYPOINT ["/opt/external-dns-dreamhost-webhook/app"]