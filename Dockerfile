FROM python:3.12-slim

# Calibre und benötigte Grafik-Abhängigkeiten für Headless-Betrieb installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    calibre \
    libegl1 \
    libopengl0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080
ENV PORT=8080

# Da E-Book-Konvertierungen etwas CPU-Zeit brauchen, setzen wir das Timeout höher
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "180", "app:app"]
