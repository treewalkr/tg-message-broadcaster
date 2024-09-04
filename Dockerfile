FROM python:3.9-slim-bullseye
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Use build-time secrets to create .env
RUN --mount=type=secret,id=env_file \
    cat /run/secrets/env_file > .env

# Set version as an environment variable
# This will be overwritten at build time
ENV BOT_VERSION=development

# Declare volumes
VOLUME ["/app/bot_groups.json", "/app/sessions"]

CMD ["python", "main.py"]