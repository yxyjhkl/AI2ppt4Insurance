# Dockerfile for web deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for python-pptx and cairosvg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY aippt_config.example.json .

WORKDIR /app/backend
EXPOSE 8099

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8099"]
