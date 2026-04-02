FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for OpenCV and Tesseract
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Render sets PORT internally, but usually defaults to 10000 or similar if we bind to it, 
# wait, actually render passes $PORT, uvicorn needs to bind to $PORT. So we can use a script or just let render override port)
# Let's bind uvicorn to host 0.0.0.0 and port $PORT. In shell form:
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
