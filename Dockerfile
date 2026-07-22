FROM python:3.11-slim

WORKDIR /app

# Set pip timeout and retries to handle unstable connections
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
