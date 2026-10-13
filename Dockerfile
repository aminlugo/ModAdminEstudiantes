# Usar una imagen oficial y ligera de Python
FROM python:3.12-slim

# Evitar que Python escriba archivos .pyc y almacene en búfer los logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias si alguna librería lo requiere
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copiar e instalar los requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente del proyecto a la imagen
COPY . /app

# Render asigna dinámicamente un puerto mediante la variable de entorno PORT, 
# por lo que usamos un script o comando que escuche en $PORT (por defecto 8080 si no está definida)
CMD gunicorn --bind 0.0.0.0:$PORT app:app