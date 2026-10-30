# Keycloak production image. Render terminates public HTTPS at its edge.
FROM quay.io/keycloak/keycloak:26.4.2

ENV KC_DB=postgres \
    KC_HTTP_ENABLED=true \
    KC_HTTP_PORT=10000 \
    KC_PROXY_HEADERS=xforwarded \
    KC_HEALTH_ENABLED=true \
    KC_METRICS_ENABLED=true

EXPOSE 10000

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--http-port=10000"]
