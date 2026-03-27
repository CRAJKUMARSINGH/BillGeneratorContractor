FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for weasyprint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
COPY engine/requirements.txt /app/engine/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt arq redis

COPY backend /app/backend
COPY engine /app/engine

WORKDIR /app/backend

# Boot up the ARQ worker to process the tasks using the exported WorkerSettings class
CMD ["arq", "worker.WorkerSettings"]
