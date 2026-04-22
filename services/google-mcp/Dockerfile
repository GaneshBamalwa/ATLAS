FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Ensure downloads directory exists
RUN mkdir -p downloads

# Set environment variables
ENV PORT=8000
EXPOSE ${PORT}

# Run the FastAPI application using uvicorn
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
