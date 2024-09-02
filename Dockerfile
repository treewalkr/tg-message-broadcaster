# Use multi-stage build for added security
FROM python:3.9-slim-bullseye AS builder

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use build-time secrets to create .env
RUN --mount=type=secret,id=env_file \
    cat /run/secrets/env_file > .env

# Final stage
FROM python:3.9-slim-bullseye
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the rest of your application
COPY . .

# Copy .env from builder stage
COPY --from=builder .env .

# Declare volumes
VOLUME ["/app/bot_groups.json", "/app/sessions"]

CMD ["python", "main.py"]