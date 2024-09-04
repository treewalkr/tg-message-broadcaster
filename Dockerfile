# Build stage
FROM python:3.9-slim-bullseye AS builder

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Use build-time secrets to create .env
RUN --mount=type=secret,id=env_file \
    cat /run/secrets/env_file > .env

# Runtime stage
FROM python:3.9-slim-bullseye

WORKDIR /app

# Copy only necessary files from builder stage
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Set version as an environment variable using build arg
ARG BOT_VERSION=development
ENV BOT_VERSION=${BOT_VERSION}

# Declare volumes
VOLUME ["/app/bot_groups.json", "/app/sessions"]

CMD ["python", "main.py"]