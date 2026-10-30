FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements.txt
COPY app.py ./
COPY templates ./templates
EXPOSE 5001
# Render supplies PORT; local Compose defaults to 5001.
CMD ["sh", "-c", "exec gunicorn --workers 2 --timeout 30 --bind 0.0.0.0:${PORT:-5001} app:app"]
