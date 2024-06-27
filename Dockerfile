# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia los archivos requeridos al contenedor Docker
COPY requirements.txt requirements.txt

# Instala las dependencias necesarias
RUN apt-get update && \
    apt-get install -y gcc libffi-dev portaudio19-dev ffmpeg && \
    apt-get clean

RUN pip install --upgrade pip
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Instala el modelo de Spacy
RUN python -m spacy download es_core_news_md

# Copia el resto del código
COPY . .

# Establece las variables de entorno para el contenedor
ENV PORT=8080
# Expone los puertos en los que correrán las aplicaciones
EXPOSE 8080
EXPOSE 8000

# Comando para ejecutar tu aplicación
CMD ["python", "main1.py"]
