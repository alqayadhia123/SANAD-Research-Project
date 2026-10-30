FROM quay.io/keycloak/keycloak:26.4.2

# Render terminates public TLS and forwards HTTP to the web-service port.
# Keycloak must bind the Render web-service port on every container interface.
ENV KC_HTTP_ENABLED=true
ENV KC_HTTP_PORT=10000
ENV KC_HTTP_HOST=0.0.0.0
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=true
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

EXPOSE 10000

# Use one explicit startup command; do not split start arguments between
# ENTRYPOINT and CMD, so the runtime port/bind address cannot be omitted.
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start", "--http-port=10000", "--http-host=0.0.0.0"]
