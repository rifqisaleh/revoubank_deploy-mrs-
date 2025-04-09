FROM python:3.12-slim

WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv tool and use it for pip
RUN pip install uv

# Copy source code
COPY . .

# Install dependencies
RUN uv pip install -r requirements.txt --system

# Install gunicorn
RUN uv pip install gunicorn --system

# Copy environment variables
COPY .env .env

# Start the app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:app"]
