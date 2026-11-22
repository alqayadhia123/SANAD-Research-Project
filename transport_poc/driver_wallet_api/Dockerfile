FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates ./templates
EXPOSE 5001
<<<<<<< HEAD
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
=======

CMD ["gunicorn", 
>>>>>>> 068d918 (Update driver_wallet_api Dockerfile)
