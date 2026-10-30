# Keycloak production image. Render supplies the external HTTPS proxy.
FROM quay.io/keycloak/keycloak:26.4.2

ENV KC_DB=postgres \
    KC_HTTP_ENABLED=true \
    KC_PROXY_HEADERS=xforwarded \
    KC_HEALTH_ENABLED=true \
    KC_METRICS_ENABLED=true

EXPOSE 8080

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--http-port=8080"]
