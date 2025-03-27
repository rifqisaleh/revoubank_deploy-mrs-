FROM python:3.12-slim

# Install curl and ca-certificates
RUN apt-get update && apt-get install -y curl ca-certificates && apt-get clean

# Install uv and add to PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s $HOME/.local/bin/uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv pip install -r requirements.txt --python=/usr/local/bin/python3

# Environment variables
ENV FLASK_APP=app/main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port
EXPOSE 5000

# Run the Flask app
CMD ["flask", "run"]
