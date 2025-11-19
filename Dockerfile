FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Keep Python output unbuffered (useful for logs)
ENV PYTHONUNBUFFERED=1

# Copy and install dependencies first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Don't include secrets in the image. Provide GEMINI_API_KEY at runtime.
EXPOSE 1810

# Default command
CMD ["python", "main.py"]
