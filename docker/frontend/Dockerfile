FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY app/ . 
RUN pip install -r requirements.txt  # Installs the dependencies

EXPOSE 5000
# Run the application
CMD ["python", "app.py"]  
