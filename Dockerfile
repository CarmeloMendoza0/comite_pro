# Usar imagen oficial de Python
FROM python:3.11-slim

# Instalar dependencias del sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libgobject-2.0-0 \
    libgirepository-1.0-1 \
    gir1.2-pango-1.0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorio para archivos estáticos
RUN mkdir -p staticfiles media

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn comite_pro.wsgi:application --bind 0.0.0.0:$PORT