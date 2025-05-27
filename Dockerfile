# Usar imagen oficial de Python
FROM python:3.11-slim

# Instalar dependencias del sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    # Dependencias básicas de compilación
    build-essential \
    # Dependencias de WeasyPrint
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    libgirepository-1.0-1 \
    gir1.2-pango-1.0 \
    gir1.2-gdkpixbuf-2.0 \
    shared-mime-info \
    # Herramientas adicionales
    pkg-config \
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

# Exponer el puerto (Railway lo sobrescribe con $PORT)
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn comite_pro.wsgi:application --bind 0.0.0.0:${PORT:-8000}