FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY transport_poc/driver_wallet_api/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install --requirement /app/requirements.txt
COPY transport_poc /app/transport_poc
EXPOSE 5001
CMD ["gunicorn", "--workers", "2", "--timeout", "30", "--bind", "0.0.0.0:5001", "transport_poc.driver_wallet_api.app:app"]
