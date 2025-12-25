FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements or project file
COPY pyproject.toml .

# Install dependencies directly from pyproject.toml using pip or generate requirements
# To keep it simple and avoid lockfile issues, we'll use requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 8501
EXPOSE 8502

# Run combined server (Flask webhooks + Streamlit proxy)
CMD ["python", "run_server.py"]
