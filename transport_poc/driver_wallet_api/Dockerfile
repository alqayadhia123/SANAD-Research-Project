FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app

COPY app.py .
COPY templates ./templates
USER app

EXPOSE 5001
CMD ["gunicorn", "--workers=2", "--threads=4", "--timeout=30", "--bind=0.0.0.0:5001", "app:app"]
