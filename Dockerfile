FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8080

# Usar timeout de 120 segundos para evitar que Gunicorn mate al worker durante peticiones de red a Firestore
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 1 app:app