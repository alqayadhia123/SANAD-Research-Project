FROM quay.io/keycloak/keycloak:26.4.2

# Render terminates public TLS and forwards HTTP to the web-service port.
# Bind explicitly to all interfaces so Render's port scanner can reach Keycloak.
ENV KC_HTTP_ENABLED=true
ENV KC_HTTP_PORT=10000
ENV KC_HTTP_HOST=0.0.0.0
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=true
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

EXPOSE 10000

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--http-port=10000", "--http-host=0.0.0.0"]
