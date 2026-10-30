FROM quay.io/keycloak/keycloak:26.4.2

# Render terminates public TLS. Keycloak serves plain HTTP on Render's
# default web-service port; traffic reaches this port through Render's proxy.
ENV KC_HTTP_ENABLED=true
ENV KC_HTTP_PORT=10000
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=true
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

EXPOSE 10000

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--http-port=10000"]
