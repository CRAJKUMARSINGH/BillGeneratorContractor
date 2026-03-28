# Use Ubuntu as base image for better system dependency support
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libgtk2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    libxtst6 \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    libcairo2-dev \
    libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb
RUN apt-get update && apt-get install -y ./wkhtmltox_0.12.6-1.focal_amd64.deb

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements_basic.txt ./

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Install Playwright browsers
RUN playwright install-deps
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Create non-root user
RUN useradd -m -u 1000 user
USER user
WORKDIR /app

# Run the application
ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8503", "--server.address=0.0.0.0"]