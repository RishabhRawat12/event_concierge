# Use official Python lightweight image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port for communication
EXPOSE 8000

# Run as a non-root user for security compliance
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]