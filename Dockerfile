FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY translate_and_qr_codes/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY translate_and_qr_codes/ .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "translate_and_qr_codes.wsgi:application", "--bind", "0.0.0.0:8000"]
